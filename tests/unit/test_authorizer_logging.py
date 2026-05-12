# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit Tests for Lambda Authorizer Structured Logging
# Tests JSON logging format and authentication attempt logging

import sys
import os
import json
import logging
from unittest.mock import patch, MagicMock
from io import StringIO

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'authorizer'))

from lambda_function import log_json, lambda_handler


def test_log_json_format():
    """Test that log_json produces valid JSON with required fields."""
    # Capture log output
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    try:
        # Call log_json
        log_json('INFO', 'Test message', field1='value1', field2=123)
        
        # Get the log output
        log_output = log_stream.getvalue().strip()
        
        # Parse as JSON
        log_entry = json.loads(log_output)
        
        # Verify required fields
        assert 'timestamp' in log_entry
        assert 'level' in log_entry
        assert 'message' in log_entry
        assert log_entry['level'] == 'INFO'
        assert log_entry['message'] == 'Test message'
        assert log_entry['field1'] == 'value1'
        assert log_entry['field2'] == 123
        
        # Verify timestamp format (ISO 8601 with Z suffix)
        assert log_entry['timestamp'].endswith('Z')
        
    finally:
        logger.removeHandler(handler)


def test_log_json_warning_level():
    """Test that log_json handles WARNING level correctly."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    
    try:
        log_json('WARNING', 'Warning message', reason='test_reason')
        
        log_output = log_stream.getvalue().strip()
        log_entry = json.loads(log_output)
        
        assert log_entry['level'] == 'WARNING'
        assert log_entry['message'] == 'Warning message'
        assert log_entry['reason'] == 'test_reason'
        
    finally:
        logger.removeHandler(handler)


def test_log_json_error_level():
    """Test that log_json handles ERROR level correctly."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    
    try:
        log_json('ERROR', 'Error message', error='test_error')
        
        log_output = log_stream.getvalue().strip()
        log_entry = json.loads(log_output)
        
        assert log_entry['level'] == 'ERROR'
        assert log_entry['message'] == 'Error message'
        assert log_entry['error'] == 'test_error'
        
    finally:
        logger.removeHandler(handler)


@patch('lambda_function.get_cognito_public_keys')
def test_authentication_attempt_logging_missing_token(mock_get_keys):
    """Test that missing token authentication attempts are logged with proper structure."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    try:
        # Create event with missing token
        event = {
            'authorizationToken': '',
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef/prod/GET/customers'
        }
        
        # Call lambda_handler
        result = lambda_handler(event, None)
        
        # Get all log outputs
        log_outputs = log_stream.getvalue().strip().split('\n')
        
        # Find the authentication failed log entry
        auth_failed_log = None
        for log_line in log_outputs:
            try:
                log_entry = json.loads(log_line)
                if log_entry.get('message') == 'Authentication failed':
                    auth_failed_log = log_entry
                    break
            except json.JSONDecodeError:
                continue
        
        # Verify the log entry exists and has required fields
        assert auth_failed_log is not None, "Authentication failed log entry not found"
        assert auth_failed_log['validation_result'] == 'denied'
        assert auth_failed_log['reason'] == 'missing_token'
        assert 'error_message' in auth_failed_log
        assert auth_failed_log['user_identity'] is None
        assert 'timestamp' in auth_failed_log
        
        # Verify the response
        assert result['principalId'] == 'user'
        assert result['policyDocument']['Statement'][0]['Effect'] == 'Deny'
        
    finally:
        logger.removeHandler(handler)


@patch('lambda_function.verify_token_signature')
@patch('lambda_function.get_cognito_public_keys')
def test_authentication_attempt_logging_successful(mock_get_keys, mock_verify):
    """Test that successful authentication attempts are logged with user identity."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    try:
        # Mock successful token verification
        mock_get_keys.return_value = [{'kid': 'test-key'}]
        mock_verify.return_value = {
            'sub': 'user-123',
            'cognito:username': 'testuser',
            'email': 'test@example.com',
            'exp': 9999999999  # Far future
        }
        
        # Create event with valid token
        event = {
            'authorizationToken': 'Bearer valid-token',
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef/prod/GET/customers'
        }
        
        # Call lambda_handler
        result = lambda_handler(event, None)
        
        # Get all log outputs
        log_outputs = log_stream.getvalue().strip().split('\n')
        
        # Find the authentication successful log entry
        auth_success_log = None
        for log_line in log_outputs:
            try:
                log_entry = json.loads(log_line)
                if log_entry.get('message') == 'Authentication successful':
                    auth_success_log = log_entry
                    break
            except json.JSONDecodeError:
                continue
        
        # Verify the log entry exists and has required fields
        assert auth_success_log is not None, "Authentication successful log entry not found"
        assert auth_success_log['validation_result'] == 'allowed'
        assert 'user_identity' in auth_success_log
        assert auth_success_log['user_identity']['user_id'] == 'user-123'
        assert auth_success_log['user_identity']['username'] == 'testuser'
        assert auth_success_log['user_identity']['email'] == 'test@example.com'
        assert 'timestamp' in auth_success_log
        
        # Verify the response
        assert result['principalId'] == 'user-123'
        assert result['policyDocument']['Statement'][0]['Effect'] == 'Allow'
        
    finally:
        logger.removeHandler(handler)


@patch('lambda_function.verify_token_signature')
@patch('lambda_function.get_cognito_public_keys')
def test_authentication_attempt_logging_invalid_token(mock_get_keys, mock_verify):
    """Test that invalid token authentication attempts are logged with error details."""
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    try:
        # Mock token verification failure
        from jose.exceptions import JWTError
        mock_get_keys.return_value = [{'kid': 'test-key'}]
        mock_verify.side_effect = JWTError("Invalid signature")
        
        # Create event with invalid token
        event = {
            'authorizationToken': 'Bearer invalid-token',
            'methodArn': 'arn:aws:execute-api:us-east-1:123456789012:abcdef/prod/GET/customers'
        }
        
        # Call lambda_handler
        result = lambda_handler(event, None)
        
        # Get all log outputs
        log_outputs = log_stream.getvalue().strip().split('\n')
        
        # Find the authentication failed log entry
        auth_failed_log = None
        for log_line in log_outputs:
            try:
                log_entry = json.loads(log_line)
                if log_entry.get('message') == 'Authentication failed' and log_entry.get('reason') == 'invalid_or_expired_token':
                    auth_failed_log = log_entry
                    break
            except json.JSONDecodeError:
                continue
        
        # Verify the log entry exists and has required fields
        assert auth_failed_log is not None, "Authentication failed log entry not found"
        assert auth_failed_log['validation_result'] == 'denied'
        assert auth_failed_log['reason'] == 'invalid_or_expired_token'
        assert 'error_message' in auth_failed_log
        assert auth_failed_log['user_identity'] is None
        assert 'timestamp' in auth_failed_log
        
        # Verify the response
        assert result['principalId'] == 'user'
        assert result['policyDocument']['Statement'][0]['Effect'] == 'Deny'
        
    finally:
        logger.removeHandler(handler)
