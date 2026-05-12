# Copyright (c) 2024 AnyCompany. All rights reserved.
# Unit Tests for Customer Validation Utilities

import pytest
import os
from unittest.mock import patch, MagicMock
from src.customers.validation import (
    validate_email,
    validate_required_fields,
    check_email_uniqueness
)


class TestValidateEmail:
    """Unit tests for email validation function."""
    
    def test_valid_email_simple(self):
        """Test that simple valid email passes validation."""
        assert validate_email("user@example.com") is True
    
    def test_valid_email_with_subdomain(self):
        """Test that email with subdomain passes validation."""
        assert validate_email("user@mail.example.com") is True
    
    def test_valid_email_with_plus(self):
        """Test that email with plus sign passes validation."""
        assert validate_email("user+tag@example.com") is True
    
    def test_valid_email_with_dots(self):
        """Test that email with dots in local part passes validation."""
        assert validate_email("first.last@example.com") is True
    
    def test_valid_email_with_numbers(self):
        """Test that email with numbers passes validation."""
        assert validate_email("user123@example456.com") is True
    
    def test_valid_email_with_hyphen(self):
        """Test that email with hyphen in domain passes validation."""
        assert validate_email("user@my-domain.com") is True
    
    def test_valid_email_with_underscore(self):
        """Test that email with underscore in local part passes validation."""
        assert validate_email("user_name@example.com") is True
    
    def test_invalid_email_no_at_symbol(self):
        """Test that email without @ symbol fails validation."""
        assert validate_email("userexample.com") is False
    
    def test_invalid_email_no_domain(self):
        """Test that email without domain fails validation."""
        assert validate_email("user@") is False
    
    def test_invalid_email_no_tld(self):
        """Test that email without TLD fails validation."""
        assert validate_email("user@domain") is False
    
    def test_invalid_email_no_local_part(self):
        """Test that email without local part fails validation."""
        assert validate_email("@example.com") is False
    
    def test_invalid_email_multiple_at_symbols(self):
        """Test that email with multiple @ symbols fails validation."""
        assert validate_email("user@@example.com") is False
    
    def test_invalid_email_spaces(self):
        """Test that email with spaces fails validation."""
        assert validate_email("user @example.com") is False
        assert validate_email("user@ example.com") is False
    
    def test_invalid_email_empty_string(self):
        """Test that empty string fails validation."""
        assert validate_email("") is False
    
    def test_invalid_email_none(self):
        """Test that None fails validation."""
        assert validate_email(None) is False
    
    def test_invalid_email_not_string(self):
        """Test that non-string input fails validation."""
        assert validate_email(123) is False
        assert validate_email([]) is False
    
    def test_invalid_email_short_tld(self):
        """Test that email with single character TLD fails validation."""
        assert validate_email("user@example.c") is False


class TestValidateRequiredFields:
    """Unit tests for required fields validation function."""
    
    def test_all_required_fields_present(self):
        """Test that validation passes when all required fields are present."""
        data = {"name": "John Doe", "email": "john@example.com"}
        # Should not raise any exception
        validate_required_fields(data, ["name", "email"])
    
    def test_single_required_field_present(self):
        """Test that validation passes with single required field."""
        data = {"name": "John Doe"}
        validate_required_fields(data, ["name"])
    
    def test_missing_single_field(self):
        """Test that validation fails when a required field is missing."""
        data = {"name": "John Doe"}
        with pytest.raises(ValueError) as exc_info:
            validate_required_fields(data, ["name", "email"])
        assert "Missing required fields: email" in str(exc_info.value)
    
    def test_missing_multiple_fields(self):
        """Test that validation fails when multiple required fields are missing."""
        data = {}
        with pytest.raises(ValueError) as exc_info:
            validate_required_fields(data, ["name", "email"])
        assert "Missing required fields:" in str(exc_info.value)
        assert "name" in str(exc_info.value)
        assert "email" in str(exc_info.value)
    
    def test_field_with_none_value(self):
        """Test that validation fails when required field has None value."""
        data = {"name": None, "email": "john@example.com"}
        with pytest.raises(ValueError) as exc_info:
            validate_required_fields(data, ["name", "email"])
        assert "Missing required fields: name" in str(exc_info.value)
    
    def test_field_with_empty_string(self):
        """Test that validation fails when required field has empty string."""
        data = {"name": "", "email": "john@example.com"}
        with pytest.raises(ValueError) as exc_info:
            validate_required_fields(data, ["name", "email"])
        assert "Missing required fields: name" in str(exc_info.value)
    
    def test_field_with_whitespace_only(self):
        """Test that validation fails when required field has only whitespace."""
        data = {"name": "   ", "email": "john@example.com"}
        with pytest.raises(ValueError) as exc_info:
            validate_required_fields(data, ["name", "email"])
        assert "Missing required fields: name" in str(exc_info.value)
    
    def test_empty_required_list(self):
        """Test that validation passes when no fields are required."""
        data = {}
        # Should not raise any exception
        validate_required_fields(data, [])
    
    def test_extra_fields_present(self):
        """Test that validation passes when extra fields are present."""
        data = {"name": "John Doe", "email": "john@example.com", "phone": "123456"}
        validate_required_fields(data, ["name", "email"])
    
    def test_field_with_zero_value(self):
        """Test that validation passes when field has zero value (not empty)."""
        data = {"name": "John Doe", "age": 0}
        validate_required_fields(data, ["name", "age"])


class TestCheckEmailUniqueness:
    """Unit tests for email uniqueness check function."""
    
    @patch('src.customers.validation.dynamodb')
    def test_email_not_found_is_unique(self, mock_dynamodb):
        """Test that email not in database is considered unique."""
        # Mock DynamoDB query to return no items
        mock_dynamodb.query.return_value = {'Items': []}
        
        result = check_email_uniqueness("new@example.com")
        
        assert result is True
        mock_dynamodb.query.assert_called_once()
        call_args = mock_dynamodb.query.call_args
        assert call_args[1]['IndexName'] == 'email-index'
        assert call_args[1]['ExpressionAttributeValues'][':email']['S'] == 'new@example.com'
    
    @patch('src.customers.validation.dynamodb')
    def test_email_exists_is_not_unique(self, mock_dynamodb):
        """Test that existing email is not considered unique."""
        # Mock DynamoDB query to return one item
        mock_dynamodb.query.return_value = {
            'Items': [
                {'customer_id': {'S': '123'}}
            ]
        }
        
        result = check_email_uniqueness("existing@example.com")
        
        assert result is False
    
    @patch('src.customers.validation.dynamodb')
    def test_email_exists_but_excluded_is_unique(self, mock_dynamodb):
        """Test that email is unique when it belongs to the excluded customer."""
        # Mock DynamoDB query to return one item with the excluded customer_id
        mock_dynamodb.query.return_value = {
            'Items': [
                {'customer_id': {'S': '123'}}
            ]
        }
        
        result = check_email_uniqueness("existing@example.com", exclude_customer_id="123")
        
        assert result is True
    
    @patch('src.customers.validation.dynamodb')
    def test_email_exists_for_different_customer_is_not_unique(self, mock_dynamodb):
        """Test that email is not unique when it belongs to a different customer."""
        # Mock DynamoDB query to return one item with different customer_id
        mock_dynamodb.query.return_value = {
            'Items': [
                {'customer_id': {'S': '456'}}
            ]
        }
        
        result = check_email_uniqueness("existing@example.com", exclude_customer_id="123")
        
        assert result is False
    
    @patch('src.customers.validation.dynamodb')
    def test_multiple_items_with_exclusion(self, mock_dynamodb):
        """Test email uniqueness with multiple items and exclusion."""
        # Mock DynamoDB query to return multiple items (should not happen in practice)
        mock_dynamodb.query.return_value = {
            'Items': [
                {'customer_id': {'S': '123'}},
                {'customer_id': {'S': '123'}}
            ]
        }
        
        result = check_email_uniqueness("existing@example.com", exclude_customer_id="123")
        
        assert result is True
    
    @patch('src.customers.validation.dynamodb')
    def test_multiple_items_with_different_customer(self, mock_dynamodb):
        """Test email uniqueness with multiple items including different customer."""
        # Mock DynamoDB query to return multiple items with different customer_id
        mock_dynamodb.query.return_value = {
            'Items': [
                {'customer_id': {'S': '123'}},
                {'customer_id': {'S': '456'}}
            ]
        }
        
        result = check_email_uniqueness("existing@example.com", exclude_customer_id="123")
        
        assert result is False
    
    @patch('src.customers.validation.dynamodb')
    def test_database_error_raises_runtime_error(self, mock_dynamodb):
        """Test that database errors are caught and re-raised as RuntimeError."""
        # Mock DynamoDB query to raise an exception
        mock_dynamodb.query.side_effect = Exception("DynamoDB connection failed")
        
        with pytest.raises(RuntimeError) as exc_info:
            check_email_uniqueness("test@example.com")
        
        assert "Database operation failed" in str(exc_info.value)
        assert "DynamoDB connection failed" in str(exc_info.value)
    
    @patch('src.customers.validation.dynamodb')
    def test_empty_items_list_is_unique(self, mock_dynamodb):
        """Test that empty Items list is treated as unique."""
        # Mock DynamoDB query to return empty Items list
        mock_dynamodb.query.return_value = {'Items': []}
        
        result = check_email_uniqueness("new@example.com")
        
        assert result is True
    
    @patch('src.customers.validation.dynamodb')
    def test_missing_items_key_is_unique(self, mock_dynamodb):
        """Test that missing Items key is treated as unique."""
        # Mock DynamoDB query to return response without Items key
        mock_dynamodb.query.return_value = {}
        
        result = check_email_uniqueness("new@example.com")
        
        assert result is True
    
    @patch('src.customers.validation.dynamodb')
    @patch.dict(os.environ, {'TABLE_NAME': 'custom-table'})
    def test_uses_table_name_from_environment(self, mock_dynamodb):
        """Test that function uses TABLE_NAME from environment variable."""
        mock_dynamodb.query.return_value = {'Items': []}
        
        check_email_uniqueness("test@example.com")
        
        call_args = mock_dynamodb.query.call_args
        assert call_args[1]['TableName'] == 'custom-table'
