# Implementation Plan: Customer Management MVP

## Overview

This implementation plan breaks down the Customer Management MVP into discrete coding tasks. The system uses a serverless architecture on AWS with Python Lambda functions, DynamoDB for storage, API Gateway for REST endpoints, and Cognito for authentication. The implementation follows an incremental approach: infrastructure setup → core data models → Lambda functions → integration → testing.

## Tasks

- [x] 1. Set up project structure and infrastructure foundation
  - Create directory structure following AWS best practices (src/authorizer, src/customers, infra/, tests/)
  - Define Terraform configuration files (main.tf, variables.tf, outputs.tf, providers.tf, versions.tf)
  - Configure AWS provider for us-east-1 region
  - Set up Python 3.11 runtime configuration
  - _Requirements: 9.1, 9.2, 9.3_

- [x] 2. Implement DynamoDB table infrastructure
  - [x] 2.1 Create DynamoDB table resource in Terraform
    - Define customers table with customer_id as partition key
    - Configure PAY_PER_REQUEST billing mode
    - Add email attribute for GSI
    - Create email-index Global Secondary Index with ALL projection
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6_
  
  - [x] 2.2 Add Terraform outputs for table name and ARN
    - Output dynamodb_table_name for Lambda environment variables
    - _Requirements: 9.5_

- [x] 3. Implement Cognito User Pool infrastructure
  - [x] 3.1 Create Cognito User Pool resource in Terraform
    - Configure user pool with name "customer-management-users"
    - Set sign-in options to username or email
    - Configure default password policy
    - Set token expiration to 1 hour
    - _Requirements: 9.3_
  
  - [x] 3.2 Add Terraform outputs for Cognito User Pool ID and ARN
    - Output user_pool_id for reference
    - Output user_pool_arn for Lambda Authorizer configuration
    - _Requirements: 9.5_

- [x] 4. Implement Lambda Authorizer
  - [x] 4.1 Create Lambda Authorizer function code
    - Implement lambda_handler function accepting API Gateway authorizer event
    - Implement extract_token function to parse Bearer token from Authorization header
    - Implement verify_token_signature function using python-jose and Cognito JWKS
    - Implement validate_token_expiration function checking exp claim
    - Implement extract_user_identity function extracting sub, username, email claims
    - Implement generate_policy function creating IAM policy document
    - Add error handling for missing token (return Deny with 401 context)
    - Add error handling for invalid/expired token (return Deny with 403 context)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.5_
  
  - [ ]* 4.2 Write property test for Lambda Authorizer
    - **Property 1: JWT Token Validation**
    - **Validates: Requirements 1.1, 1.4, 1.5**
    - Generate random valid and invalid JWT tokens
    - Verify correct authorization decision (Allow/Deny) for each token type
  
  - [ ]* 4.3 Write unit tests for Lambda Authorizer
    - Test valid token extraction and validation
    - Test missing token returns 401 error
    - Test invalid token format returns 403 error
    - Test expired token returns 403 error
    - Test malformed token returns 403 error
    - _Requirements: 1.2, 1.3, 7.5_
  
  - [x] 4.4 Create requirements.txt for Authorizer Lambda
    - Add boto3 for AWS SDK
    - Add python-jose[cryptography] for JWT handling
    - _Requirements: 9.3_
  
  - [x] 4.5 Create IAM role and policy for Lambda Authorizer
    - Define IAM role with Lambda service principal
    - Attach CloudWatch Logs permissions (CreateLogGroup, CreateLogStream, PutLogEvents)
    - _Requirements: 9.4, 10.7_
  
  - [x] 4.6 Create Lambda Authorizer resource in Terraform
    - Define Lambda function with Python 3.11 runtime
    - Set function name to "customer-management-authorizer"
    - Configure handler as lambda_function.lambda_handler
    - Attach IAM role from 4.5
    - Set memory to 256 MB and timeout to 5 seconds
    - Add environment variable for Cognito User Pool ID
    - _Requirements: 9.3_
  
  - [x] 4.7 Create CloudWatch Log Group for Lambda Authorizer
    - Define log group /aws/lambda/customer-management-authorizer
    - Set retention period to 7 days
    - _Requirements: 10.3, 10.6_
  
  - [x] 4.8 Implement structured logging in Lambda Authorizer
    - Log all authentication attempts with timestamp, validation result, user identity
    - Log error details for invalid tokens
    - Use JSON format for structured logging
    - _Requirements: 10.1, 10.5_

- [x] 5. Checkpoint - Verify infrastructure and authorizer
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement Customer data models and validation
  - [x] 6.1 Create Customer data model class
    - Define Customer dataclass with all fields (customer_id, name, email, phone, address, company, notes, created_at, updated_at)
    - Implement to_dict method for DynamoDB serialization
    - Implement from_dict classmethod for DynamoDB deserialization
    - _Requirements: 6.3_
  
  - [ ]* 6.2 Write property test for data model round-trip
    - **Property 11: Data Persistence Round-Trip**
    - **Validates: Requirements 6.3**
    - Generate random customer records with all fields
    - Verify to_dict → from_dict preserves all data
  
  - [x] 6.3 Create validation utility functions
    - Implement validate_email function using regex pattern
    - Implement validate_required_fields function checking name and email presence
    - Implement check_email_uniqueness function querying email-index GSI
    - _Requirements: 2.5, 2.6, 2.7, 4.6, 4.7_
  
  - [ ]* 6.4 Write property test for email validation
    - **Property 3: Email Validation**
    - **Validates: Requirements 2.6, 4.6**
    - Generate random invalid email strings
    - Verify all invalid emails are rejected with HTTP 400
  
  - [ ]* 6.5 Write unit tests for validation functions
    - Test valid email formats pass validation
    - Test invalid email formats fail validation
    - Test missing required fields are detected
    - Test email uniqueness check with GSI query
    - _Requirements: 2.5, 2.6_

- [x] 7. Implement Customer CRUD Lambda - Create operation
  - [x] 7.1 Implement create_customer function
    - Validate required fields (name, email) are present
    - Validate email format using validate_email
    - Check email uniqueness using check_email_uniqueness
    - Generate unique customer_id using UUID
    - Set created_at and updated_at to current UTC timestamp
    - Store customer record in DynamoDB using PutItem
    - Return HTTP 201 with complete customer record
    - Handle validation errors returning HTTP 400
    - Handle duplicate email returning HTTP 409
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_
  
  - [ ]* 7.2 Write property test for customer creation
    - **Property 2: Customer Creation with Valid Data**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.7**
    - Generate random valid customer data with various field combinations
    - Verify customer record created with unique ID and proper timestamps
  
  - [ ]* 7.3 Write property test for customer ID uniqueness
    - **Property 4: Customer ID Uniqueness**
    - **Validates: Requirements 2.2**
    - Generate multiple customer creation operations
    - Verify all customer_ids are unique
  
  - [ ]* 7.4 Write unit tests for create operation
    - Test successful customer creation with all fields
    - Test successful creation with only required fields
    - Test missing name returns HTTP 400
    - Test missing email returns HTTP 400
    - Test invalid email format returns HTTP 400
    - Test duplicate email returns HTTP 409
    - _Requirements: 2.5, 2.6, 2.7_

- [x] 8. Implement Customer CRUD Lambda - Read operations
  - [x] 8.1 Implement get_customer function
    - Accept customer_id parameter
    - Retrieve customer from DynamoDB using GetItem
    - Return HTTP 200 with customer record if found
    - Return HTTP 404 with error message if not found
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 8.2 Implement list_customers function
    - Retrieve all customers from DynamoDB using Scan
    - Return HTTP 200 with array of customer records
    - _Requirements: 3.4, 3.5_
  
  - [ ]* 8.3 Write property test for customer retrieval
    - **Property 5: Customer Retrieval by ID**
    - **Validates: Requirements 3.1, 3.2**
    - Create random customers and retrieve by ID
    - Verify retrieved record matches created record
  
  - [ ]* 8.4 Write property test for list all customers
    - **Property 6: List All Customers**
    - **Validates: Requirements 3.4, 3.5**
    - Create set of random customers
    - Verify list operation returns all created customers
  
  - [ ]* 8.5 Write unit tests for read operations
    - Test get_customer with valid ID returns HTTP 200
    - Test get_customer with non-existent ID returns HTTP 404
    - Test list_customers returns all records
    - Test list_customers returns empty array when no customers exist
    - _Requirements: 3.3_

- [x] 9. Implement Customer CRUD Lambda - Update operation
  - [x] 9.1 Implement update_customer function
    - Accept customer_id and update_data parameters
    - Verify customer exists using GetItem (return 404 if not found)
    - Validate email format if email is being updated
    - Check email uniqueness if email is being updated (exclude current customer)
    - Update updated_at timestamp to current UTC time
    - Preserve created_at timestamp from original record
    - Support partial updates (only update provided fields)
    - Update customer in DynamoDB using UpdateItem
    - Return HTTP 200 with complete updated customer record
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_
  
  - [ ]* 9.2 Write property test for update persistence
    - **Property 7: Customer Update Persistence**
    - **Validates: Requirements 4.1, 4.4**
    - Create customers and apply random valid updates
    - Verify all changes persisted correctly
  
  - [ ]* 9.3 Write property test for timestamp management
    - **Property 8: Timestamp Management on Update**
    - **Validates: Requirements 4.2, 4.3**
    - Create customers and update them
    - Verify updated_at changes and created_at remains unchanged
  
  - [ ]* 9.4 Write property test for partial updates
    - **Property 9: Partial Update Support**
    - **Validates: Requirements 4.7**
    - Generate random subsets of updateable fields
    - Verify only specified fields change, others preserved
  
  - [ ]* 9.5 Write unit tests for update operation
    - Test successful update with all fields
    - Test successful partial update
    - Test update with non-existent ID returns HTTP 404
    - Test update with invalid email returns HTTP 400
    - Test update with duplicate email returns HTTP 409
    - Test created_at timestamp preservation
    - Test updated_at timestamp changes
    - _Requirements: 4.2, 4.3, 4.5, 4.6, 4.7_

- [x] 10. Implement Customer CRUD Lambda - Delete operation
  - [x] 10.1 Implement delete_customer function
    - Accept customer_id parameter
    - Verify customer exists using GetItem (return 404 if not found)
    - Delete customer from DynamoDB using DeleteItem
    - Return HTTP 200 with success message
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ]* 10.2 Write property test for customer deletion
    - **Property 10: Customer Deletion**
    - **Validates: Requirements 5.1, 5.2**
    - Create random customers and delete them
    - Verify subsequent retrieval returns HTTP 404
  
  - [ ]* 10.3 Write unit tests for delete operation
    - Test successful deletion returns HTTP 200
    - Test delete with non-existent ID returns HTTP 404
    - Test deleted customer cannot be retrieved
    - _Requirements: 5.3_

- [x] 11. Implement Customer CRUD Lambda - Main handler and routing
  - [x] 11.1 Implement lambda_handler function
    - Parse httpMethod and path from API Gateway proxy event
    - Route POST /customers to create_customer
    - Route GET /customers to list_customers
    - Route GET /customers/{customer_id} to get_customer
    - Route PUT /customers/{customer_id} to update_customer
    - Route DELETE /customers/{customer_id} to delete_customer
    - Extract customer_id from pathParameters
    - Parse JSON body for POST/PUT requests
    - Extract user identity from requestContext.authorizer
    - Return properly formatted API Gateway proxy response
    - _Requirements: 8.1, 8.4_
  
  - [x] 11.2 Implement error handling and response formatting
    - Define CustomerManagementError base exception class
    - Define ValidationError exception (HTTP 400)
    - Define NotFoundError exception (HTTP 404)
    - Define DatabaseError exception (HTTP 500)
    - Implement handle_error function converting exceptions to API Gateway responses
    - Add CORS headers to all responses
    - Format error responses with error, message, timestamp fields
    - Handle malformed JSON returning HTTP 400
    - _Requirements: 7.1, 7.2, 7.3, 8.5_
  
  - [ ]* 11.3 Write property test for error response format
    - **Property 12: Error Response Format**
    - **Validates: Requirements 7.1**
    - Generate various error conditions
    - Verify all error responses contain error, message, timestamp fields
  
  - [ ]* 11.4 Write property test for authentication error messages
    - **Property 13: Authentication Error Messages**
    - **Validates: Requirements 7.5**
    - Generate various authentication failures
    - Verify error messages identify specific failure types
  
  - [x] 11.3 Implement structured logging for CRUD operations
    - Log all CRUD operations with timestamp, operation type, customer_id, user identity, result
    - Log errors with full stack traces
    - Use JSON format for structured logging
    - _Requirements: 7.4, 10.2, 10.5_
  
  - [x] 11.4 Create requirements.txt for Customer CRUD Lambda
    - Add boto3 for DynamoDB client
    - _Requirements: 9.3_
  
  - [x] 11.5 Create IAM role and policy for Customer CRUD Lambda
    - Define IAM role with Lambda service principal
    - Attach DynamoDB permissions (PutItem, GetItem, Scan, UpdateItem, DeleteItem, Query)
    - Attach CloudWatch Logs permissions (CreateLogGroup, CreateLogStream, PutLogEvents)
    - Scope DynamoDB permissions to customers table and email-index
    - _Requirements: 9.4, 10.7_
  
  - [x] 11.6 Create Lambda function resource in Terraform
    - Define Lambda function with Python 3.11 runtime
    - Set function name to "customer-management-crud"
    - Configure handler as lambda_function.lambda_handler
    - Attach IAM role from 11.5
    - Set memory to 512 MB and timeout to 10 seconds
    - Add environment variable TABLE_NAME pointing to DynamoDB table
    - _Requirements: 9.3_
  
  - [x] 11.7 Create CloudWatch Log Group for Customer CRUD Lambda
    - Define log group /aws/lambda/customer-management-crud
    - Set retention period to 7 days
    - _Requirements: 10.4, 10.6_

- [x] 12. Checkpoint - Verify Lambda functions
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement API Gateway infrastructure
  - [x] 13.1 Create API Gateway REST API resource
    - Define REST API with name "customer-management-api"
    - Set description "Customer Management REST API"
    - _Requirements: 9.3_
  
  - [x] 13.2 Create API Gateway Authorizer
    - Define custom authorizer using Lambda Authorizer function
    - Set authorizer type to TOKEN
    - Configure identity source as method.request.header.Authorization
    - Set authorizer result TTL to 300 seconds
    - _Requirements: 8.2, 8.3_
  
  - [x] 13.3 Create /customers resource and methods
    - Define /customers resource
    - Create POST method with Lambda proxy integration to CRUD Lambda
    - Create GET method with Lambda proxy integration to CRUD Lambda
    - Attach authorizer to both methods
    - Enable CORS for both methods
    - _Requirements: 8.1, 8.2, 8.4, 8.5_
  
  - [x] 13.4 Create /customers/{customer_id} resource and methods
    - Define /customers/{customer_id} resource with path parameter
    - Create GET method with Lambda proxy integration to CRUD Lambda
    - Create PUT method with Lambda proxy integration to CRUD Lambda
    - Create DELETE method with Lambda proxy integration to CRUD Lambda
    - Attach authorizer to all methods
    - Enable CORS for all methods
    - _Requirements: 8.1, 8.2, 8.4, 8.5_
  
  - [x] 13.5 Create API Gateway deployment and stage
    - Define deployment resource depending on all methods
    - Create "prod" stage
    - _Requirements: 9.3_
  
  - [x] 13.6 Add Terraform output for API endpoint URL
    - Output api_endpoint with invoke URL
    - _Requirements: 9.5_

- [x] 14. Create Lambda deployment packages
  - [x] 14.1 Create build script for Lambda packages
    - Write script to install dependencies and create zip files
    - Package Authorizer Lambda with dependencies
    - Package Customer CRUD Lambda with dependencies
    - Place zip files in infra/ directory for Terraform
    - _Requirements: 9.3_

- [x] 15. Create environment-specific Terraform variable files
  - [x] 15.1 Create infra/terraform.tfvars with default values
    - Define default AWS region (us-east-1)
    - Define default environment name
    - _Requirements: 9.2_
  
  - [x] 15.2 Create infra/envs/dev.tfvars
    - Configure development environment variables
    - _Requirements: 9.1_
  
  - [x] 15.3 Create infra/envs/prod.tfvars
    - Configure production environment variables
    - _Requirements: 9.1_

- [x] 16. Create project documentation
  - [x] 16.1 Create README.md
    - Document project overview and architecture
    - Document prerequisites (AWS CLI, Terraform, Python 3.11)
    - Document build process for Lambda packages
    - Document deployment process with Terraform commands
    - Document API endpoints and usage examples
    - Document testing instructions
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 17. Final checkpoint - Integration testing
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at key milestones
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples and edge cases
- The implementation follows AWS best practices for serverless architecture
- All Lambda functions use Python 3.11 runtime
- Infrastructure is fully defined in Terraform for reproducible deployments
- CloudWatch logging provides comprehensive observability

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "3.1"] },
    { "id": 2, "tasks": ["2.2", "3.2", "4.1", "4.4"] },
    { "id": 3, "tasks": ["4.2", "4.3", "4.5", "6.1"] },
    { "id": 4, "tasks": ["4.6", "4.7", "6.2", "6.3"] },
    { "id": 5, "tasks": ["4.8", "6.4", "6.5", "7.1"] },
    { "id": 6, "tasks": ["7.2", "7.3", "7.4", "8.1", "8.2"] },
    { "id": 7, "tasks": ["8.3", "8.4", "8.5", "9.1"] },
    { "id": 8, "tasks": ["9.2", "9.3", "9.4", "9.5", "10.1"] },
    { "id": 9, "tasks": ["10.2", "10.3", "11.1", "11.2"] },
    { "id": 10, "tasks": ["11.3", "11.4", "11.5", "11.3", "11.4"] },
    { "id": 11, "tasks": ["11.6", "11.7"] },
    { "id": 12, "tasks": ["13.1"] },
    { "id": 13, "tasks": ["13.2", "13.3", "13.4"] },
    { "id": 14, "tasks": ["13.5", "13.6", "14.1"] },
    { "id": 15, "tasks": ["15.1", "15.2", "15.3", "16.1"] }
  ]
}
```
