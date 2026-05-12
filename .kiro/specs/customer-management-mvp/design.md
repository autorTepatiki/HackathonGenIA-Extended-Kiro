# Design Document

## Architecture Overview

The Customer Management MVP follows a serverless architecture pattern on AWS, implementing a three-tier design:

1. **API Layer**: Amazon API Gateway provides RESTful endpoints with Lambda Authorizer for authentication
2. **Business Logic Layer**: AWS Lambda functions handle CRUD operations and authorization logic
3. **Data Layer**: Amazon DynamoDB provides persistent, scalable NoSQL storage

### High-Level Architecture

```
┌─────────────┐
│   Client    │
│ Application │
└──────┬──────┘
       │ HTTPS + JWT
       ▼
┌─────────────────────────────────────┐
│      API Gateway (REST API)         │
│  - CORS enabled                     │
│  - JSON content type                │
└──────┬──────────────────────────────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐    ┌──────────────────┐
│   Lambda    │    │  Customer CRUD   │
│ Authorizer  │    │     Lambda       │
│             │    │                  │
│ - Validate  │    │ - Create         │
│   JWT       │    │ - Read           │
│ - Extract   │    │ - Update         │
│   Identity  │    │ - Delete         │
└──────┬──────┘    └────────┬─────────┘
       │                    │
       │                    ▼
       │            ┌───────────────┐
       │            │   DynamoDB    │
       │            │     Table     │
       │            │  (Customers)  │
       │            └───────────────┘
       │
       ▼
┌─────────────┐
│   Cognito   │
│  User Pool  │
│ (JWT Issuer)│
└─────────────┘
```

## Component Design

### 1. Lambda Authorizer

**Purpose**: Validates JWT tokens issued by Cognito User Pool and enforces authentication for all API endpoints.

**Responsibilities**:
- Extract JWT token from Authorization header
- Validate token signature against Cognito public keys
- Verify token expiration
- Extract user identity from token claims
- Generate IAM policy allowing or denying API Gateway invocation

**Interface**:

```python
def lambda_handler(event: dict, context: object) -> dict:
    """
    Lambda Authorizer handler for API Gateway.
    
    Args:
        event: API Gateway authorizer event containing:
            - authorizationToken: Bearer token from Authorization header
            - methodArn: ARN of the API Gateway method being invoked
        context: Lambda context object
    
    Returns:
        IAM policy document with Allow or Deny effect
        
    Raises:
        Unauthorized: When token is missing (returns 401)
        Forbidden: When token is invalid or expired (returns 403)
    """
```

**Key Functions**:

```python
def extract_token(authorization_header: str) -> str:
    """Extract JWT token from 'Bearer <token>' format."""

def verify_token_signature(token: str, cognito_keys: list) -> dict:
    """Verify JWT signature against Cognito public keys."""

def validate_token_expiration(token_claims: dict) -> bool:
    """Check if token is expired based on 'exp' claim."""

def extract_user_identity(token_claims: dict) -> str:
    """Extract user identifier from token claims."""

def generate_policy(principal_id: str, effect: str, resource: str) -> dict:
    """Generate IAM policy document for API Gateway."""
```

**Error Handling**:
- Missing token → HTTP 401 with message "Missing authentication token"
- Invalid signature → HTTP 403 with message "Invalid or expired token"
- Expired token → HTTP 403 with message "Invalid or expired token"
- Malformed token → HTTP 403 with message "Invalid or expired token"

**Dependencies**:
- `boto3`: AWS SDK for retrieving Cognito public keys
- `python-jose`: JWT decoding and signature verification
- `datetime`: Token expiration validation

### 2. Customer CRUD Lambda

**Purpose**: Implements business logic for customer data management operations.

**Responsibilities**:
- Validate incoming request data
- Generate unique customer IDs
- Manage timestamps (created_at, updated_at)
- Perform DynamoDB operations (PutItem, GetItem, UpdateItem, DeleteItem, Scan)
- Format responses with appropriate HTTP status codes
- Handle and log errors

**Interface**:

```python
def lambda_handler(event: dict, context: object) -> dict:
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
```

**Key Functions**:

```python
def create_customer(customer_data: dict) -> dict:
    """
    Create new customer record.
    
    Args:
        customer_data: Dictionary with customer fields
    
    Returns:
        Created customer record with generated customer_id
        
    Raises:
        ValidationError: Missing required fields or invalid email
    """

def get_customer(customer_id: str) -> dict:
    """
    Retrieve customer by ID.
    
    Args:
        customer_id: Unique customer identifier
    
    Returns:
        Customer record
        
    Raises:
        NotFoundError: Customer does not exist
    """

def list_customers() -> list:
    """
    Retrieve all customer records.
    
    Returns:
        List of customer records
    """

def update_customer(customer_id: str, update_data: dict) -> dict:
    """
    Update existing customer record.
    
    Args:
        customer_id: Unique customer identifier
        update_data: Dictionary with fields to update
    
    Returns:
        Updated customer record
        
    Raises:
        NotFoundError: Customer does not exist
        ValidationError: Invalid email format
    """

def delete_customer(customer_id: str) -> dict:
    """
    Delete customer record.
    
    Args:
        customer_id: Unique customer identifier
    
    Returns:
        Success message
        
    Raises:
        NotFoundError: Customer does not exist
    """

def validate_email(email: str) -> bool:
    """Validate email format using regex."""

def validate_required_fields(data: dict, required: list) -> None:
    """Validate required fields are present."""

def check_email_uniqueness(email: str, exclude_customer_id: str = None) -> bool:
    """
    Check if email is unique in the system.
    
    Args:
        email: Email address to check
        exclude_customer_id: Optional customer_id to exclude from check (for updates)
    
    Returns:
        True if email is unique, False if already exists
        
    Raises:
        DatabaseError: If GSI query fails
    """

def generate_customer_id() -> str:
    """Generate unique customer ID using UUID."""

def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
```

**Validation Rules**:
- Required fields: `name`, `email`
- Optional fields: `phone`, `address`, `company`, `notes`
- Email format: Standard email regex pattern
- Partial updates: Allow updating subset of fields

**Response Formats**:

```python
# Success Response (200/201)
{
    "customer_id": "uuid-string",
    "name": "string",
    "email": "string",
    "phone": "string",
    "address": "string",
    "company": "string",
    "notes": "string",
    "created_at": "ISO-8601-timestamp",
    "updated_at": "ISO-8601-timestamp"
}

# Error Response (400/404/500)
{
    "error": "error-type",
    "message": "detailed-error-message",
    "timestamp": "ISO-8601-timestamp"
}

# Delete Success Response (200)
{
    "message": "Customer deleted successfully"
}

# List Response (200)
{
    "customers": [
        { /* customer record */ },
        { /* customer record */ }
    ]
}
```

**Dependencies**:
- `boto3`: DynamoDB client
- `uuid`: Customer ID generation
- `datetime`: Timestamp generation
- `json`: Request/response parsing
- `re`: Email validation

### 3. DynamoDB Table

**Purpose**: Persistent storage for customer records.

**Schema**:

```
Table Name: customers
Partition Key: customer_id (String)
Billing Mode: PAY_PER_REQUEST (on-demand)

Attributes:
- customer_id: String (Primary Key)
- name: String (Required)
- email: String (Required)
- phone: String (Optional)
- address: String (Optional)
- company: String (Optional)
- notes: String (Optional)
- created_at: String (ISO 8601 timestamp)
- updated_at: String (ISO 8601 timestamp)

Global Secondary Indexes:
- email-index:
  - Partition Key: email (String)
  - Projection Type: ALL
  - Purpose: Enable efficient email uniqueness checks and email-based lookups
```

**Access Patterns**:
1. Get customer by ID: `GetItem` on partition key
2. List all customers: `Scan` operation
3. Create customer: `PutItem` with new customer_id
4. Update customer: `UpdateItem` on partition key
5. Delete customer: `DeleteItem` on partition key
6. Check email uniqueness: `Query` on email-index GSI

### 4. API Gateway

**Purpose**: Expose RESTful HTTP endpoints for customer management.

**Endpoints**:

| Method | Path | Description | Request Body | Response |
|--------|------|-------------|--------------|----------|
| POST | /customers | Create customer | Customer data | 201 + Customer record |
| GET | /customers | List all customers | None | 200 + Customer array |
| GET | /customers/{customer_id} | Get customer by ID | None | 200 + Customer record |
| PUT | /customers/{customer_id} | Update customer | Update data | 200 + Customer record |
| DELETE | /customers/{customer_id} | Delete customer | None | 200 + Success message |

**Configuration**:
- Integration Type: Lambda Proxy Integration
- Authorization: Custom Lambda Authorizer (all endpoints)
- CORS: Enabled with appropriate headers
- Content Type: application/json
- Stage: prod

**CORS Headers**:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### 5. Cognito User Pool

**Purpose**: User authentication and JWT token issuance.

**Configuration**:
- User Pool Name: customer-management-users
- Sign-in Options: Username or Email
- MFA: Optional (disabled for MVP)
- Password Policy: AWS default
- Token Expiration: 1 hour (default)

**JWT Claims**:
- `sub`: User unique identifier
- `email`: User email address
- `cognito:username`: Username
- `exp`: Token expiration timestamp
- `iss`: Issuer (Cognito User Pool URL)

## Data Models

### Customer Record

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Customer:
    """Customer data model."""
    customer_id: str
    name: str
    email: str
    created_at: str
    updated_at: str
    phone: Optional[str] = None
    address: Optional[str] = None
    company: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DynamoDB."""
        return {
            'customer_id': self.customer_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'company': self.company,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Customer':
        """Create from DynamoDB item."""
        return cls(
            customer_id=data['customer_id'],
            name=data['name'],
            email=data['email'],
            phone=data.get('phone'),
            address=data.get('address'),
            company=data.get('company'),
            notes=data.get('notes'),
            created_at=data['created_at'],
            updated_at=data['updated_at']
        )
```

### Authorization Context

```python
@dataclass
class AuthContext:
    """Authorization context from Lambda Authorizer."""
    user_id: str
    username: str
    email: str
    
    @classmethod
    def from_authorizer(cls, authorizer_data: dict) -> 'AuthContext':
        """Extract from API Gateway authorizer context."""
        return cls(
            user_id=authorizer_data.get('sub'),
            username=authorizer_data.get('username'),
            email=authorizer_data.get('email')
        )
```

## Error Handling

### Error Categories

1. **Authentication Errors (401/403)**
   - Missing token
   - Invalid token signature
   - Expired token
   - Malformed token

2. **Validation Errors (400)**
   - Missing required fields
   - Invalid email format
   - Malformed JSON
   - Invalid request parameters

3. **Not Found Errors (404)**
   - Customer ID does not exist

4. **Server Errors (500)**
   - DynamoDB operation failures
   - Unexpected exceptions
   - Service unavailability

### Error Response Format

All errors follow a consistent JSON structure:

```python
{
    "error": "ErrorType",
    "message": "Human-readable error description",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Handling Strategy

```python
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

class NotFoundError(CustomerManagementError):
    """Resource not found (404)."""
    def __init__(self, message: str):
        super().__init__(message, 404)

class DatabaseError(CustomerManagementError):
    """Database operation error (500)."""
    def __init__(self, message: str):
        super().__init__(message, 500)

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
    else:
        status_code = 500
        message = "Internal server error"
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': error.__class__.__name__,
            'message': message,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    }
```

### Logging Strategy

All errors are logged to CloudWatch Logs with:
- Full stack trace
- Request context (method, path, parameters)
- User identity (from authorizer)
- Timestamp
- Error details

```python
import logging
import traceback

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_error(error: Exception, context: dict):
    """Log error with full context."""
    logger.error(
        f"Error: {error.__class__.__name__}",
        extra={
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'request_context': context,
            'timestamp': datetime.utcnow().isoformat()
        }
    )
```

## Security Considerations

### Authentication Flow

1. User authenticates with Cognito (outside system scope)
2. Cognito issues JWT token
3. Client includes token in Authorization header: `Bearer <token>`
4. API Gateway invokes Lambda Authorizer
5. Authorizer validates token and returns IAM policy
6. API Gateway enforces policy (Allow/Deny)
7. If allowed, request proceeds to CRUD Lambda

### Token Validation

The Lambda Authorizer performs comprehensive token validation:

1. **Presence Check**: Verify Authorization header exists
2. **Format Check**: Verify "Bearer <token>" format
3. **Signature Verification**: Validate JWT signature using Cognito public keys (JWKS)
4. **Expiration Check**: Verify token is not expired
5. **Issuer Check**: Verify token was issued by correct Cognito User Pool
6. **Claims Extraction**: Extract user identity from token claims

### IAM Permissions

Lambda functions require specific IAM permissions:

**Customer CRUD Lambda**:
- `dynamodb:PutItem` - Create customers
- `dynamodb:GetItem` - Read customer by ID
- `dynamodb:Scan` - List all customers
- `dynamodb:UpdateItem` - Update customers
- `dynamodb:DeleteItem` - Delete customers
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` - CloudWatch logging

**Lambda Authorizer**:
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` - CloudWatch logging
- No DynamoDB permissions required

### Data Protection

- **In Transit**: All API communication over HTTPS (enforced by API Gateway)
- **At Rest**: DynamoDB encryption at rest (AWS managed keys)
- **Access Control**: All endpoints require valid JWT token
- **Least Privilege**: Lambda IAM roles have minimal required permissions

## Infrastructure as Code

### Terraform Structure

```
infra/
├── main.tf           # Main resource definitions
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── providers.tf      # Provider configuration
├── versions.tf       # Terraform and provider versions
├── terraform.tfvars  # Default variable values
└── envs/
    ├── dev.tfvars    # Development environment
    └── prod.tfvars   # Production environment
```

### Key Resources

```hcl
# DynamoDB Table
resource "aws_dynamodb_table" "customers" {
  name         = "customers"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "customer_id"
  
  attribute {
    name = "customer_id"
    type = "S"
  }
  
  attribute {
    name = "email"
    type = "S"
  }
  
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }
}

# Lambda Functions
resource "aws_lambda_function" "authorizer" {
  function_name = "customer-management-authorizer"
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.authorizer_role.arn
  filename      = "authorizer.zip"
}

resource "aws_lambda_function" "crud" {
  function_name = "customer-management-crud"
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"
  role          = aws_iam_role.crud_role.arn
  filename      = "crud.zip"
  
  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.customers.name
    }
  }
}

# API Gateway
resource "aws_api_gateway_rest_api" "customer_api" {
  name        = "customer-management-api"
  description = "Customer Management REST API"
}

# Cognito User Pool
resource "aws_cognito_user_pool" "users" {
  name = "customer-management-users"
}
```

### Outputs

```hcl
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_deployment.prod.invoke_url
}

output "user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.users.id
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.customers.name
}
```

## Deployment Process

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (version >= 1.0)
3. Python 3.11 installed
4. Lambda deployment packages built

### Build Lambda Packages

```bash
# Build Authorizer Lambda
cd src/authorizer
pip install -r requirements.txt -t .
zip -r ../../infra/authorizer.zip .

# Build CRUD Lambda
cd ../customers
pip install -r requirements.txt -t .
zip -r ../../infra/crud.zip .
```

### Deploy Infrastructure

```bash
cd infra
terraform init
terraform plan -var-file="envs/dev.tfvars"
terraform apply -var-file="envs/dev.tfvars"
```

### Post-Deployment

1. Note API Gateway endpoint URL from Terraform output
2. Create test user in Cognito User Pool
3. Obtain JWT token for testing
4. Test API endpoints with token

## Testing Strategy

### Unit Tests

Unit tests focus on specific examples, edge cases, and error conditions:

**Authorizer Tests**:
- Valid token extraction and validation
- Missing token error handling
- Invalid token format error handling
- Expired token error handling
- Malformed token error handling

**CRUD Tests**:
- Valid customer creation
- Missing required fields error handling
- Invalid email format error handling
- Customer retrieval by ID
- Non-existent customer error handling
- Customer update with valid data
- Customer deletion
- Partial update handling

**Validation Tests**:
- Email format validation (valid and invalid cases)
- Required field validation
- JSON parsing error handling

### Property-Based Tests

Property-based tests verify universal properties across all inputs with minimum 100 iterations per test.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified the following redundancies:

**Redundancies Identified**:
1. Properties 3.2 and 3.5 (response format for GET operations) are covered by properties 3.1 and 3.4
2. Properties 2.4, 4.4, and 5.2 (response format verification) are covered by the main operation properties
3. Properties 4.6 and 2.6 (email validation) test the same validation logic and can be combined
4. Multiple "not found" edge cases (3.3, 4.5, 5.3) can be consolidated into generator coverage

**Consolidation Strategy**:
- Combine response format verification into the main operation properties
- Create a single comprehensive email validation property
- Ensure edge case generators cover all "not found" scenarios
- Combine timestamp properties (2.3, 4.2, 4.3) into comprehensive timestamp management properties

### Property 1: JWT Token Validation

*For any* JWT token (valid or invalid), the Lambda Authorizer SHALL correctly validate the token signature against Cognito public keys and return the appropriate authorization decision (Allow for valid tokens, Deny for invalid/expired tokens).

**Validates: Requirements 1.1, 1.4, 1.5**

### Property 2: Customer Creation with Valid Data

*For any* valid customer data (containing required fields name and email, with valid email format, and any combination of optional fields), creating a customer SHALL result in a new customer record in the data store with a unique customer_id, proper timestamps, and all provided fields preserved.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.7**

### Property 3: Email Validation

*For any* string that does not match valid email format, attempting to create or update a customer with that email SHALL be rejected with HTTP 400 and error message "Invalid email format".

**Validates: Requirements 2.6, 4.6**

### Property 4: Customer ID Uniqueness

*For any* set of customer creation operations, all generated customer_ids SHALL be unique (no duplicates).

**Validates: Requirements 2.2**

### Property 5: Customer Retrieval by ID

*For any* customer that has been created, retrieving that customer by its customer_id SHALL return HTTP 200 with the complete customer record matching all fields from creation.

**Validates: Requirements 3.1, 3.2**

### Property 6: List All Customers

*For any* set of created customers, listing all customers SHALL return HTTP 200 with an array containing all created customer records.

**Validates: Requirements 3.4, 3.5**

### Property 7: Customer Update Persistence

*For any* existing customer and any valid update data, updating the customer SHALL persist all changes to the data store and return HTTP 200 with the updated customer record reflecting all changes.

**Validates: Requirements 4.1, 4.4**

### Property 8: Timestamp Management on Update

*For any* customer update operation, the updated_at timestamp SHALL change to a new current UTC time, while the created_at timestamp SHALL remain unchanged from the original value.

**Validates: Requirements 4.2, 4.3**

### Property 9: Partial Update Support

*For any* existing customer and any subset of updateable fields, updating only those fields SHALL change only the specified fields while preserving all other fields unchanged.

**Validates: Requirements 4.7**

### Property 10: Customer Deletion

*For any* existing customer, deleting that customer SHALL remove it from the data store such that subsequent retrieval attempts return HTTP 404.

**Validates: Requirements 5.1, 5.2**

### Property 11: Data Persistence Round-Trip

*For any* customer record with all fields populated, creating the customer and then retrieving it SHALL return a customer record with all fields matching the original input (round-trip property).

**Validates: Requirements 6.3**

### Property 12: Error Response Format

*For any* error condition (validation error, not found error, or server error), the error response SHALL be valid JSON containing the fields: error, message, and timestamp.

**Validates: Requirements 7.1**

### Property 13: Authentication Error Messages

*For any* authentication failure (missing token, invalid token, expired token), the Lambda Authorizer SHALL return an error message that specifically identifies the type of authentication failure.

**Validates: Requirements 7.5**

## Performance Considerations

### Lambda Configuration

**Authorizer Lambda**:
- Memory: 256 MB (sufficient for JWT validation)
- Timeout: 5 seconds
- Cold start: ~500ms
- Warm execution: ~50ms

**CRUD Lambda**:
- Memory: 512 MB (sufficient for DynamoDB operations)
- Timeout: 10 seconds
- Cold start: ~800ms
- Warm execution: ~100-200ms

### DynamoDB Performance

- **Read Capacity**: On-demand (auto-scaling)
- **Write Capacity**: On-demand (auto-scaling)
- **Latency**: Single-digit milliseconds for GetItem/PutItem
- **Scan Performance**: O(n) - acceptable for MVP with small dataset

### API Gateway Limits

- **Throttle Limit**: 10,000 requests per second (default)
- **Burst Limit**: 5,000 requests (default)
- **Payload Size**: 10 MB maximum

### Optimization Opportunities (Post-MVP)

1. **Caching**: Add API Gateway caching for GET operations
2. **Connection Pooling**: Reuse DynamoDB connections across Lambda invocations
3. **Pagination**: Implement pagination for list operations
4. **Indexes**: Add GSI for email-based lookups
5. **Authorizer Caching**: Enable authorizer result caching (TTL: 300s)

## Monitoring and Observability

### CloudWatch Metrics

**Lambda Metrics**:
- Invocations
- Duration
- Errors
- Throttles
- Concurrent Executions

**DynamoDB Metrics**:
- ConsumedReadCapacityUnits
- ConsumedWriteCapacityUnits
- UserErrors
- SystemErrors

**API Gateway Metrics**:
- Count (request count)
- 4XXError
- 5XXError
- Latency
- IntegrationLatency

### CloudWatch Logs

All Lambda functions log to CloudWatch Logs:
- Request/response details
- Error stack traces
- Execution duration
- Custom application logs

### Alarms (Post-MVP)

Recommended CloudWatch Alarms:
- Lambda error rate > 5%
- API Gateway 5XX error rate > 1%
- Lambda duration > 5 seconds
- DynamoDB throttling events

## Future Enhancements (Out of Scope for MVP)

1. **Advanced Search**: Add additional GSIs for company/name lookups
2. **Audit Logging**: Track all changes with user identity and timestamp
3. **Multi-Tenancy**: Add tenant_id to support multiple organizations
4. **Pagination**: Implement cursor-based pagination for list operations
5. **Filtering**: Add query parameters for filtering customer lists
6. **Soft Delete**: Mark customers as deleted instead of removing
7. **Data Validation**: Enhanced validation rules (phone format, address structure)
8. **Rate Limiting**: Per-user rate limiting
9. **Caching**: Redis/ElastiCache for frequently accessed customers
10. **Batch Operations**: Bulk create/update/delete endpoints

