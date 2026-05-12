# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit Tests for create_customer function
# Tests customer creation with validation and error handling

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.customers.lambda_function import (
    create_customer,
    ValidationError,
    ConflictError,
    DatabaseError,
    lambda_handler
)


class TestCreateCustomer:
    """Unit tests for create_customer function."""
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.validation.dynamodb')
    @patch('src.customers.lambda_function.generate_customer_id')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_create_customer_with_all_fields(self, mock_timestamp, mock_gen_id, mock_validation_db, mock_dynamodb):
        """Test successful customer creation with all fields."""
        # Setup mocks
        mock_gen_id.return_value = 'test-uuid-123'
        mock_timestamp.return_value = '2024-01-15T10:00:00Z'
        mock_validation_db.query.return_value = {'Items': []}  # Email is unique
        mock_dynamodb.put_item.return_value = {}
        
        # Customer data with all fields
        customer_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '+1234567890',
            'address': '123 Main St',
            'company': 'Acme Corp',
            'notes': 'VIP customer'
        }
        
        # Call create_customer
        result = create_customer(customer_data)
        
        # Verify result
        assert result['customer_id'] == 'test-uuid-123'
        assert result['name'] == 'John Doe'
        assert result['email'] == 'john@example.com'
        assert result['phone'] == '+1234567890'
        assert result['address'] == '123 Main St'
        assert result['company'] == 'Acme Corp'
        assert result['notes'] == 'VIP customer'
        assert result['created_at'] == '2024-01-15T10:00:00Z'
        assert result['updated_at'] == '2024-01-15T10:00:00Z'
        
        # Verify DynamoDB put_item was called
        mock_dynamodb.put_item.assert_called_once()
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.validation.dynamodb')
    @patch('src.customers.lambda_function.generate_customer_id')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_create_customer_with_only_required_fields(self, mock_timestamp, mock_gen_id, mock_validation_db, mock_dynamodb):
        """Test successful customer creation with only required fields."""
        # Setup mocks
        mock_gen_id.return_value = 'test-uuid-456'
        mock_timestamp.return_value = '2024-01-15T11:00:00Z'
        mock_validation_db.query.return_value = {'Items': []}
        mock_dynamodb.put_item.return_value = {}
        
        # Customer data with only required fields
        customer_data = {
            'name': 'Jane Smith',
            'email': 'jane@example.com'
        }
        
        # Call create_customer
        result = create_customer(customer_data)
        
        # Verify result
        assert result['customer_id'] == 'test-uuid-456'
        assert result['name'] == 'Jane Smith'
        assert result['email'] == 'jane@example.com'
        assert result['phone'] is None
        assert result['address'] is None
        assert result['company'] is None
        assert result['notes'] is None
        assert result['created_at'] == '2024-01-15T11:00:00Z'
        assert result['updated_at'] == '2024-01-15T11:00:00Z'
    
    def test_create_customer_missing_name(self):
        """Test that missing name field raises ValidationError."""
        customer_data = {
            'email': 'john@example.com'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_customer(customer_data)
        
        assert "Missing required fields: name" in str(exc_info.value.message)
    
    def test_create_customer_missing_email(self):
        """Test that missing email field raises ValidationError."""
        customer_data = {
            'name': 'John Doe'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_customer(customer_data)
        
        assert "Missing required fields: email" in str(exc_info.value.message)
    
    def test_create_customer_missing_both_required_fields(self):
        """Test that missing both required fields raises ValidationError."""
        customer_data = {
            'phone': '+1234567890'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_customer(customer_data)
        
        assert "Missing required fields:" in str(exc_info.value.message)
    
    @patch('src.customers.validation.dynamodb')
    def test_create_customer_invalid_email_format(self, mock_validation_db):
        """Test that invalid email format raises ValidationError."""
        customer_data = {
            'name': 'John Doe',
            'email': 'invalid-email'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            create_customer(customer_data)
        
        assert "Invalid email format" in str(exc_info.value.message)
    
    @patch('src.customers.validation.dynamodb')
    def test_create_customer_duplicate_email(self, mock_validation_db):
        """Test that duplicate email raises ConflictError."""
        # Mock email already exists
        mock_validation_db.query.return_value = {
            'Items': [{'customer_id': {'S': 'existing-id'}}]
        }
        
        customer_data = {
            'name': 'John Doe',
            'email': 'existing@example.com'
        }
        
        with pytest.raises(ConflictError) as exc_info:
            create_customer(customer_data)
        
        assert "Customer email must be unique" in str(exc_info.value.message)
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.validation.dynamodb')
    @patch('src.customers.lambda_function.generate_customer_id')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_create_customer_database_error(self, mock_timestamp, mock_gen_id, mock_validation_db, mock_dynamodb):
        """Test that database errors raise DatabaseError."""
        # Setup mocks
        mock_gen_id.return_value = 'test-uuid-789'
        mock_timestamp.return_value = '2024-01-15T12:00:00Z'
        mock_validation_db.query.return_value = {'Items': []}
        mock_dynamodb.put_item.side_effect = Exception("DynamoDB connection failed")
        
        customer_data = {
            'name': 'John Doe',
            'email': 'john@example.com'
        }
        
        with pytest.raises(DatabaseError) as exc_info:
            create_customer(customer_data)
        
        assert "Database operation failed" in str(exc_info.value.message)


class TestLambdaHandlerCreateCustomer:
    """Unit tests for lambda_handler with POST /customers."""
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.validation.dynamodb')
    @patch('src.customers.lambda_function.generate_customer_id')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_lambda_handler_create_customer_success(self, mock_timestamp, mock_gen_id, mock_validation_db, mock_dynamodb):
        """Test lambda_handler successfully creates customer and returns HTTP 201."""
        # Setup mocks
        mock_gen_id.return_value = 'test-uuid-123'
        mock_timestamp.return_value = '2024-01-15T10:00:00Z'
        mock_validation_db.query.return_value = {'Items': []}
        mock_dynamodb.put_item.return_value = {}
        
        # API Gateway event
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'body': json.dumps({
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+1234567890'
            })
        }
        
        # Call lambda_handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 201
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['customer_id'] == 'test-uuid-123'
        assert body['name'] == 'John Doe'
        assert body['email'] == 'john@example.com'
        assert body['phone'] == '+1234567890'
    
    def test_lambda_handler_create_customer_invalid_json(self):
        """Test lambda_handler returns HTTP 400 for invalid JSON."""
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'body': 'invalid json'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
        assert 'Invalid JSON format' in body['message']
    
    def test_lambda_handler_create_customer_missing_required_fields(self):
        """Test lambda_handler returns HTTP 400 for missing required fields."""
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'body': json.dumps({
                'name': 'John Doe'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
        assert 'Missing required fields' in body['message']
    
    @patch('src.customers.validation.dynamodb')
    def test_lambda_handler_create_customer_invalid_email(self, mock_validation_db):
        """Test lambda_handler returns HTTP 400 for invalid email format."""
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'body': json.dumps({
                'name': 'John Doe',
                'email': 'invalid-email'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
        assert 'Invalid email format' in body['message']
    
    @patch('src.customers.validation.dynamodb')
    def test_lambda_handler_create_customer_duplicate_email(self, mock_validation_db):
        """Test lambda_handler returns HTTP 409 for duplicate email."""
        # Mock email already exists
        mock_validation_db.query.return_value = {
            'Items': [{'customer_id': {'S': 'existing-id'}}]
        }
        
        event = {
            'httpMethod': 'POST',
            'path': '/customers',
            'body': json.dumps({
                'name': 'John Doe',
                'email': 'existing@example.com'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert body['error'] == 'ConflictError'
        assert 'Customer email must be unique' in body['message']
