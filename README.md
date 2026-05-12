# Customer Management MVP


> **Important**: This documentation uses placeholder values like `[YOUR_USERNAME]`, `[YOUR_EMAIL]`, `<user-pool-id>`, etc. For actual credential values and setup instructions, see [SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md).

A serverless customer management API built on AWS, providing secure CRUD operations for customer data through REST API endpoints.

## Overview

The Customer Management MVP is a serverless platform that centralizes customer data management for AnyCompany. The system provides secure CRUD operations through REST API endpoints, enabling customer service representatives, sales team members, and internal applications to access and manage customer information efficiently.

### Business Problem

- Customer data is fragmented across multiple systems
- No single source of truth for customer information
- Manual processes lead to data inconsistencies
- Support teams cannot quickly access customer records

### Solution

This system provides:
- Centralized customer data storage in DynamoDB
- Secure access for authorized users via JWT authentication
- RESTful endpoints for integration with other systems
- Scalable serverless architecture that grows with the business

## Architecture

The system follows a serverless three-tier architecture pattern on AWS:

- **API Layer**: Amazon API Gateway with Lambda Authorizer for authentication
- **Business Logic**: AWS Lambda functions (Python 3.11) for authorization and CRUD operations
- **Data Layer**: Amazon DynamoDB for persistent, scalable NoSQL storage
- **Authentication**: AWS Cognito User Pool for JWT token management

### Architecture Diagram

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

## Project Structure

```
.
├── src/
│   ├── authorizer/          # Lambda Authorizer for JWT validation
│   │   ├── lambda_function.py
│   │   └── requirements.txt
│   └── customers/           # Customer CRUD Lambda function
│       ├── lambda_function.py
│       └── requirements.txt
├── tests/
│   ├── unit/               # Unit tests
│   │   └── events/         # Test event files
│   └── integration/        # Integration tests
├── infra/                  # Terraform infrastructure as code
│   ├── main.tf            # Main resource definitions
│   ├── variables.tf       # Input variables
│   ├── outputs.tf         # Output values
│   ├── providers.tf       # AWS provider configuration
│   ├── versions.tf        # Terraform version constraints
│   ├── terraform.tfvars   # Default variable values
│   └── envs/
│       ├── dev.tfvars     # Development environment
│       └── prod.tfvars    # Production environment
└── README.md
```

## Prerequisites

Before deploying the Customer Management MVP, ensure you have the following installed and configured:

### Required Software

- **AWS CLI** (v2.x or later)
  - Install: https://aws.amazon.com/cli/
  - Configure with credentials: `aws configure`
  - Verify: `aws --version`

- **Terraform** (v1.0 or later)
  - Install: https://www.terraform.io/downloads
  - Verify: `terraform --version`

- **Python 3.11**
  - Install: https://www.python.org/downloads/
  - Verify: `python3 --version`

- **pip** (Python package manager)
  - Usually included with Python
  - Verify: `pip3 --version`

### AWS Account Setup

1. **AWS Account**: Active AWS account with appropriate permissions
2. **IAM Permissions**: User/role must have permissions to create:
   - Lambda functions
   - API Gateway REST APIs
   - DynamoDB tables
   - IAM roles and policies
   - CloudWatch Log Groups
   - Cognito User Pools

3. **AWS Credentials**: Configure AWS CLI with access key and secret:
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)
```

### Verify Prerequisites

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check Terraform
terraform version

# Check Python
python3 --version

# Check pip
pip3 --version
```

## Infrastructure Deployment

### Overview

The deployment process consists of three main steps:
1. Build Lambda deployment packages with dependencies
2. Initialize and configure Terraform
3. Deploy infrastructure to AWS

### 1. Build Lambda Packages

Lambda functions require their dependencies to be packaged in zip files. Use the provided build scripts to create deployment packages for both Lambda functions.

#### Quick Start - Automated Build

**Python Script (Recommended - Cross-platform):**
```bash
python build_lambdas.py
```

**Bash Script (Linux/macOS):**
```bash
chmod +x build_lambdas.sh
./build_lambdas.sh
```

**Batch Script (Windows):**
```cmd
build_lambdas.bat
```

All scripts will:
1. Install dependencies from `requirements.txt` files
2. Package Lambda code with dependencies
3. Create `authorizer.zip` and `crud.zip` in the `infra/` directory

**Output:**
```
infra/
├── authorizer.zip  (~22 MB)
└── crud.zip        (~16 MB)
```

For detailed build instructions, troubleshooting, and manual build steps, see [BUILD.md](BUILD.md).

### 2. Initialize Terraform

```bash
# Navigate to infrastructure directory
cd infra

# Initialize Terraform (downloads providers)
terraform init

# Verify initialization
terraform version
```

### 3. Deploy Infrastructure

#### Development Environment

```bash
# Review planned changes
terraform plan -var-file="envs/dev.tfvars"

# Apply changes (creates infrastructure)
terraform apply -var-file="envs/dev.tfvars"

# Type 'yes' when prompted to confirm
```

#### Production Environment

```bash
# Review planned changes
terraform plan -var-file="envs/prod.tfvars"

# Apply changes
terraform apply -var-file="envs/prod.tfvars"

# Type 'yes' when prompted to confirm
```

#### Auto-Approve (CI/CD)

For automated deployments, use the `-auto-approve` flag:

```bash
terraform apply -var-file="envs/dev.tfvars" -auto-approve
```

### 4. Capture Outputs

After successful deployment, Terraform outputs important values:

```bash
# View all outputs
terraform output

# View specific output
terraform output api_endpoint
terraform output user_pool_id
terraform output dynamodb_table_name
```

**Example Output:**
```
api_endpoint = "https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod"
user_pool_id = "us-east-1_ABC123XYZ"
dynamodb_table_name = "customers"
```

### 5. Post-Deployment Setup

#### Create Test User in Cognito

```bash
# Set variables from Terraform outputs
export USER_POOL_ID=$(terraform output -raw user_pool_id)

# Create test user
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username [YOUR_USERNAME] \
  --user-attributes Name=email,Value=[YOUR_EMAIL] \
  --temporary-password [YOUR_TEMP_PASSWORD]

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username [YOUR_USERNAME] \
  --password [YOUR_SECURE_PASSWORD] \
  --permanent
```

#### Get JWT Token for Testing

```bash
# First, create an app client (if not already created by Terraform)
export APP_CLIENT_ID=$(aws cognito-idp list-user-pool-clients \
  --user-pool-id $USER_POOL_ID \
  --query 'UserPoolClients[0].ClientId' \
  --output text)

# Authenticate and get token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $APP_CLIENT_ID \
  --auth-parameters USERNAME=[YOUR_USERNAME],PASSWORD=[YOUR_SECURE_PASSWORD] \
  --query 'AuthenticationResult.IdToken' \
  --output text
```

### Updating Infrastructure

When you make changes to Terraform configuration or Lambda code:

```bash
# Rebuild Lambda packages (if code changed)
python build_lambdas.py

# Navigate to infra directory
cd infra

# Review changes
terraform plan -var-file="envs/dev.tfvars"

# Apply updates
terraform apply -var-file="envs/dev.tfvars"
```

### Destroying Infrastructure

To remove all resources (use with caution):

```bash
# Review what will be destroyed
terraform plan -destroy -var-file="envs/dev.tfvars"

# Destroy all resources
terraform destroy -var-file="envs/dev.tfvars"

# Type 'yes' when prompted to confirm
```

**Warning**: This will permanently delete all data in DynamoDB and remove all infrastructure.

## API Endpoints

All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Endpoint Reference

| Method | Path | Description | Status Codes |
|--------|------|-------------|--------------|
| POST | /customers | Create a new customer | 201, 400, 409 |
| GET | /customers | List all customers | 200 |
| GET | /customers/{customer_id} | Get customer by ID | 200, 404 |
| PUT | /customers/{customer_id} | Update customer | 200, 400, 404, 409 |
| DELETE | /customers/{customer_id} | Delete customer | 200, 404 |

### Customer Data Model

```json
{
  "customer_id": "uuid-string",
  "name": "string (required)",
  "email": "string (required)",
  "phone": "string (optional)",
  "address": "string (optional)",
  "company": "string (optional)",
  "notes": "string (optional)",
  "created_at": "ISO-8601 timestamp",
  "updated_at": "ISO-8601 timestamp"
}
```

**Field Descriptions:**

- `customer_id`: Unique identifier (UUID v4), auto-generated on creation
- `name`: Customer full name (required)
- `email`: Customer email address (required, must be unique, validated format)
- `phone`: Contact phone number (optional)
- `address`: Physical or mailing address (optional)
- `company`: Company or organization name (optional)
- `notes`: Additional notes or comments (optional)
- `created_at`: Timestamp when customer was created (ISO 8601 format, UTC)
- `updated_at`: Timestamp when customer was last updated (ISO 8601 format, UTC)

### DynamoDB Schema

**Table Name:** `customers`

**Primary Key:**
- Partition Key: `customer_id` (String)

**Billing Mode:** PAY_PER_REQUEST (on-demand)

**Global Secondary Indexes:**
- **email-index**
  - Partition Key: `email` (String)
  - Projection Type: ALL
  - Purpose: Enable efficient email uniqueness checks and email-based lookups

**Attributes:**
All customer fields are stored as DynamoDB attributes with appropriate types (String for all fields in this MVP).

**Access Patterns:**
1. Get customer by ID → GetItem on `customer_id`
2. List all customers → Scan operation
3. Create customer → PutItem with new `customer_id`
4. Update customer → UpdateItem on `customer_id`
5. Delete customer → DeleteItem on `customer_id`
6. Check email uniqueness → Query on `email-index` GSI

### API Usage Examples

#### Create Customer

**Request:**
```bash
curl -X POST https://api-endpoint/customers \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0123",
    "company": "Acme Corp",
    "address": "123 Main St, Anytown, USA",
    "notes": "VIP customer"
  }'
```

**Response (201 Created):**
```json
{
  "customer_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "company": "Acme Corp",
  "address": "123 Main St, Anytown, USA",
  "notes": "VIP customer",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### List All Customers

**Request:**
```bash
curl -X GET https://api-endpoint/customers \
  -H "Authorization: Bearer <jwt_token>"
```

**Response (200 OK):**
```json
{
  "customers": [
    {
      "customer_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1-555-0123",
      "company": "Acme Corp",
      "address": "123 Main St, Anytown, USA",
      "notes": "VIP customer",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### Get Customer by ID

**Request:**
```bash
curl -X GET https://api-endpoint/customers/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer <jwt_token>"
```

**Response (200 OK):**
```json
{
  "customer_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "company": "Acme Corp",
  "address": "123 Main St, Anytown, USA",
  "notes": "VIP customer",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Update Customer

**Request:**
```bash
curl -X PUT https://api-endpoint/customers/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+1-555-9999",
    "notes": "Updated contact information"
  }'
```

**Response (200 OK):**
```json
{
  "customer_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-9999",
  "company": "Acme Corp",
  "address": "123 Main St, Anytown, USA",
  "notes": "Updated contact information",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T14:20:00Z"
}
```

#### Delete Customer

**Request:**
```bash
curl -X DELETE https://api-endpoint/customers/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Authorization: Bearer <jwt_token>"
```

**Response (200 OK):**
```json
{
  "message": "Customer deleted successfully"
}
```

### Error Responses

All errors follow a consistent JSON structure:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error description",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Common Error Codes:**

- **400 Bad Request**: Missing required fields, invalid email format, malformed JSON
- **401 Unauthorized**: Missing authentication token
- **403 Forbidden**: Invalid or expired token
- **404 Not Found**: Customer ID does not exist
- **409 Conflict**: Email already exists (must be unique)
- **500 Internal Server Error**: Database operation failed or unexpected error

**Example Error Response:**
```json
{
  "error": "ValidationError",
  "message": "Invalid email format",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Testing

The project includes comprehensive unit tests for all Lambda functions and validation logic.

### Running Tests

**Important:** Tests require the project root to be in PYTHONPATH to import from the `src` directory.

**Linux/macOS:**
```bash
# Run all unit tests
PYTHONPATH=. pytest tests/unit/ -v

# Run specific test file
PYTHONPATH=. pytest tests/unit/test_create_customer.py -v

# Run tests with coverage report
PYTHONPATH=. pytest tests/unit/ --cov=src --cov-report=html

# Run all tests (unit + integration)
PYTHONPATH=. pytest tests/ -v
```

**Windows (PowerShell):**
```powershell
# Run all unit tests
$env:PYTHONPATH = "$PWD"; pytest tests/unit/ -v

# Run specific test file
$env:PYTHONPATH = "$PWD"; pytest tests/unit/test_create_customer.py -v

# Run tests with coverage report
$env:PYTHONPATH = "$PWD"; pytest tests/unit/ --cov=src --cov-report=html

# Run all tests (unit + integration)
$env:PYTHONPATH = "$PWD"; pytest tests/ -v
```

**Windows (Command Prompt):**
```cmd
# Set PYTHONPATH first
set PYTHONPATH=%CD%

# Then run tests
pytest tests/unit/ -v
```

### Test Structure

```
tests/
├── unit/
│   ├── test_authorizer_logging.py      # Authorizer logging tests
│   ├── test_create_customer.py         # Create operation tests
│   ├── test_crud_logging.py            # CRUD logging tests
│   ├── test_customer_model.py          # Data model tests
│   ├── test_delete_customer.py         # Delete operation tests
│   ├── test_error_handling.py          # Error handling tests
│   ├── test_get_customer.py            # Get operation tests
│   ├── test_lambda_handler_routing.py  # Handler routing tests
│   ├── test_list_customers.py          # List operation tests
│   ├── test_update_customer.py         # Update operation tests
│   └── test_validation.py              # Validation logic tests
└── integration/
    └── (integration tests)
```

### Test Coverage

The test suite covers:
- ✓ Customer creation with valid and invalid data
- ✓ Customer retrieval (single and list)
- ✓ Customer updates (full and partial)
- ✓ Customer deletion
- ✓ Email validation and uniqueness checks
- ✓ Error handling for all error types
- ✓ Lambda handler routing logic
- ✓ Structured logging for all operations
- ✓ Authorization token validation

### Manual Testing with curl

After deployment, you can test the API manually:

1. **Get JWT Token from Cognito:**
```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <app-client-id> \
  --auth-parameters USERNAME=testuser,PASSWORD=<password>
```

2. **Test Create Customer:**
```bash
export JWT_TOKEN="<token-from-step-1>"
export API_ENDPOINT="<api-endpoint-from-terraform-output>"

curl -X POST $API_ENDPOINT/customers \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com"}'
```

3. **Test List Customers:**
```bash
curl -X GET $API_ENDPOINT/customers \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Common Commands

### Terraform Operations

```bash
# Initialize Terraform (first time setup)
cd infra
terraform init

# Validate configuration
terraform validate

# Format Terraform files
terraform fmt

# Plan changes (preview)
terraform plan -var-file="envs/dev.tfvars"

# Apply changes (deploy)
terraform apply -var-file="envs/dev.tfvars"

# Show current state
terraform show

# List all resources
terraform state list

# View outputs
terraform output

# Destroy infrastructure
terraform destroy -var-file="envs/dev.tfvars"
```

### AWS CLI Operations

#### Cognito User Management

```bash
# Create a test user
aws cognito-idp admin-create-user \
  --user-pool-id <user-pool-id> \
  --username [YOUR_USERNAME] \
  --user-attributes Name=email,Value=[YOUR_EMAIL] \
  --temporary-password [YOUR_TEMP_PASSWORD]

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id <user-pool-id> \
  --username [YOUR_USERNAME] \
  --password [YOUR_SECURE_PASSWORD] \
  --permanent

# List users
aws cognito-idp list-users \
  --user-pool-id <user-pool-id>

# Delete user
aws cognito-idp admin-delete-user \
  --user-pool-id <user-pool-id> \
  --username [YOUR_USERNAME]

# Get JWT token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <app-client-id> \
  --auth-parameters USERNAME=[YOUR_USERNAME],PASSWORD=[YOUR_SECURE_PASSWORD]
```

#### Lambda Operations

```bash
# Invoke Lambda function directly (for testing)
aws lambda invoke \
  --function-name customer-management-crud \
  --payload file://test-event.json \
  response.json

# View Lambda configuration
aws lambda get-function \
  --function-name customer-management-crud

# Update Lambda function code
aws lambda update-function-code \
  --function-name customer-management-crud \
  --zip-file fileb://infra/crud.zip

# View Lambda logs (last 10 minutes)
aws logs tail /aws/lambda/customer-management-crud --since 10m
```

#### DynamoDB Operations

```bash
# Scan table (list all customers)
aws dynamodb scan \
  --table-name customers

# Get item by ID
aws dynamodb get-item \
  --table-name customers \
  --key '{"customer_id": {"S": "abc-123"}}'

# Query by email (using GSI)
aws dynamodb query \
  --table-name customers \
  --index-name email-index \
  --key-condition-expression "email = :email" \
  --expression-attribute-values '{":email": {"S": "test@example.com"}}'

# Delete item
aws dynamodb delete-item \
  --table-name customers \
  --key '{"customer_id": {"S": "abc-123"}}'
```

#### CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/customer-management-crud --follow

# Filter logs by pattern
aws logs filter-log-events \
  --log-group-name /aws/lambda/customer-management-crud \
  --filter-pattern "ERROR"

# Get logs from specific time range
aws logs filter-log-events \
  --log-group-name /aws/lambda/customer-management-crud \
  --start-time $(date -d '1 hour ago' +%s)000
```

#### API Gateway Operations

```bash
# Get API details
aws apigateway get-rest-apis

# Get API resources
aws apigateway get-resources \
  --rest-api-id <api-id>

# Test invoke API
aws apigateway test-invoke-method \
  --rest-api-id <api-id> \
  --resource-id <resource-id> \
  --http-method GET
```

## Configuration

### Environment Variables

Lambda functions use the following environment variables:

**Authorizer Lambda:**
- `USER_POOL_ID`: Cognito User Pool ID
- `REGION`: AWS region

**Customer CRUD Lambda:**
- `TABLE_NAME`: DynamoDB table name
- `REGION`: AWS region

### Terraform Variables

Key variables in `variables.tf`:
- `aws_region`: AWS region (default: us-east-1)
- `environment`: Environment name (dev/prod)
- `lambda_runtime`: Python runtime version (default: python3.11)
- `log_retention_days`: CloudWatch Logs retention (default: 7 days)

## Monitoring

### CloudWatch Logs

Lambda functions log to CloudWatch Log Groups with structured JSON logging:
- `/aws/lambda/customer-management-authorizer` - Authentication attempts and token validation
- `/aws/lambda/customer-management-crud` - CRUD operations, errors, and user actions

**Log Retention:** 7 days (configurable in Terraform)

**Viewing Logs:**
```bash
# View Authorizer logs
aws logs tail /aws/lambda/customer-management-authorizer --follow

# View CRUD Lambda logs
aws logs tail /aws/lambda/customer-management-crud --follow

# Filter logs by error
aws logs filter-log-events \
  --log-group-name /aws/lambda/customer-management-crud \
  --filter-pattern "ERROR"
```

### CloudWatch Metrics

Monitor the following metrics in CloudWatch:

**Lambda Metrics:**
- Invocations - Number of function invocations
- Errors - Number of failed invocations
- Duration - Execution time
- Throttles - Number of throttled invocations
- ConcurrentExecutions - Number of concurrent executions

**API Gateway Metrics:**
- Count - Total API requests
- 4XXError - Client errors
- 5XXError - Server errors
- Latency - End-to-end latency
- IntegrationLatency - Backend latency

**DynamoDB Metrics:**
- ConsumedReadCapacityUnits - Read capacity consumed
- ConsumedWriteCapacityUnits - Write capacity consumed
- UserErrors - Client-side errors
- SystemErrors - Server-side errors

### Troubleshooting

#### Authentication Issues

**Problem:** Getting 401 Unauthorized errors

**Solutions:**
1. Verify JWT token is included in Authorization header
2. Check token format: `Bearer <token>`
3. Verify token is not expired (1 hour default expiration)
4. Check CloudWatch logs for authorizer errors

**Problem:** Getting 403 Forbidden errors

**Solutions:**
1. Verify token signature is valid
2. Check token was issued by correct Cognito User Pool
3. Verify Cognito User Pool ID in authorizer environment variables
4. Review authorizer CloudWatch logs for specific error

#### CRUD Operation Issues

**Problem:** 400 Bad Request - Missing required fields

**Solutions:**
1. Verify request includes `name` and `email` fields
2. Check JSON format is valid
3. Ensure Content-Type header is `application/json`

**Problem:** 409 Conflict - Email already exists

**Solutions:**
1. Email must be unique across all customers
2. Check if customer with that email already exists
3. Use different email or update existing customer

**Problem:** 404 Not Found - Customer not found

**Solutions:**
1. Verify customer_id is correct
2. Check customer exists using list endpoint
3. Ensure customer wasn't deleted

**Problem:** 500 Internal Server Error

**Solutions:**
1. Check CloudWatch logs for detailed error
2. Verify DynamoDB table exists and is accessible
3. Check Lambda IAM permissions for DynamoDB access
4. Verify Lambda environment variables are set correctly

#### Deployment Issues

**Problem:** Terraform apply fails

**Solutions:**
1. Run `terraform init` to initialize providers
2. Verify AWS credentials are configured
3. Check AWS region is set correctly (us-east-1)
4. Review Terraform error messages for specific issues

**Problem:** Lambda function not found

**Solutions:**
1. Verify Lambda zip files exist in infra/ directory
2. Rebuild Lambda packages with dependencies
3. Check Terraform successfully created Lambda functions
4. Verify function names match expected values

**Problem:** API Gateway returns 502 Bad Gateway

**Solutions:**
1. Check Lambda function logs for errors
2. Verify Lambda function has correct handler configured
3. Check Lambda execution role has necessary permissions
4. Verify Lambda function is not timing out

## Security

### Authentication & Authorization

- **JWT Tokens**: All API endpoints require valid JWT token from Cognito User Pool
- **Token Validation**: Lambda Authorizer validates token signature, expiration, and issuer
- **HTTPS Only**: All API communication encrypted in transit via HTTPS (enforced by API Gateway)

### Data Protection

- **At Rest**: DynamoDB encryption at rest using AWS managed keys
- **In Transit**: TLS 1.2+ for all API Gateway and AWS service communication
- **Access Control**: IAM roles with least privilege permissions for Lambda functions

### IAM Permissions

**Lambda Authorizer Role:**
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

**Customer CRUD Lambda Role:**
- `dynamodb:PutItem` - Create customers
- `dynamodb:GetItem` - Read customer by ID
- `dynamodb:Scan` - List all customers
- `dynamodb:UpdateItem` - Update customers
- `dynamodb:DeleteItem` - Delete customers
- `dynamodb:Query` - Email uniqueness checks via GSI
- `logs:CreateLogGroup`
- `logs:CreateLogStream`
- `logs:PutLogEvents`

### Best Practices

1. **Rotate Credentials**: Regularly rotate AWS access keys and Cognito user passwords
2. **Monitor Logs**: Review CloudWatch logs for suspicious authentication attempts
3. **Limit Token TTL**: Keep JWT token expiration short (default: 1 hour)
4. **Use Environment Variables**: Never hardcode credentials in code
5. **Enable MFA**: Consider enabling MFA for Cognito users in production

## Performance

### Lambda Configuration

**Authorizer Lambda:**
- Memory: 256 MB
- Timeout: 5 seconds
- Cold start: ~500ms
- Warm execution: ~50ms

**Customer CRUD Lambda:**
- Memory: 512 MB
- Timeout: 10 seconds
- Cold start: ~800ms
- Warm execution: ~100-200ms

### DynamoDB Configuration

- **Billing Mode**: PAY_PER_REQUEST (on-demand auto-scaling)
- **Latency**: Single-digit milliseconds for GetItem/PutItem operations
- **Global Secondary Index**: email-index for efficient email uniqueness checks

### API Gateway Limits

- **Throttle Limit**: 10,000 requests per second (AWS default)
- **Burst Limit**: 5,000 requests (AWS default)
- **Payload Size**: 10 MB maximum
- **Timeout**: 29 seconds maximum

### Optimization Tips

1. **Keep Lambda Warm**: Use CloudWatch Events to ping Lambda functions periodically
2. **Enable Authorizer Caching**: Cache authorizer results for 300 seconds (5 minutes)
3. **Use Connection Pooling**: Reuse DynamoDB connections across Lambda invocations
4. **Monitor Cold Starts**: Track cold start metrics and optimize package size if needed

## Future Enhancements

Potential improvements beyond the MVP scope:

1. **Pagination**: Implement cursor-based pagination for list operations
2. **Advanced Search**: Add GSIs for company/name lookups and filtering
3. **Audit Logging**: Track all changes with user identity and timestamp
4. **Soft Delete**: Mark customers as deleted instead of removing records
5. **Rate Limiting**: Implement per-user rate limiting
6. **Caching**: Add API Gateway caching for GET operations
7. **Batch Operations**: Bulk create/update/delete endpoints
8. **Data Validation**: Enhanced validation (phone format, address structure)
9. **Multi-Tenancy**: Add tenant_id to support multiple organizations
10. **CloudWatch Alarms**: Automated alerts for errors and performance issues

## License

Copyright (c) 2024 AnyCompany. All rights reserved.
#   H a c k a t h o n G e n I A - E x t e n d e d - K i r o 
 
 