# Copyright (c) 2024 AnyCompany. All rights reserved.
# Customer Validation Utilities
# Provides validation functions for customer data

import re
import os
import boto3
from typing import List, Optional


# Email validation regex pattern (RFC 5322 simplified)
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Initialize DynamoDB client
dynamodb = boto3.client('dynamodb')


def validate_email(email: str) -> bool:
    """
    Validate email format using regex pattern.
    
    Uses a simplified RFC 5322 pattern that matches common email formats:
    - Local part: alphanumeric, dots, underscores, percent, plus, hyphen
    - @ symbol
    - Domain: alphanumeric, dots, hyphens
    - TLD: at least 2 alphabetic characters
    
    Args:
        email: Email address string to validate
    
    Returns:
        True if email format is valid, False otherwise
    
    Examples:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid.email")
        False
        >>> validate_email("user@domain")
        False
        >>> validate_email("user@example.co.uk")
        True
    
    Requirements:
        - 2.6: Email format validation for create operation
        - 4.6: Email format validation for update operation
    """
    if not email or not isinstance(email, str):
        return False
    
    return EMAIL_PATTERN.match(email) is not None


def validate_required_fields(data: dict, required: List[str]) -> None:
    """
    Validate that required fields are present in the data dictionary.
    
    Checks that all required field names exist in the data dictionary
    and that their values are not None or empty strings.
    
    Args:
        data: Dictionary containing customer data
        required: List of required field names
    
    Raises:
        ValueError: If any required fields are missing or empty,
                   with message "Missing required fields: [field_names]"
    
    Examples:
        >>> validate_required_fields({"name": "John", "email": "john@example.com"}, ["name", "email"])
        # No exception raised
        
        >>> validate_required_fields({"name": "John"}, ["name", "email"])
        ValueError: Missing required fields: email
        
        >>> validate_required_fields({"name": "", "email": "john@example.com"}, ["name", "email"])
        ValueError: Missing required fields: name
    
    Requirements:
        - 2.5: Validate required fields (name, email) for create operation
        - 4.7: Support partial updates (only validate fields being updated)
    """
    missing_fields = []
    
    for field in required:
        if field not in data or data[field] is None or (isinstance(data[field], str) and data[field].strip() == ''):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def check_email_uniqueness(email: str, exclude_customer_id: Optional[str] = None) -> bool:
    """
    Check if email is unique in the system using the email-index GSI.
    
    Queries the DynamoDB email-index Global Secondary Index to determine
    if the email address is already in use by another customer.
    
    Args:
        email: Email address to check for uniqueness
        exclude_customer_id: Optional customer_id to exclude from the check.
                           Used during update operations to allow a customer
                           to keep their existing email address.
    
    Returns:
        True if email is unique (not found or only found for excluded customer),
        False if email already exists for a different customer
    
    Raises:
        RuntimeError: If the GSI query fails with a database error
    
    Examples:
        >>> check_email_uniqueness("new@example.com")
        True  # Email not in use
        
        >>> check_email_uniqueness("existing@example.com")
        False  # Email already in use
        
        >>> check_email_uniqueness("existing@example.com", exclude_customer_id="123")
        True  # Email belongs to customer 123, so it's unique for them
    
    Requirements:
        - 2.7: Check email uniqueness for create operation using GSI
        - 4.7: Check email uniqueness for update operation (excluding current customer)
        - 6.5: Use email-index GSI for efficient email lookups
    """
    try:
        # Get table name from environment variable
        table_name = os.environ.get('TABLE_NAME', 'customers')
        
        # Query the email-index GSI
        response = dynamodb.query(
            TableName=table_name,
            IndexName='email-index',
            KeyConditionExpression='email = :email',
            ExpressionAttributeValues={
                ':email': {'S': email}
            },
            ProjectionExpression='customer_id'
        )
        
        # Check if any items were found
        items = response.get('Items', [])
        
        if not items:
            # No customer with this email exists
            return True
        
        if exclude_customer_id:
            # Check if all found items are the excluded customer
            for item in items:
                customer_id = item.get('customer_id', {}).get('S', '')
                if customer_id != exclude_customer_id:
                    # Found a different customer with this email
                    return False
            # All found items are the excluded customer
            return True
        
        # Email exists and no exclusion specified
        return False
        
    except Exception as e:
        # Log the error and raise a RuntimeError
        raise RuntimeError(f"Database operation failed: {str(e)}")
