# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit tests for CRUD operations structured logging

import json
import pytest
from unittest.mock import patch, MagicMock
from src.customers.lambda_function import (
    create_customer,
    get_customer,
    list_customers,
    update_customer,
    delete_customer
)


class TestCRUDLogging:
    """Test structured logging for CRUD operations."""
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.check_email_uniqueness')
    @patch('src.customers.lambda_function.logger')
    def test_create_customer_logs_with_user_identity(self, mock_logger, mock_check_email, mock_dynamodb):
        """Test that create_customer logs include user identity."""
        mock_check_email.return_value = True
        mock_dynamodb.put_item.return_value = {}
        
        customer_data = {
            'name': 'Test User',
            'email': 'test@example.com'
        }
        
        create_customer(customer_data, user_identity='user-123')
        
        # Verify logging was called
        assert mock_logger.info.called
        
        # Get the first log call (operation start)
        first_log_call = mock_logger.info.call_args_list[0][0][0]
        log_data = json.loads(first_log_call)
        
        # Verify required fields are present
        assert 'operation' in log_data
        assert 'operation_type' in log_data
        assert 'user_identity' in log_data
        assert 'timestamp' in log_data
        assert log_data['operation'] == 'create_customer'
        assert log_data['operation_type'] == 'CREATE'
        assert log_data['user_identity'] == 'user-123'
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.lambda_function.logger')
    def test_get_customer_logs_with_user_identity(self, mock_logger, mock_dynamodb):
        """Test that get_customer logs include user identity."""
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {
            'Item': {
                'customer_id': 'test-123',
                'name': 'Test User',
                'email': 'test@example.com'
            }
        }
        
        get_customer('test-123', user_identity='user-456')
        
        # Verify logging was called
        assert mock_logger.info.called
        
        # Get the first log call
        first_log_call = mock_logger.info.call_args_list[0][0][0]
        log_data = json.loads(first_log_call)
        
        # Verify required fields
        assert log_data['operation'] == 'get_customer'
        assert log_data['operation_type'] == 'READ'
        assert log_data['user_identity'] == 'user-456'
        assert log_data['customer_id'] == 'test-123'
    
    @patch('src.customers.lambda_function.dynamodb_resource')
    @patch('src.customers.lambda_function.logger')
    def test_list_customers_logs_with_user_identity(self, mock_logger, mock_dynamodb):
        """Test that list_customers logs include user identity."""
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.scan.return_value = {
            'Items': [
                {'customer_id': '1', 'name': 'User 1', 'email': 'user1@example.com'},
                {'customer_id': '2', 'name': 'User 2', 'email': 'user2@example.com'}
            ]
        }
        
        list_customers(user_identity='user-789')
        
        # Verify logging was called
        assert mock_logger.info.called
        
        # Get the first log call
        first_log_call = mock_logger.info.call_args_list[0][0][0]
        log_data = json.loads(first_log_call)
        
        # Verify required fields
        assert log_data['operation'] == 'list_customers'
        assert log_data['operation_type'] == 'READ'
        assert log_data['user_identity'] == 'user-789'
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.get_customer')
    @patch('src.customers.lambda_function.check_email_uniqueness')
    @patch('src.customers.lambda_function.logger')
    def test_update_customer_logs_with_user_identity(self, mock_logger, mock_check_email, mock_get, mock_dynamodb):
        """Test that update_customer logs include user identity."""
        mock_get.return_value = {
            'customer_id': 'test-123',
            'name': 'Old Name',
            'email': 'old@example.com',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z'
        }
        mock_check_email.return_value = True
        mock_dynamodb.update_item.return_value = {
            'Attributes': {
                'customer_id': {'S': 'test-123'},
                'name': {'S': 'New Name'},
                'email': {'S': 'old@example.com'},
                'created_at': {'S': '2024-01-01T00:00:00Z'},
                'updated_at': {'S': '2024-01-02T00:00:00Z'}
            }
        }
        
        update_customer('test-123', {'name': 'New Name'}, user_identity='user-abc')
        
        # Verify logging was called
        assert mock_logger.info.called
        
        # Find the update operation log (not the get_customer log)
        update_log = None
        for call in mock_logger.info.call_args_list:
            log_str = call[0][0]
            log_data = json.loads(log_str)
            if log_data.get('operation') == 'update_customer':
                update_log = log_data
                break
        
        # Verify required fields
        assert update_log is not None
        assert update_log['operation'] == 'update_customer'
        assert update_log['operation_type'] == 'UPDATE'
        assert update_log['user_identity'] == 'user-abc'
        assert update_log['customer_id'] == 'test-123'
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.get_customer')
    @patch('src.customers.lambda_function.logger')
    def test_delete_customer_logs_with_user_identity(self, mock_logger, mock_get, mock_dynamodb):
        """Test that delete_customer logs include user identity."""
        mock_get.return_value = {
            'customer_id': 'test-123',
            'name': 'Test User',
            'email': 'test@example.com'
        }
        mock_dynamodb.delete_item.return_value = {}
        
        delete_customer('test-123', user_identity='user-xyz')
        
        # Verify logging was called
        assert mock_logger.info.called
        
        # Find the delete operation log (not the get_customer log)
        delete_log = None
        for call in mock_logger.info.call_args_list:
            log_str = call[0][0]
            log_data = json.loads(log_str)
            if log_data.get('operation') == 'delete_customer':
                delete_log = log_data
                break
        
        # Verify required fields
        assert delete_log is not None
        assert delete_log['operation'] == 'delete_customer'
        assert delete_log['operation_type'] == 'DELETE'
        assert delete_log['user_identity'] == 'user-xyz'
        assert delete_log['customer_id'] == 'test-123'
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.check_email_uniqueness')
    @patch('src.customers.lambda_function.logger')
    def test_error_logging_includes_stack_trace(self, mock_logger, mock_check_email, mock_dynamodb):
        """Test that error logs include full stack traces."""
        mock_check_email.return_value = True
        mock_dynamodb.put_item.side_effect = Exception("Database error")
        
        customer_data = {
            'name': 'Test User',
            'email': 'test@example.com'
        }
        
        with pytest.raises(Exception):
            create_customer(customer_data, user_identity='user-error')
        
        # Verify error logging was called
        assert mock_logger.error.called
        
        # Get the error log call
        error_log_call = mock_logger.error.call_args_list[0][0][0]
        error_log_data = json.loads(error_log_call)
        
        # Verify stack trace is present
        assert 'stack_trace' in error_log_data
        assert 'error' in error_log_data
        assert 'message' in error_log_data
        assert 'user_identity' in error_log_data
        assert error_log_data['user_identity'] == 'user-error'
        assert len(error_log_data['stack_trace']) > 0
    
    @patch('src.customers.lambda_function.dynamodb_client')
    @patch('src.customers.lambda_function.check_email_uniqueness')
    @patch('src.customers.lambda_function.logger')
    def test_success_logging_includes_result(self, mock_logger, mock_check_email, mock_dynamodb):
        """Test that success logs include result field."""
        mock_check_email.return_value = True
        mock_dynamodb.put_item.return_value = {}
        
        customer_data = {
            'name': 'Test User',
            'email': 'test@example.com'
        }
        
        create_customer(customer_data, user_identity='user-success')
        
        # Find the success log (second info call)
        success_log = None
        for call in mock_logger.info.call_args_list:
            log_str = call[0][0]
            log_data = json.loads(log_str)
            if 'result' in log_data:
                success_log = log_data
                break
        
        # Verify result field is present
        assert success_log is not None
        assert success_log['result'] == 'success'
        assert success_log['user_identity'] == 'user-success'
