# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit Tests for Get Customer Operation
# Tests retrieval of customer records by ID

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.customers.lambda_function import (
    get_customer,
    lambda_handler,
    NotFoundError
)


@patch('src.customers.lambda_function.dynamodb_resource')
def test_get_customer_success(mock_dynamodb):
    """Test successful customer retrieval returns customer record."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    customer_data = {
        'customer_id': 'test-123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '+1234567890',
        'address': '123 Main St',
        'company': 'Acme Corp',
        'notes': 'VIP customer',
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T10:00:00Z'
    }
    
    mock_table.get_item.return_value = {
        'Item': customer_data
    }
    
    # Execute
    result = get_customer('test-123')
    
    # Verify
    assert result == customer_data
    mock_table.get_item.assert_called_once_with(
        Key={'customer_id': 'test-123'}
    )


@patch('src.customers.lambda_function.dynamodb_resource')
def test_get_customer_not_found(mock_dynamodb):
    """Test get_customer with non-existent ID returns HTTP 404."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # DynamoDB returns empty response when item not found
    mock_table.get_item.return_value = {}
    
    # Execute and verify exception
    try:
        get_customer('non-existent-id')
        assert False, "Expected NotFoundError"
    except NotFoundError as e:
        assert e.message == "Customer not found"
        assert e.status_code == 404


@patch('src.customers.lambda_function.dynamodb_resource')
def test_get_customer_with_minimal_fields(mock_dynamodb):
    """Test get_customer returns customer with only required fields."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    customer_data = {
        'customer_id': 'test-456',
        'name': 'Jane Smith',
        'email': 'jane@example.com',
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T10:00:00Z'
    }
    
    mock_table.get_item.return_value = {
        'Item': customer_data
    }
    
    # Execute
    result = get_customer('test-456')
    
    # Verify
    assert result['customer_id'] == 'test-456'
    assert result['name'] == 'Jane Smith'
    assert result['email'] == 'jane@example.com'


@patch('src.customers.lambda_function.dynamodb_resource')
def test_get_customer_database_error(mock_dynamodb):
    """Test get_customer handles database errors gracefully."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # Simulate database error
    mock_table.get_item.side_effect = Exception("DynamoDB connection failed")
    
    # Execute and verify exception
    try:
        get_customer('test-789')
        assert False, "Expected DatabaseError"
    except Exception as e:
        assert "Database operation failed" in str(e)


@patch('src.customers.lambda_function.dynamodb_resource')
def test_lambda_handler_get_customer_success(mock_dynamodb):
    """Test lambda_handler routes GET /customers/{customer_id} correctly."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    customer_data = {
        'customer_id': 'test-123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T10:00:00Z'
    }
    
    mock_table.get_item.return_value = {
        'Item': customer_data
    }
    
    # Create API Gateway event
    event = {
        'httpMethod': 'GET',
        'path': '/customers/test-123',
        'pathParameters': {
            'customer_id': 'test-123'
        },
        'requestContext': {
            'authorizer': {
                'sub': 'user-id'
            }
        }
    }
    
    # Execute
    response = lambda_handler(event, None)
    
    # Verify
    assert response['statusCode'] == 200
    assert response['headers']['Content-Type'] == 'application/json'
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    body = json.loads(response['body'])
    assert body['customer_id'] == 'test-123'
    assert body['name'] == 'John Doe'
    assert body['email'] == 'john@example.com'


@patch('src.customers.lambda_function.dynamodb_resource')
def test_lambda_handler_get_customer_not_found(mock_dynamodb):
    """Test lambda_handler returns 404 for non-existent customer."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    # DynamoDB returns empty response
    mock_table.get_item.return_value = {}
    
    # Create API Gateway event
    event = {
        'httpMethod': 'GET',
        'path': '/customers/non-existent',
        'pathParameters': {
            'customer_id': 'non-existent'
        },
        'requestContext': {
            'authorizer': {
                'sub': 'user-id'
            }
        }
    }
    
    # Execute
    response = lambda_handler(event, None)
    
    # Verify
    assert response['statusCode'] == 404
    assert response['headers']['Content-Type'] == 'application/json'
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
    
    body = json.loads(response['body'])
    assert body['error'] == 'NotFoundError'
    assert body['message'] == 'Customer not found'
    assert 'timestamp' in body


@patch('src.customers.lambda_function.dynamodb_resource')
def test_lambda_handler_includes_cors_headers(mock_dynamodb):
    """Test that all responses include CORS headers."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    customer_data = {
        'customer_id': 'test-123',
        'name': 'John Doe',
        'email': 'john@example.com',
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T10:00:00Z'
    }
    
    mock_table.get_item.return_value = {
        'Item': customer_data
    }
    
    # Create API Gateway event
    event = {
        'httpMethod': 'GET',
        'path': '/customers/test-123',
        'pathParameters': {
            'customer_id': 'test-123'
        }
    }
    
    # Execute
    response = lambda_handler(event, None)
    
    # Verify CORS headers
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['headers']['Access-Control-Allow-Origin'] == '*'


@patch('src.customers.lambda_function.dynamodb_resource')
def test_get_customer_returns_all_fields(mock_dynamodb):
    """Test that get_customer returns all customer fields."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb.Table.return_value = mock_table
    
    customer_data = {
        'customer_id': 'test-999',
        'name': 'Complete Customer',
        'email': 'complete@example.com',
        'phone': '+9999999999',
        'address': '999 Complete Ave',
        'company': 'Complete Inc',
        'notes': 'All fields populated',
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T12:00:00Z'
    }
    
    mock_table.get_item.return_value = {
        'Item': customer_data
    }
    
    # Execute
    result = get_customer('test-999')
    
    # Verify all fields are present
    assert result['customer_id'] == 'test-999'
    assert result['name'] == 'Complete Customer'
    assert result['email'] == 'complete@example.com'
    assert result['phone'] == '+9999999999'
    assert result['address'] == '999 Complete Ave'
    assert result['company'] == 'Complete Inc'
    assert result['notes'] == 'All fields populated'
    assert result['created_at'] == '2024-01-15T10:00:00Z'
    assert result['updated_at'] == '2024-01-15T12:00:00Z'
