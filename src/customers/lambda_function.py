# Copyright (c) 2024 AnyCompany. All rights reserved.
# Customer CRUD Lambda Function
# Handles Create, Read, Update, Delete operations for customer records

import json
import os
import uuid
import boto3
import logging
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Try relative imports first (for Lambda), fall back to absolute imports (for tests)
try:
    from validation import validate_email, validate_required_fields, check_email_uniqueness
    from models import Customer
except ImportError:
    from src.customers.validation import validate_email, validate_required_fields, check_email_uniqueness
    from src.customers.models import Customer

# Initialize DynamoDB resource and client
dynamodb_resource = boto3.resource('dynamodb')
dynamodb_client = boto3.client('dynamodb')

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CustomerManagementError(Exception):
    """Base exception for customer management errors."""
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(CustomerManagementError):
    """Validation error (400)."""
    def __init__(self, message: str):
        super().__init__(message, 400)


class ConflictError(CustomerManagementError):
    """Conflict error (409)."""
    def __init__(self, message: str):
        super().__init__(message, 409)


class NotFoundError(CustomerManagementError):
    """Resource not found (404)."""
    def __init__(self, message: str):
        super().__init__(message, 404)


class DatabaseError(CustomerManagementError):
    """Database operation error (500)."""
    def __init__(self, message: str):
        super().__init__(message, 500)


def get_utc_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.
    
    Returns:
        ISO 8601 formatted timestamp string (e.g., "2024-01-15T10:30:00Z")
    """
    return datetime.utcnow().isoformat() + 'Z'


def generate_customer_id() -> str:
    """
    Generate unique customer ID using UUID.
    
    Returns:
        UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
    """
    return str(uuid.uuid4())


def create_customer(customer_data: dict, user_identity: str = 'unknown') -> dict:
    """
    Create new customer record.
    
    Args:
        customer_data: Dictionary with customer fields
        user_identity: User identity from authorizer context
    
    Returns:
        Created customer record with generated customer_id
        
    Raises:
        ValidationError: Missing required fields or invalid email
        ConflictError: Email already exists
        DatabaseError: DynamoDB operation failed
    
    Requirements:
        - 2.1: Create new customer record in DynamoDB
        - 2.2: Generate unique customer_id
        - 2.3: Set created_at and updated_at timestamps
        - 2.4: Return HTTP 201 with complete customer record
        - 2.5: Validate required fields (name, email)
        - 2.6: Validate email format
        - 2.7: Check email uniqueness
        - 2.8: Accept optional fields (phone, address, company, notes)
    """
    try:
        # Validate required fields (name, email)
        validate_required_fields(customer_data, ['name', 'email'])
        
        # Validate email format
        email = customer_data['email']
        if not validate_email(email):
            raise ValidationError("Invalid email format")
        
        # Check email uniqueness
        if not check_email_uniqueness(email):
            raise ConflictError("Customer email must be unique")
        
        # Generate unique customer_id
        customer_id = generate_customer_id()
        
        # Get current UTC timestamp
        timestamp = get_utc_timestamp()
        
        # Build customer record
        customer_record = {
            'customer_id': customer_id,
            'name': customer_data['name'],
            'email': email,
            'phone': customer_data.get('phone'),
            'address': customer_data.get('address'),
            'company': customer_data.get('company'),
            'notes': customer_data.get('notes'),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Get table name from environment variable
        table_name = os.environ.get('TABLE_NAME', 'customers')
        
        # Log the operation start
        logger.info(json.dumps({
            'operation': 'create_customer',
            'operation_type': 'CREATE',
            'table': table_name,
            'customer_id': customer_id,
            'user_identity': user_identity,
            'timestamp': timestamp
        }))
        
        # Store customer record in DynamoDB using PutItem
        dynamodb_client.put_item(
            TableName=table_name,
            Item={
                'customer_id': {'S': customer_record['customer_id']},
                'name': {'S': customer_record['name']},
                'email': {'S': customer_record['email']},
                'phone': {'S': customer_record['phone']} if customer_record['phone'] else {'NULL': True},
                'address': {'S': customer_record['address']} if customer_record['address'] else {'NULL': True},
                'company': {'S': customer_record['company']} if customer_record['company'] else {'NULL': True},
                'notes': {'S': customer_record['notes']} if customer_record['notes'] else {'NULL': True},
                'created_at': {'S': customer_record['created_at']},
                'updated_at': {'S': customer_record['updated_at']}
            }
        )
        
        # Log success
        logger.info(json.dumps({
            'operation': 'create_customer',
            'operation_type': 'CREATE',
            'result': 'success',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'timestamp': get_utc_timestamp()
        }))
        
        return customer_record
        
    except ValueError as e:
        # Raised by validate_required_fields
        logger.error(json.dumps({
            'operation': 'create_customer',
            'operation_type': 'CREATE',
            'error': 'ValidationError',
            'message': str(e),
            'user_identity': user_identity,
            'stack_trace': traceback.format_exc(),
            'timestamp': get_utc_timestamp()
        }))
        raise ValidationError(str(e))
    except RuntimeError as e:
        # Raised by check_email_uniqueness
        logger.error(json.dumps({
            'operation': 'create_customer',
            'operation_type': 'CREATE',
            'error': 'DatabaseError',
            'message': str(e),
            'user_identity': user_identity,
            'stack_trace': traceback.format_exc(),
            'timestamp': get_utc_timestamp()
        }))
        raise DatabaseError(str(e))
    except Exception as e:
        # Catch any other DynamoDB errors
        if isinstance(e, (ValidationError, ConflictError)):
            raise
        logger.error(json.dumps({
            'operation': 'create_customer',
            'operation_type': 'CREATE',
            'error': 'DatabaseError',
            'message': str(e),
            'user_identity': user_identity,
            'stack_trace': traceback.format_exc(),
            'timestamp': get_utc_timestamp()
        }))
        raise DatabaseError(f"Database operation failed: {str(e)}")


def get_customer(customer_id: str, user_identity: str = 'unknown') -> Dict[str, Any]:
    """
    Retrieve customer by ID.
    
    Retrieves a single customer record from DynamoDB using the customer_id
    as the partition key. Returns the complete customer record if found.
    
    Args:
        customer_id: Unique customer identifier (UUID string)
    
    Returns:
        Customer record dictionary containing all customer fields
        (customer_id, name, email, phone, address, company, notes,
        created_at, updated_at)
        
    Raises:
        NotFoundError: If customer with the given ID does not exist
        DatabaseError: If the DynamoDB GetItem operation fails
    
    Example:
        >>> customer = get_customer("123e4567-e89b-12d3-a456-426614174000")
        >>> customer['name']
        'John Doe'
        >>> customer['email']
        'john@example.com'
    
    Requirements:
        - 3.1: Retrieve customer from DynamoDB using GetItem
        - 3.2: Return HTTP 200 with complete customer record
        - 3.3: Return HTTP 404 if customer not found
    """
    try:
        # Get table name from environment variable
        table_name = os.environ.get('TABLE_NAME', 'customers')
        table = dynamodb_resource.Table(table_name)
        
        # Log the operation
        logger.info(json.dumps({
            'operation': 'get_customer',
            'operation_type': 'READ',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'table': table_name,
            'timestamp': get_utc_timestamp()
        }))
        
        # Retrieve customer from DynamoDB using GetItem
        response = table.get_item(
            Key={'customer_id': customer_id}
        )
        
        # Check if customer exists
        if 'Item' not in response:
            logger.info(json.dumps({
                'operation': 'get_customer',
                'operation_type': 'READ',
                'customer_id': customer_id,
                'user_identity': user_identity,
                'result': 'not_found',
                'timestamp': get_utc_timestamp()
            }))
            raise NotFoundError("Customer not found")
        
        # Log success
        logger.info(json.dumps({
            'operation': 'get_customer',
            'operation_type': 'READ',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'result': 'success',
            'timestamp': get_utc_timestamp()
        }))
        
        # Return customer record
        return response['Item']
        
    except NotFoundError:
        raise
    except Exception as e:
        # Log the error with full stack trace
        logger.error(json.dumps({
            'operation': 'get_customer',
            'operation_type': 'READ',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'error': str(e),
            'stack_trace': traceback.format_exc(),
            'timestamp': get_utc_timestamp()
        }))
        raise DatabaseError(f"Database operation failed: {str(e)}")


def list_customers(user_identity: str = 'unknown') -> List[Dict[str, Any]]:
    """
    Retrieve all customer records from DynamoDB.
    
    Uses DynamoDB Scan operation to retrieve all customer records from the
    customers table. This operation reads all items in the table.
    
    Returns:
        List of customer record dictionaries. Each dictionary contains all
        customer fields (customer_id, name, email, phone, address, company,
        notes, created_at, updated_at).
    
    Raises:
        RuntimeError: If the DynamoDB Scan operation fails
    
    Example:
        >>> customers = list_customers()
        >>> len(customers)
        5
        >>> customers[0]['name']
        'John Doe'
    
    Requirements:
        - 3.4: Retrieve all customers using Scan operation
        - 3.5: Return HTTP 200 with array of customer records
    """
    try:
        # Get table name from environment variable
        table_name = os.environ.get('TABLE_NAME', 'customers')
        table = dynamodb_resource.Table(table_name)
        
        # Log the operation
        logger.info(json.dumps({
            'operation': 'list_customers',
            'operation_type': 'READ',
            'user_identity': user_identity,
            'table': table_name,
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }))
        
        # Perform Scan operation to retrieve all customers
        response = table.scan()
        
        # Extract items from response
        customers = response.get('Items', [])
        
        # Handle pagination if there are more items
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            customers.extend(response.get('Items', []))
        
        # Log success
        logger.info(json.dumps({
            'operation': 'list_customers',
            'operation_type': 'READ',
            'result': 'success',
            'user_identity': user_identity,
            'count': len(customers),
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }))
        
        return customers
        
    except Exception as e:
        # Log the error with full stack trace
        logger.error(json.dumps({
            'operation': 'list_customers',
            'operation_type': 'READ',
            'user_identity': user_identity,
            'error': str(e),
            'stack_trace': traceback.format_exc(),
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }))
        raise RuntimeError(f"Database operation failed: {str(e)}")


def delete_customer(customer_id: str, user_identity: str = 'unknown') -> dict:
    """
    Delete customer record.
    
    Deletes a customer record from DynamoDB after verifying it exists.
    Returns a success message upon successful deletion.
    
    Args:
        customer_id: Unique customer identifier (UUID string)
    
    Returns:
        Success message dictionary with "message" key
        
    Raises:
        NotFoundError: If customer with the given ID does not exist
        DatabaseError: If the DynamoDB operation fails
    
    Example:
        >>> result = delete_customer("123e4567-e89b-12d3-a456-426614174000")
        >>> result['message']
        'Customer deleted successfully'
    
    Requirements:
        - 5.1: Delete customer from DynamoDB using DeleteItem
        - 5.2: Return HTTP 200 with success message
        - 5.3: Return HTTP 404 if customer not found
    """
    try:
        # Get table name from environment variable
        table_name = os.environ.get('TABLE_NAME', 'customers')
        
        # Log the operation
        logger.info(json.dumps({
            'operation': 'delete_customer',
            'operation_type': 'DELETE',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'table': table_name,
            'timestamp': get_utc_timestamp()
        }))
        
        # Verify customer exists using GetItem (return 404 if not found)
        customer = get_customer(customer_id, user_identity)
        
        # Delete customer from DynamoDB using DeleteItem
        dynamodb_client.delete_item(
            TableName=table_name,
            Key={
                'customer_id': {'S': customer_id}
            }
        )
        
        # Log success
        logger.info(json.dumps({
            'operation': 'delete_customer',
            'operation_type': 'DELETE',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'result': 'success',
            'timestamp': get_utc_timestamp()
        }))
        
        # Return success message
        return {
            'message': 'Customer deleted successfully'
        }
        
    except NotFoundError:
        # Re-raise NotFoundError from get_customer
        raise
    except Exception as e:
        # Log the error with full stack trace
        logger.error(json.dumps({
            'operation': 'delete_customer',
            'operation_type': 'DELETE',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'error': str(e),
            'stack_trace': traceback.format_exc(),
            'timestamp': get_utc_timestamp()
        }))
        raise DatabaseError(f"Database operation failed: {str(e)}")


def update_customer(customer_id: str, update_data: dict, user_identity: str = 'unknown') -> Dict[str, Any]:
    """
    Update existing customer record.
    
    Updates an existing customer record in DynamoDB with the provided data.
    Supports partial updates (only updates fields that are provided).
    Validates email format and uniqueness if email is being updated.
    Preserves created_at timestamp and updates updated_at to current time.
    
    Args:
        customer_id: Unique customer identifier (UUID string)
        update_data: Dictionary with fields to update (can be partial)
    
    Returns:
        Complete updated customer record dictionary containing all customer
        fields (customer_id, name, email, phone, address, company, notes,
        created_at, updated_at)
        
    Raises:
        NotFoundError: If customer with the given ID does not exist
        ValidationError: If email format is invalid
        ConflictError: If email already exists for a different customer
        DatabaseError: If the DynamoDB operation fails
    
    Example:
        >>> updated = update_customer("123e4567-e89b-12d3-a456-426614174000", 
        ...                          {"name": "Jane Doe", "phone": "555-1234"})
        >>> updated['name']
        'Jane Doe'
        >>> updated['phone']
        '555-1234'
    
    Requirements:
        - 4.1: Update customer record in DynamoDB using UpdateItem
        - 4.2: Update updated_at timestamp to current UTC time
        - 4.3: Preserve created_at timestamp from original record
        - 4.4: Return HTTP 200 with complete updated customer record
        - 4.5: Return HTTP 404 if customer not found
        - 4.6: Validate email format if email is being updated
        - 4.7: Check email uniqueness if email is being updated (exclude current customer)
        - 4.8: Support partial updates of customer fields
    """
    try:
        # Get table name from environment variable
        table_name = os.environ.get('TABLE_NAME', 'customers')
        
        # Log the operation
        logger.info(json.dumps({
            'operation': 'update_customer',
            'operation_type': 'UPDATE',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'table': table_name,
            'timestamp': get_utc_timestamp()
        }))
        
        # Verify customer exists using GetItem
        existing_customer = get_customer(customer_id, user_identity)
        
        # Validate email format if email is being updated
        if 'email' in update_data:
            email = update_data['email']
            if not validate_email(email):
                raise ValidationError("Invalid email format")
            
            # Check email uniqueness (exclude current customer)
            if not check_email_uniqueness(email, exclude_customer_id=customer_id):
                raise ConflictError("Customer email must be unique")
        
        # Build UpdateExpression and ExpressionAttributeValues
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # Update updated_at timestamp to current UTC time
        current_timestamp = get_utc_timestamp()
        update_expression_parts.append('#updated_at = :updated_at')
        expression_attribute_values[':updated_at'] = {'S': current_timestamp}
        expression_attribute_names['#updated_at'] = 'updated_at'
        
        # Add fields from update_data
        updateable_fields = ['name', 'email', 'phone', 'address', 'company', 'notes']
        for field in updateable_fields:
            if field in update_data:
                value = update_data[field]
                update_expression_parts.append(f'#{field} = :{field}')
                expression_attribute_names[f'#{field}'] = field
                
                # Handle None values
                if value is None:
                    expression_attribute_values[f':{field}'] = {'NULL': True}
                else:
                    expression_attribute_values[f':{field}'] = {'S': str(value)}
        
        # Build the complete UpdateExpression
        update_expression = 'SET ' + ', '.join(update_expression_parts)
        
        # Update customer in DynamoDB using UpdateItem
        response = dynamodb_client.update_item(
            TableName=table_name,
            Key={'customer_id': {'S': customer_id}},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        # Convert DynamoDB response to customer record format
        updated_item = response['Attributes']
        customer_record = {
            'customer_id': updated_item['customer_id']['S'],
            'name': updated_item['name']['S'],
            'email': updated_item['email']['S'],
            'phone': updated_item['phone'].get('S') if 'phone' in updated_item and 'S' in updated_item['phone'] else None,
            'address': updated_item['address'].get('S') if 'address' in updated_item and 'S' in updated_item['address'] else None,
            'company': updated_item['company'].get('S') if 'company' in updated_item and 'S' in updated_item['company'] else None,
            'notes': updated_item['notes'].get('S') if 'notes' in updated_item and 'S' in updated_item['notes'] else None,
            'created_at': updated_item['created_at']['S'],
            'updated_at': updated_item['updated_at']['S']
        }
        
        # Log success
        logger.info(json.dumps({
            'operation': 'update_customer',
            'operation_type': 'UPDATE',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'result': 'success',
            'timestamp': get_utc_timestamp()
        }))
        
        return customer_record
        
    except (NotFoundError, ValidationError, ConflictError):
        raise
    except RuntimeError as e:
        # Raised by check_email_uniqueness
        logger.error(json.dumps({
            'operation': 'update_customer',
            'operation_type': 'UPDATE',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'error': 'DatabaseError',
            'message': str(e),
            'stack_trace': traceback.format_exc(),
            'timestamp': get_utc_timestamp()
        }))
        raise DatabaseError(str(e))
    except Exception as e:
        # Catch any other DynamoDB errors
        logger.error(json.dumps({
            'operation': 'update_customer',
            'operation_type': 'UPDATE',
            'customer_id': customer_id,
            'user_identity': user_identity,
            'error': 'DatabaseError',
            'message': str(e),
            'stack_trace': traceback.format_exc(),
            'timestamp': get_utc_timestamp()
        }))
        raise DatabaseError(f"Database operation failed: {str(e)}")


def handle_error(error: Exception) -> dict:
    """
    Convert exception to API Gateway response.
    
    Args:
        error: Exception to handle
    
    Returns:
        API Gateway response with error details
    """
    if isinstance(error, CustomerManagementError):
        status_code = error.status_code
        message = error.message
        error_type = error.__class__.__name__
    else:
        status_code = 500
        message = "Internal server error"
        error_type = "InternalServerError"
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': error_type,
            'message': message,
            'timestamp': get_utc_timestamp()
        })
    }


def lambda_handler(event, context):
    """
    Customer CRUD handler for API Gateway proxy integration.
    
    Args:
        event: API Gateway proxy event containing:
            - httpMethod: HTTP method (GET, POST, PUT, DELETE)
            - path: Request path
            - pathParameters: Path parameters (e.g., customer_id)
            - body: JSON request body (for POST/PUT)
            - requestContext: Request context with authorizer data
        context: Lambda context object
    
    Returns:
        API Gateway proxy response with:
            - statusCode: HTTP status code
            - headers: Response headers (Content-Type, CORS)
            - body: JSON response body
    """
    try:
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        
        # Extract user identity from requestContext.authorizer
        request_context = event.get('requestContext', {})
        authorizer_context = request_context.get('authorizer', {})
        user_identity = authorizer_context.get('principalId', 'unknown')
        
        # Log the incoming request
        logger.info(json.dumps({
            'event': 'request_received',
            'method': http_method,
            'path': path,
            'user_identity': user_identity,
            'timestamp': get_utc_timestamp()
        }))
        
        # Route GET /customers/{customer_id}
        if http_method == 'GET' and 'customer_id' in path_parameters:
            customer_id = path_parameters['customer_id']
            customer = get_customer(customer_id, user_identity)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(customer)
            }
        
        # Route GET /customers (list all)
        if http_method == 'GET' and path == '/customers' and 'customer_id' not in path_parameters:
            customers = list_customers(user_identity)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'customers': customers
                })
            }
        
        # Route POST /customers to create_customer
        if http_method == 'POST' and path == '/customers':
            # Parse JSON body
            try:
                body = json.loads(event.get('body', '{}'))
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format")
            
            # Create customer
            customer_record = create_customer(body, user_identity)
            
            # Return HTTP 201 with complete customer record
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(customer_record)
            }
        
        # Route PUT /customers/{customer_id} to update_customer
        if http_method == 'PUT' and 'customer_id' in path_parameters:
            customer_id = path_parameters['customer_id']
            
            # Parse JSON body
            try:
                body = json.loads(event.get('body', '{}'))
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format")
            
            # Update customer
            customer_record = update_customer(customer_id, body, user_identity)
            
            # Return HTTP 200 with complete updated customer record
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(customer_record)
            }
        
        # Route DELETE /customers/{customer_id}
        if http_method == 'DELETE' and 'customer_id' in path_parameters:
            customer_id = path_parameters['customer_id']
            result = delete_customer(customer_id, user_identity)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result)
            }
        
        # Placeholder for other operations
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'NotFound',
                'message': 'Endpoint not implemented',
                'timestamp': get_utc_timestamp()
            })
        }
        
    except Exception as e:
        return handle_error(e)
