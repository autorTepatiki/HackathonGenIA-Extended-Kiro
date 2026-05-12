# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit tests for lambda_handler routing and request context handling

import json
import pytest
from unittest.mock import patch, MagicMock

from src.customers.lambda_function import lambda_handler


class TestLambdaHandlerRouting:
    """Unit tests for lambda_handler routing and request context."""
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    def test_lambda_handler_extracts_user_identity(self, mock_dynamodb_resource):
        """Test lambda_handler extracts user identity from requestContext.authorizer."""
        # Setup mock
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-customer-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+1234567890',
                'address': '123 Main St',
                'company': 'ACME Corp',
                'notes': 'VIP customer',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        mock_dynamodb_resource.Table.return_value = mock_table
        
        # Create event with requestContext.authorizer
        event = {
            'httpMethod': 'GET',
            'path': '/customers/test-customer-123',
            'pathParameters': {
                'customer_id': 'test-customer-123'
            },
            'requestContext': {
                'authorizer': {
                    'principalId': 'user-123',
                    'email': 'user@example.com',
                    'username': 'testuser'
                }
            }
        }
        
        # Execute
        with patch('src.customers.lambda_function.logger') as mock_logger:
            response = lambda_handler(event, None)
            
            # Verify logger was called with user_identity
            assert mock_logger.info.called
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            
            # Find the request_received log entry
            request_log = None
            for log_entry in log_calls:
                log_data = json.loads(log_entry)
                if log_data.get('event') == 'request_received':
                    request_log = log_data
                    break
            
            # Verify user_identity was logged
            assert request_log is not None, "request_received log entry not found"
            assert 'user_identity' in request_log
            assert request_log['user_identity'] == 'user-123'
        
        # Verify response is successful
        assert response['statusCode'] == 200
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    def test_lambda_handler_handles_missing_authorizer_context(self, mock_dynamodb_resource):
        """Test lambda_handler handles missing authorizer context gracefully."""
        # Setup mock
        mock_table = MagicMock()
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-customer-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        mock_dynamodb_resource.Table.return_value = mock_table
        
        # Create event without requestContext.authorizer
        event = {
            'httpMethod': 'GET',
            'path': '/customers/test-customer-123',
            'pathParameters': {
                'customer_id': 'test-customer-123'
            }
        }
        
        # Execute
        with patch('src.customers.lambda_function.logger') as mock_logger:
            response = lambda_handler(event, None)
            
            # Verify logger was called with default user_identity
            assert mock_logger.info.called
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            
            # Find the request_received log entry
            request_log = None
            for log_entry in log_calls:
                log_data = json.loads(log_entry)
                if log_data.get('event') == 'request_received':
                    request_log = log_data
                    break
            
            # Verify user_identity defaults to 'unknown'
            assert request_log is not None
            assert 'user_identity' in request_log
            assert request_log['user_identity'] == 'unknown'
        
        # Verify response is successful
        assert response['statusCode'] == 200
    
    def test_lambda_handler_routes_post_customers(self):
        """Test lambda_handler correctly routes POST /customers."""
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'body': json.dumps({
                'name': 'Test User',
                'email': 'test@example.com'
            })
        }
        
        with patch('src.customers.lambda_function.create_customer') as mock_create:
            mock_create.return_value = {
                'customer_id': 'test-123',
                'name': 'Test User',
                'email': 'test@example.com',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
            
            response = lambda_handler(event, None)
            
            assert response['statusCode'] == 201
            assert mock_create.called
    
    @patch('src.customers.lambda_function.list_customers')
    def test_lambda_handler_routes_get_customers_list(self, mock_list):
        """Test lambda_handler correctly routes GET /customers (list all)."""
        mock_list.return_value = [
            {'customer_id': '1', 'name': 'User 1', 'email': 'user1@example.com'},
            {'customer_id': '2', 'name': 'User 2', 'email': 'user2@example.com'}
        ]
        
        event = {
            'httpMethod': 'GET',
            'path': '/customers'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        assert mock_list.called
        body = json.loads(response['body'])
        assert 'customers' in body
        assert len(body['customers']) == 2
    
    @patch('src.customers.lambda_function.get_customer')
    def test_lambda_handler_routes_get_customer_by_id(self, mock_get):
        """Test lambda_handler correctly routes GET /customers/{customer_id}."""
        mock_get.return_value = {
            'customer_id': 'test-123',
            'name': 'Test User',
            'email': 'test@example.com'
        }
        
        event = {
            'httpMethod': 'GET',
            'path': '/customers/test-123',
            'pathParameters': {
                'customer_id': 'test-123'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        assert mock_get.called
        mock_get.assert_called_once_with('test-123', 'unknown')
    
    @patch('src.customers.lambda_function.update_customer')
    def test_lambda_handler_routes_put_customer(self, mock_update):
        """Test lambda_handler correctly routes PUT /customers/{customer_id}."""
        mock_update.return_value = {
            'customer_id': 'test-123',
            'name': 'Updated User',
            'email': 'updated@example.com',
            'updated_at': '2024-01-15T11:00:00Z'
        }
        
        event = {
            'httpMethod': 'PUT',
            'path': '/customers/test-123',
            'pathParameters': {
                'customer_id': 'test-123'
            },
            'body': json.dumps({
                'name': 'Updated User'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        assert mock_update.called
        mock_update.assert_called_once_with('test-123', {'name': 'Updated User'}, 'unknown')
    
    @patch('src.customers.lambda_function.delete_customer')
    def test_lambda_handler_routes_delete_customer(self, mock_delete):
        """Test lambda_handler correctly routes DELETE /customers/{customer_id}."""
        mock_delete.return_value = {
            'message': 'Customer deleted successfully'
        }
        
        event = {
            'httpMethod': 'DELETE',
            'path': '/customers/test-123',
            'pathParameters': {
                'customer_id': 'test-123'
            }
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 200
        assert mock_delete.called
        mock_delete.assert_called_once_with('test-123', 'unknown')
    
    def test_lambda_handler_returns_404_for_unknown_endpoint(self):
        """Test lambda_handler returns 404 for unknown endpoints."""
        event = {
            'httpMethod': 'GET',
            'path': '/unknown'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'NotFound'
        assert 'Endpoint not implemented' in body['message']
    
    def test_lambda_handler_includes_cors_headers_in_all_responses(self):
        """Test lambda_handler includes CORS headers in all responses."""
        event = {
            'httpMethod': 'GET',
            'path': '/unknown'
        }
        
        response = lambda_handler(event, None)
        
        assert 'headers' in response
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'Content-Type' in response['headers']
        assert response['headers']['Content-Type'] == 'application/json'
