# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit tests for error handling and response formatting

import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.customers.lambda_function import (
    CustomerManagementError,
    ValidationError,
    NotFoundError,
    DatabaseError,
    ConflictError,
    handle_error,
    lambda_handler
)


class TestExceptionClasses:
    """Test custom exception classes."""
    
    def test_customer_management_error_base_class(self):
        """Test CustomerManagementError base exception class."""
        error = CustomerManagementError("Test error", 500)
        
        assert error.message == "Test error"
        assert error.status_code == 500
        assert str(error) == "Test error"
    
    def test_validation_error_http_400(self):
        """Test ValidationError exception returns HTTP 400."""
        error = ValidationError("Invalid input")
        
        assert error.message == "Invalid input"
        assert error.status_code == 400
        assert isinstance(error, CustomerManagementError)
    
    def test_not_found_error_http_404(self):
        """Test NotFoundError exception returns HTTP 404."""
        error = NotFoundError("Resource not found")
        
        assert error.message == "Resource not found"
        assert error.status_code == 404
        assert isinstance(error, CustomerManagementError)
    
    def test_database_error_http_500(self):
        """Test DatabaseError exception returns HTTP 500."""
        error = DatabaseError("Database operation failed")
        
        assert error.message == "Database operation failed"
        assert error.status_code == 500
        assert isinstance(error, CustomerManagementError)
    
    def test_conflict_error_http_409(self):
        """Test ConflictError exception returns HTTP 409."""
        error = ConflictError("Resource conflict")
        
        assert error.message == "Resource conflict"
        assert error.status_code == 409
        assert isinstance(error, CustomerManagementError)


class TestHandleErrorFunction:
    """Test handle_error function for converting exceptions to API Gateway responses."""
    
    def test_handle_validation_error(self):
        """Test handle_error converts ValidationError to HTTP 400 response."""
        error = ValidationError("Invalid email format")
        
        response = handle_error(error)
        
        assert response['statusCode'] == 400
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
        assert body['message'] == 'Invalid email format'
        assert 'timestamp' in body
        # Verify timestamp is in ISO 8601 format
        datetime.fromisoformat(body['timestamp'].replace('Z', '+00:00'))
    
    def test_handle_not_found_error(self):
        """Test handle_error converts NotFoundError to HTTP 404 response."""
        error = NotFoundError("Customer not found")
        
        response = handle_error(error)
        
        assert response['statusCode'] == 404
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['error'] == 'NotFoundError'
        assert body['message'] == 'Customer not found'
        assert 'timestamp' in body
    
    def test_handle_database_error(self):
        """Test handle_error converts DatabaseError to HTTP 500 response."""
        error = DatabaseError("Database operation failed: Connection timeout")
        
        response = handle_error(error)
        
        assert response['statusCode'] == 500
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['error'] == 'DatabaseError'
        assert body['message'] == 'Database operation failed: Connection timeout'
        assert 'timestamp' in body
    
    def test_handle_conflict_error(self):
        """Test handle_error converts ConflictError to HTTP 409 response."""
        error = ConflictError("Customer email must be unique")
        
        response = handle_error(error)
        
        assert response['statusCode'] == 409
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['error'] == 'ConflictError'
        assert body['message'] == 'Customer email must be unique'
        assert 'timestamp' in body
    
    def test_handle_generic_exception(self):
        """Test handle_error converts generic Exception to HTTP 500 response."""
        error = Exception("Unexpected error occurred")
        
        response = handle_error(error)
        
        assert response['statusCode'] == 500
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['error'] == 'InternalServerError'
        assert body['message'] == 'Internal server error'
        assert 'timestamp' in body
    
    def test_error_response_format_has_required_fields(self):
        """Test error response contains error, message, and timestamp fields."""
        error = ValidationError("Test error")
        
        response = handle_error(error)
        body = json.loads(response['body'])
        
        # Verify all required fields are present
        assert 'error' in body
        assert 'message' in body
        assert 'timestamp' in body
        
        # Verify field types
        assert isinstance(body['error'], str)
        assert isinstance(body['message'], str)
        assert isinstance(body['timestamp'], str)
    
    def test_error_response_includes_cors_headers(self):
        """Test all error responses include CORS headers."""
        errors = [
            ValidationError("Validation failed"),
            NotFoundError("Not found"),
            DatabaseError("Database error"),
            ConflictError("Conflict"),
            Exception("Generic error")
        ]
        
        for error in errors:
            response = handle_error(error)
            
            assert 'Access-Control-Allow-Origin' in response['headers']
            assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    def test_error_response_timestamp_format(self):
        """Test error response timestamp is in ISO 8601 format with Z suffix."""
        error = ValidationError("Test error")
        
        response = handle_error(error)
        body = json.loads(response['body'])
        
        # Verify timestamp ends with 'Z' (UTC indicator)
        assert body['timestamp'].endswith('Z')
        
        # Verify timestamp can be parsed as ISO 8601
        timestamp = datetime.fromisoformat(body['timestamp'].replace('Z', '+00:00'))
        assert isinstance(timestamp, datetime)


class TestMalformedJSONHandling:
    """Test malformed JSON handling in lambda_handler."""
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.validation.dynamodb')
    def test_malformed_json_in_post_request(self, mock_validation_db, mock_dynamodb):
        """Test malformed JSON in POST request returns HTTP 400."""
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'body': '{invalid json}',
            'pathParameters': None
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
        assert 'Invalid JSON format' in body['message']
        assert 'timestamp' in body
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.validation.dynamodb')
    def test_malformed_json_in_put_request(self, mock_validation_db, mock_dynamodb_client, mock_dynamodb_resource):
        """Test malformed JSON in PUT request returns HTTP 400."""
        event = {
            'httpMethod': 'PUT',
            'path': '/customers/test-id',
            'pathParameters': {'customer_id': 'test-id'},
            'body': 'not valid json at all'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
        assert 'Invalid JSON format' in body['message']
        assert 'timestamp' in body
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.validation.dynamodb')
    def test_empty_body_in_post_request(self, mock_validation_db, mock_dynamodb):
        """Test empty body in POST request is handled gracefully."""
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'body': '',
            'pathParameters': None
        }
        
        response = lambda_handler(event, None)
        
        # Should fail validation for missing required fields
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.validation.dynamodb')
    def test_missing_body_in_post_request(self, mock_validation_db, mock_dynamodb):
        """Test missing body in POST request is handled gracefully."""
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'pathParameters': None
        }
        
        response = lambda_handler(event, None)
        
        # Should fail validation for missing required fields
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'


class TestCORSHeaders:
    """Test CORS headers are included in all responses."""
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    def test_cors_headers_in_successful_get_response(self, mock_dynamodb_resource):
        """Test CORS headers are included in successful GET response."""
        # Mock DynamoDB response
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        mock_dynamodb_resource.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/customers/test-123',
            'pathParameters': {'customer_id': 'test-123'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    def test_cors_headers_in_error_response(self, mock_dynamodb_resource):
        """Test CORS headers are included in error responses."""
        # Mock DynamoDB to return no item (404)
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_dynamodb_resource.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/customers/non-existent',
            'pathParameters': {'customer_id': 'non-existent'}
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    def test_cors_headers_in_list_response(self, mock_dynamodb_resource):
        """Test CORS headers are included in list response."""
        # Mock DynamoDB scan response
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            'Items': [
                {
                    'customer_id': 'test-1',
                    'name': 'Customer 1',
                    'email': 'customer1@example.com',
                    'created_at': '2024-01-15T10:00:00Z',
                    'updated_at': '2024-01-15T10:00:00Z'
                }
            ]
        }
        mock_dynamodb_resource.Table.return_value = mock_table
        
        event = {
            'httpMethod': 'GET',
            'path': '/customers',
            'pathParameters': None
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestErrorResponseConsistency:
    """Test error responses are consistent across different error types."""
    
    def test_all_error_types_have_same_structure(self):
        """Test all error types return responses with the same structure."""
        errors = [
            ValidationError("Validation error"),
            NotFoundError("Not found error"),
            DatabaseError("Database error"),
            ConflictError("Conflict error")
        ]
        
        for error in errors:
            response = handle_error(error)
            body = json.loads(response['body'])
            
            # All should have exactly these three fields
            assert set(body.keys()) == {'error', 'message', 'timestamp'}
            
            # All should have proper headers
            assert 'Content-Type' in response['headers']
            assert 'Access-Control-Allow-Origin' in response['headers']
    
    def test_error_type_matches_exception_class_name(self):
        """Test error field matches the exception class name."""
        test_cases = [
            (ValidationError("test"), "ValidationError"),
            (NotFoundError("test"), "NotFoundError"),
            (DatabaseError("test"), "DatabaseError"),
            (ConflictError("test"), "ConflictError")
        ]
        
        for error, expected_error_type in test_cases:
            response = handle_error(error)
            body = json.loads(response['body'])
            
            assert body['error'] == expected_error_type
    
    def test_error_message_preserved_in_response(self):
        """Test error message is preserved exactly in the response."""
        test_messages = [
            "Invalid email format",
            "Customer not found",
            "Database operation failed: Connection timeout",
            "Customer email must be unique"
        ]
        
        for message in test_messages:
            error = ValidationError(message)
            response = handle_error(error)
            body = json.loads(response['body'])
            
            assert body['message'] == message
