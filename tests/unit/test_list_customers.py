# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit Tests for list_customers function
# Tests retrieval of all customer records

import os
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal

# Set environment variable before importing lambda_function
os.environ['TABLE_NAME'] = 'customers'

from src.customers.lambda_function import list_customers


@patch('src.customers.lambda_function.dynamodb_resource')
def test_list_customers_returns_all_records(mock_dynamodb_resource):
    """Test list_customers returns all customer records from DynamoDB."""
    # Mock the table and scan response
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
    # Mock scan response with multiple customers
    mock_table.scan.return_value = {
        'Items': [
            {
                'customer_id': 'cust-001',
                'name': 'John Doe',
                'email': 'john@example.com',
                'phone': '+1234567890',
                'address': '123 Main St',
                'company': 'Acme Corp',
                'notes': 'VIP customer',
                'created_at': '2024-01-15T10:00:00Z',
                'updated_at': '2024-01-15T10:00:00Z'
            },
            {
                'customer_id': 'cust-002',
                'name': 'Jane Smith',
                'email': 'jane@example.com',
                'phone': None,
                'address': None,
                'company': None,
                'notes': None,
                'created_at': '2024-01-15T11:00:00Z',
                'updated_at': '2024-01-15T11:00:00Z'
            }
        ]
    }
    
    # Call list_customers
    result = list_customers()
    
    # Verify the result
    assert len(result) == 2
    assert result[0]['customer_id'] == 'cust-001'
    assert result[0]['name'] == 'John Doe'
    assert result[0]['email'] == 'john@example.com'
    assert result[1]['customer_id'] == 'cust-002'
    assert result[1]['name'] == 'Jane Smith'
    
    # Verify scan was called
    mock_table.scan.assert_called_once()


@patch('src.customers.lambda_function.dynamodb_resource')
def test_list_customers_returns_empty_array_when_no_customers(mock_dynamodb_resource):
    """Test list_customers returns empty array when no customers exist."""
    # Mock the table and scan response
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
    # Mock scan response with no items
    mock_table.scan.return_value = {
        'Items': []
    }
    
    # Call list_customers
    result = list_customers()
    
    # Verify the result is an empty list
    assert result == []
    assert len(result) == 0
    
    # Verify scan was called
    mock_table.scan.assert_called_once()


@patch('src.customers.lambda_function.dynamodb_resource')
def test_list_customers_handles_pagination(mock_dynamodb_resource):
    """Test list_customers handles paginated scan results."""
    # Mock the table
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    
    # Mock paginated scan responses
    mock_table.scan.side_effect = [
        {
            'Items': [
                {
                    'customer_id': 'cust-001',
                    'name': 'Customer 1',
                    'email': 'customer1@example.com',
                    'created_at': '2024-01-15T10:00:00Z',
                    'updated_at': '2024-01-15T10:00:00Z'
                }
            ],
            'LastEvaluatedKey': {'customer_id': 'cust-001'}
        },
        {
            'Items': [
                {
                    'customer_id': 'cust-002',
                    'name': 'Customer 2',
                    'email': 'customer2@example.com',
                    'created_at': '2024-01-15T11:00:00Z',
                    'updated_at': '2024-01-15T11:00:00Z'
                }
            ]
        }
    ]
    
    # Call list_customers
    result = list_customers()
    
    # Verify all items from both pages are returned
    assert len(result) == 2
    assert result[0]['customer_id'] == 'cust-001'
    assert result[1]['customer_id'] == 'cust-002'
    
    # Verify scan was called twice (once for each page)
    assert mock_table.scan.call_count == 2


@patch('src.customers.lambda_function.dynamodb_resource')
def test_list_customers_raises_error_on_database_failure(mock_dynamodb_resource):
    """Test list_customers raises RuntimeError when DynamoDB operation fails."""
    # Mock the table to raise an exception
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    mock_table.scan.side_effect = Exception("DynamoDB connection error")
    
    # Call list_customers and expect RuntimeError
    try:
        list_customers()
        assert False, "Expected RuntimeError to be raised"
    except RuntimeError as e:
        assert "Database operation failed" in str(e)
        assert "DynamoDB connection error" in str(e)


@patch('src.customers.lambda_function.dynamodb_resource')
def test_list_customers_uses_correct_table_name(mock_dynamodb_resource):
    """Test list_customers uses the correct table name from environment variable."""
    # Mock the table
    mock_table = MagicMock()
    mock_dynamodb_resource.Table.return_value = mock_table
    mock_table.scan.return_value = {'Items': []}
    
    # Call list_customers
    list_customers()
    
    # Verify Table was called with correct table name
    mock_dynamodb_resource.Table.assert_called_once_with('customers')
