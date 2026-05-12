# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit Tests for update_customer function
# Tests customer update with validation and error handling

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.customers.lambda_function import (
    update_customer,
    ValidationError,
    ConflictError,
    NotFoundError,
    DatabaseError,
    lambda_handler
)


class TestUpdateCustomer:
    """Unit tests for update_customer function."""
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.validation.dynamodb')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_update_customer_partial_update_name(self, mock_timestamp, mock_validation_db, mock_dynamodb_resource, mock_dynamodb_client):
        """Test successful partial update of customer name."""
        # Setup mocks
        mock_timestamp.return_value = '2024-01-15T12:00:00Z'
        
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+1234567890',
                'address': '123 Main St',
                'company': 'Acme Corp',
                'notes': 'VIP customer',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        # Mock update_item response
        mock_dynamodb_client.update_item.return_value = {
            'Attributes': {
                'customer_id': {'S': 'test-uuid-123'},
                'name': {'S': 'Jane Doe'},
                'email': {'S': 'john@example.com'},
                'phone': {'S': '+1234567890'},
                'address': {'S': '123 Main St'},
                'company': {'S': 'Acme Corp'},
                'notes': {'S': 'VIP customer'},
                'created_at': {'S': '2024-01-15T10:00:00Z'},
                'updated_at': {'S': '2024-01-15T12:00:00Z'}
            }
        }
        
        # Update data (only name)
        update_data = {
            'name': 'Jane Doe'
        }
        
        # Call update_customer
        result = update_customer('test-uuid-123', update_data)
        
        # Verify result
        assert result['customer_id'] == 'test-uuid-123'
        assert result['name'] == 'Jane Doe'
        assert result['email'] == 'john@example.com'
        assert result['phone'] == '+1234567890'
        assert result['address'] == '123 Main St'
        assert result['company'] == 'Acme Corp'
        assert result['notes'] == 'VIP customer'
        assert result['created_at'] == '2024-01-15T10:00:00Z'
        assert result['updated_at'] == '2024-01-15T12:00:00Z'
        
        # Verify DynamoDB update_item was called
        mock_dynamodb_client.update_item.assert_called_once()
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.validation.dynamodb')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_update_customer_multiple_fields(self, mock_timestamp, mock_validation_db, mock_dynamodb_resource, mock_dynamodb_client):
        """Test successful update of multiple customer fields."""
        # Setup mocks
        mock_timestamp.return_value = '2024-01-15T13:00:00Z'
        
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-456',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+1234567890',
                'address': '123 Main St',
                'company': 'Acme Corp',
                'notes': 'VIP customer',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        # Mock update_item response
        mock_dynamodb_client.update_item.return_value = {
            'Attributes': {
                'customer_id': {'S': 'test-uuid-456'},
                'name': {'S': 'Jane Smith'},
                'email': {'S': 'john@example.com'},
                'phone': {'S': '+9876543210'},
                'address': {'S': '456 Oak Ave'},
                'company': {'S': 'Acme Corp'},
                'notes': {'S': 'VIP customer'},
                'created_at': {'S': '2024-01-15T10:00:00Z'},
                'updated_at': {'S': '2024-01-15T13:00:00Z'}
            }
        }
        
        # Update data (multiple fields)
        update_data = {
            'name': 'Jane Smith',
            'phone': '+9876543210',
            'address': '456 Oak Ave'
        }
        
        # Call update_customer
        result = update_customer('test-uuid-456', update_data)
        
        # Verify result
        assert result['customer_id'] == 'test-uuid-456'
        assert result['name'] == 'Jane Smith'
        assert result['phone'] == '+9876543210'
        assert result['address'] == '456 Oak Ave'
        assert result['created_at'] == '2024-01-15T10:00:00Z'
        assert result['updated_at'] == '2024-01-15T13:00:00Z'
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.validation.dynamodb')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_update_customer_email_with_validation(self, mock_timestamp, mock_validation_db, mock_dynamodb_resource, mock_dynamodb_client):
        """Test successful update of customer email with validation."""
        # Setup mocks
        mock_timestamp.return_value = '2024-01-15T14:00:00Z'
        
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-789',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        # Mock email uniqueness check (email is unique)
        mock_validation_db.query.return_value = {'Items': []}
        
        # Mock update_item response
        mock_dynamodb_client.update_item.return_value = {
            'Attributes': {
                'customer_id': {'S': 'test-uuid-789'},
                'name': {'S': 'John Doe'},
                'email': {'S': 'newemail@example.com'},
                'phone': {'NULL': True},
                'address': {'NULL': True},
                'company': {'NULL': True},
                'notes': {'NULL': True},
                'created_at': {'S': '2024-01-15T10:00:00Z'},
                'updated_at': {'S': '2024-01-15T14:00:00Z'}
            }
        }
        
        # Update data (email)
        update_data = {
            'email': 'newemail@example.com'
        }
        
        # Call update_customer
        result = update_customer('test-uuid-789', update_data)
        
        # Verify result
        assert result['customer_id'] == 'test-uuid-789'
        assert result['email'] == 'newemail@example.com'
        assert result['created_at'] == '2024-01-15T10:00:00Z'
        assert result['updated_at'] == '2024-01-15T14:00:00Z'
        
        # Verify email uniqueness was checked with exclusion
        mock_validation_db.query.assert_called_once()
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    def test_update_customer_not_found(self, mock_dynamodb_resource):
        """Test that updating non-existent customer raises NotFoundError."""
        # Mock get_customer (customer not found)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {}  # No Item in response
        
        update_data = {
            'name': 'Jane Doe'
        }
        
        with pytest.raises(NotFoundError) as exc_info:
            update_customer('non-existent-id', update_data)
        
        assert "Customer not found" in str(exc_info.value.message)
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.validation.dynamodb')
    def test_update_customer_invalid_email_format(self, mock_validation_db, mock_dynamodb_resource):
        """Test that invalid email format raises ValidationError."""
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        update_data = {
            'email': 'invalid-email'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            update_customer('test-uuid-123', update_data)
        
        assert "Invalid email format" in str(exc_info.value.message)
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.validation.dynamodb')
    def test_update_customer_duplicate_email(self, mock_validation_db, mock_dynamodb_resource):
        """Test that duplicate email raises ConflictError."""
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        # Mock email already exists for different customer
        mock_validation_db.query.return_value = {
            'Items': [{'customer_id': {'S': 'different-customer-id'}}]
        }
        
        update_data = {
            'email': 'existing@example.com'
        }
        
        with pytest.raises(ConflictError) as exc_info:
            update_customer('test-uuid-123', update_data)
        
        assert "Customer email must be unique" in str(exc_info.value.message)
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_update_customer_preserves_created_at(self, mock_timestamp, mock_dynamodb_resource, mock_dynamodb_client):
        """Test that update preserves the original created_at timestamp."""
        # Setup mocks
        original_created_at = '2024-01-10T08:00:00Z'
        mock_timestamp.return_value = '2024-01-15T15:00:00Z'
        
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-999',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': original_created_at,
                'updated_at': '2024-01-10T08:00:00Z'
            }
        }
        
        # Mock update_item response
        mock_dynamodb_client.update_item.return_value = {
            'Attributes': {
                'customer_id': {'S': 'test-uuid-999'},
                'name': {'S': 'Updated Name'},
                'email': {'S': 'john@example.com'},
                'phone': {'NULL': True},
                'address': {'NULL': True},
                'company': {'NULL': True},
                'notes': {'NULL': True},
                'created_at': {'S': original_created_at},
                'updated_at': {'S': '2024-01-15T15:00:00Z'}
            }
        }
        
        # Update data
        update_data = {
            'name': 'Updated Name'
        }
        
        # Call update_customer
        result = update_customer('test-uuid-999', update_data)
        
        # Verify created_at is preserved and updated_at is changed
        assert result['created_at'] == original_created_at
        assert result['updated_at'] == '2024-01-15T15:00:00Z'
        assert result['created_at'] != result['updated_at']
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_update_customer_database_error(self, mock_timestamp, mock_dynamodb_resource, mock_dynamodb_client):
        """Test that database errors raise DatabaseError."""
        # Setup mocks
        mock_timestamp.return_value = '2024-01-15T16:00:00Z'
        
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-error',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        # Mock update_item to raise exception
        mock_dynamodb_client.update_item.side_effect = Exception("DynamoDB connection failed")
        
        update_data = {
            'name': 'Updated Name'
        }
        
        with pytest.raises(DatabaseError) as exc_info:
            update_customer('test-uuid-error', update_data)
        
        assert "Database operation failed" in str(exc_info.value.message)


class TestLambdaHandlerUpdateCustomer:
    """Unit tests for lambda_handler with PUT /customers/{customer_id}."""
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.lambda_function.get_utc_timestamp')
    def test_lambda_handler_update_customer_success(self, mock_timestamp, mock_dynamodb_resource, mock_dynamodb_client):
        """Test lambda_handler successfully updates customer and returns HTTP 200."""
        # Setup mocks
        mock_timestamp.return_value = '2024-01-15T17:00:00Z'
        
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+1234567890',
                'address': '123 Main St',
                'company': 'Acme Corp',
                'notes': 'VIP customer',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        # Mock update_item response
        mock_dynamodb_client.update_item.return_value = {
            'Attributes': {
                'customer_id': {'S': 'test-uuid-123'},
                'name': {'S': 'Jane Doe'},
                'email': {'S': 'john@example.com'},
                'phone': {'S': '+1234567890'},
                'address': {'S': '123 Main St'},
                'company': {'S': 'Acme Corp'},
                'notes': {'S': 'Updated notes'},
                'created_at': {'S': '2024-01-15T10:00:00Z'},
                'updated_at': {'S': '2024-01-15T17:00:00Z'}
            }
        }
        
        # API Gateway event
        event = {
            'httpMethod': 'PUT',
            'path': '/customers/test-uuid-123',
            'pathParameters': {
                'customer_id': 'test-uuid-123'
            },
            'body': json.dumps({
                'name': 'Jane Doe',
                'notes': 'Updated notes'
            })
        }
        
        # Call lambda_handler
        response = lambda_handler(event, None)
        
        # Verify response
        assert response['statusCode'] == 200
        assert response['headers']['Content-Type'] == 'application/json'
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        
        body = json.loads(response['body'])
        assert body['customer_id'] == 'test-uuid-123'
        assert body['name'] == 'Jane Doe'
        assert body['notes'] == 'Updated notes'
        assert body['created_at'] == '2024-01-15T10:00:00Z'
        assert body['updated_at'] == '2024-01-15T17:00:00Z'
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    def test_lambda_handler_update_customer_not_found(self, mock_dynamodb_resource):
        """Test lambda_handler returns HTTP 404 for non-existent customer."""
        # Mock get_customer (customer not found)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {}  # No Item in response
        
        event = {
            'httpMethod': 'PUT',
            'path': '/customers/non-existent-id',
            'pathParameters': {
                'customer_id': 'non-existent-id'
            },
            'body': json.dumps({
                'name': 'Jane Doe'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 404
        body = json.loads(response['body'])
        assert body['error'] == 'NotFoundError'
        assert 'Customer not found' in body['message']
    
    def test_lambda_handler_update_customer_invalid_json(self):
        """Test lambda_handler returns HTTP 400 for invalid JSON."""
        event = {
            'httpMethod': 'PUT',
            'path': '/customers/test-uuid-123',
            'pathParameters': {
                'customer_id': 'test-uuid-123'
            },
            'body': 'invalid json'
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
        assert 'Invalid JSON format' in body['message']
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.validation.dynamodb')
    def test_lambda_handler_update_customer_invalid_email(self, mock_validation_db, mock_dynamodb_resource):
        """Test lambda_handler returns HTTP 400 for invalid email format."""
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        event = {
            'httpMethod': 'PUT',
            'path': '/customers/test-uuid-123',
            'pathParameters': {
                'customer_id': 'test-uuid-123'
            },
            'body': json.dumps({
                'email': 'invalid-email'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['error'] == 'ValidationError'
        assert 'Invalid email format' in body['message']
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.validation.dynamodb')
    def test_lambda_handler_update_customer_duplicate_email(self, mock_validation_db, mock_dynamodb_resource):
        """Test lambda_handler returns HTTP 409 for duplicate email."""
        # Mock get_customer (existing customer)
        mock_table = MagicMock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-uuid-123',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            }
        }
        
        # Mock email already exists for different customer
        mock_validation_db.query.return_value = {
            'Items': [{'customer_id': {'S': 'different-customer-id'}}]
        }
        
        event = {
            'httpMethod': 'PUT',
            'path': '/customers/test-uuid-123',
            'pathParameters': {
                'customer_id': 'test-uuid-123'
            },
            'body': json.dumps({
                'email': 'existing@example.com'
            })
        }
        
        response = lambda_handler(event, None)
        
        assert response['statusCode'] == 409
        body = json.loads(response['body'])
        assert body['error'] == 'ConflictError'
        assert 'Customer email must be unique' in body['message']
