# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit Tests for Delete Customer Operation
# Tests deletion of customer records by ID

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from src.customers.lambda_function import (
    delete_customer,
    lambda_handler,
    NotFoundError,
    DatabaseError
)


@patch('src.customers.lambda_function.dynamodb_client')
@patch('src.customers.lambda_function.dynamodb_resource')
def test_delete_customer_success(mock_dynamodb_resource, mock_dynamodb_client):
    """Test successful deletion returns HTTP 200 with success message."""
    # Setup mock for get_customer (verify exists)
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
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
    
    # Setup mock for delete_item
    mock_dynamodb_client.delete_item.return_value = {}
    
    # Execute
    result = delete_customer('test-123')
    
    # Verify
    assert result == {'message': 'Customer deleted successfully'}
    mock_table.get_item.assert_called_once_with(
        Key={'customer_id': 'test-123'}
    )
    mock_dynamodb_client.delete_item.assert_called_once_with(
        TableName='customers',
        Key={
            'customer_id': {'S': 'test-123'}
        }
    )


@patch('src.customers.lambda_function.dynamodb_resource')
def test_delete_customer_not_found(mock_dynamodb_resource):
    """Test delete with non-existent ID returns HTTP 404."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
    # DynamoDB returns empty response when item not found
    mock_table.get_item.return_value = {}
    
    # Execute and verify exception
    with pytest.raises(NotFoundError) as exc_info:
        delete_customer('non-existent-id')
    
    assert exc_info.value.message == "Customer not found"
    assert exc_info.value.status_code == 404


@patch('src.customers.lambda_function.dynamodb_client')
@patch('src.customers.lambda_function.dynamodb_resource')
def test_delete_customer_database_error(mock_dynamodb_resource, mock_dynamodb_client):
    """Test delete_customer handles database errors gracefully."""
    # Setup mock for get_customer (verify exists)
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
    customer_data = {
        'customer_id': 'test-789',
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T10:00:00Z'
    }
    
    mock_table.get_item.return_value = {
        'Item': customer_data
    }
    
    # Simulate database error on delete
    mock_dynamodb_client.delete_item.side_effect = Exception("DynamoDB connection failed")
    
    # Execute and verify exception
    with pytest.raises(DatabaseError) as exc_info:
        delete_customer('test-789')
    
    assert "Database operation failed" in str(exc_info.value.message)


@patch('src.customers.lambda_function.dynamodb_client')
@patch('src.customers.lambda_function.dynamodb_resource')
def test_lambda_handler_delete_customer_success(mock_dynamodb_resource, mock_dynamodb_client):
    """Test lambda_handler routes DELETE /customers/{customer_id} correctly."""
    # Setup mock for get_customer (verify exists)
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
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
    
    # Setup mock for delete_item
    mock_dynamodb_client.delete_item.return_value = {}
    
    # Create API Gateway event
    event = {
        'httpMethod': 'DELETE',
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
    assert body['message'] == 'Customer deleted successfully'


@patch('src.customers.lambda_function.dynamodb_resource')
def test_lambda_handler_delete_customer_not_found(mock_dynamodb_resource):
    """Test lambda_handler returns 404 when deleting non-existent customer."""
    # Setup mock
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
    # DynamoDB returns empty response
    mock_table.get_item.return_value = {}
    
    # Create API Gateway event
    event = {
        'httpMethod': 'DELETE',
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


@patch('src.customers.lambda_function.dynamodb_client')
@patch('src.customers.lambda_function.dynamodb_resource')
def test_deleted_customer_cannot_be_retrieved(mock_dynamodb_resource, mock_dynamodb_client):
    """Test that deleted customer cannot be retrieved (verifies deletion)."""
    # Setup mock for get_customer (verify exists before delete)
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
    customer_data = {
        'customer_id': 'test-456',
        'name': 'Jane Smith',
        'email': 'jane@example.com',
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T10:00:00Z'
    }
    
    # First call returns customer (exists), second call returns empty (deleted)
    mock_table.get_item.side_effect = [
        {'Item': customer_data},  # First call: customer exists
        {}  # Second call: customer not found after deletion
    ]
    
    # Setup mock for delete_item
    mock_dynamodb_client.delete_item.return_value = {}
    
    # Execute delete
    result = delete_customer('test-456')
    assert result['message'] == 'Customer deleted successfully'
    
    # Verify customer cannot be retrieved after deletion
    from src.customers.lambda_function import get_customer
    with pytest.raises(NotFoundError):
        get_customer('test-456')


@patch('src.customers.lambda_function.dynamodb_client')
@patch('src.customers.lambda_function.dynamodb_resource')
def test_delete_customer_includes_cors_headers(mock_dynamodb_resource, mock_dynamodb_client):
    """Test that delete response includes CORS headers."""
    # Setup mock for get_customer (verify exists)
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
    customer_data = {
        'customer_id': 'test-789',
        'name': 'Test User',
        'email': 'test@example.com',
        'created_at': '2024-01-15T10:00:00Z',
        'updated_at': '2024-01-15T10:00:00Z'
    }
    
    mock_table.get_item.return_value = {
        'Item': customer_data
    }
    
    # Setup mock for delete_item
    mock_dynamodb_client.delete_item.return_value = {}
    
    # Create API Gateway event
    event = {
        'httpMethod': 'DELETE',
        'path': '/customers/test-789',
        'pathParameters': {
            'customer_id': 'test-789'
        }
    }
    
    # Execute
    response = lambda_handler(event, None)
    
    # Verify CORS headers
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert response['headers']['Access-Control-Allow-Origin'] == '*'
