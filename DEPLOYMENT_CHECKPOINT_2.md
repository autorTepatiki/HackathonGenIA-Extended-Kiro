# Deployment Checkpoint 2 - API Fully Functional

> **Important**: This document uses placeholder values. For actual credential values and setup instructions, see [SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md).

**Date**: May 12, 2026  
**Status**: ✅ All API endpoints working correctly  
**Environment**: AWS Development ([YOUR_REGION])

---

## Current State Summary

The Customer Management API is now **fully functional** with all CRUD operations working correctly:

- ✅ Authentication with Cognito ID tokens
- ✅ POST /customers (Create)
- ✅ GET /customers (List all)
- ✅ GET /customers/{id} (Get by ID)
- ✅ PUT /customers/{id} (Update)
- ✅ DELETE /customers/{id} (Delete)

---

## Issues Resolved in This Session

### Issue 1: Lambda Functions Missing Python Dependencies

**Problem**: Lambda functions were failing with `Runtime.ImportModuleError: No module named 'jose'`

**Root Cause**: Terraform's `archive_file` data source was creating zip files without installing Python dependencies from requirements.txt

**Solution Applied**:
1. Used `build_lambdas.py` to properly install dependencies and create packages
2. Updated Lambda functions via AWS CLI:
   ```powershell
   python build_lambdas.py
   cd infra
   aws lambda update-function-code --function-name customer-management-dev-authorizer --zip-file fileb://authorizer.zip
   aws lambda update-function-code --function-name customer-management-dev-crud --zip-file fileb://crud.zip
   ```

**Files Modified**:
- `infra/authorizer.zip` (22.24 MB with dependencies)
- `infra/crud.zip` (16.19 MB with dependencies)

---

### Issue 2: JWT Audience Validation Failed

**Problem**: Authorizer returning 403 Forbidden with error: "Token claims validation failed: Invalid audience"

**Root Cause**: The `python-jose` library's `jwt.decode()` was validating the `aud` (audience) claim, but the `COGNITO_CLIENT_ID` environment variable was not set in the Lambda function

**Solution Applied**:
1. Added `COGNITO_CLIENT_ID` environment variable to authorizer Lambda configuration
2. Updated `src/authorizer/lambda_function.py` to validate audience:
   ```python
   expected_audience = os.environ.get('COGNITO_CLIENT_ID', '')
   
   claims = jwt.decode(
       token,
       key,
       algorithms=['RS256'],
       issuer=issuer,
       audience=expected_audience,  # Added audience validation
       options={
           'verify_signature': True,
           'verify_exp': True,
           'verify_iss': True,
           'verify_aud': True  # Added audience verification
       }
   )
   ```

**AWS CLI Command Used**:
```powershell
aws lambda update-function-configuration `
  --function-name customer-management-dev-authorizer `
  --environment "Variables={COGNITO_USER_POOL_ID=[YOUR_USER_POOL_ID],COGNITO_CLIENT_ID=[YOUR_CLIENT_ID],COGNITO_REGION=[YOUR_REGION]}"
```

**Files Modified**:
- `src/authorizer/lambda_function.py` (lines 130-145)
- `infra/main.tf` (added COGNITO_CLIENT_ID to environment variables)

---

### Issue 3: API Gateway Cannot Invoke Lambda

**Problem**: API returning 500 errors, no logs appearing in Lambda CloudWatch

**Root Cause**: The `aws_lambda_permission` resource was not created due to Terraform apply failure, so API Gateway didn't have permission to invoke the CRUD Lambda

**Solution Applied**:
```powershell
aws lambda add-permission `
  --function-name customer-management-dev-crud `
  --statement-id AllowAPIGatewayInvoke `
  --action lambda:InvokeFunction `
  --principal apigateway.amazonaws.com `
  --source-arn "arn:aws:execute-api:[YOUR_REGION]:[AWS_ACCOUNT_ID]:[YOUR_API_ID]/*"
```

**Verification**:
```powershell
aws lambda get-policy --function-name customer-management-dev-crud
# Returns: Statement with Sid "AllowAPIGatewayInvoke"
```

---

### Issue 4: Authorizer Allows POST but Denies Other Methods

**Problem**: POST /customers worked, but GET/PUT/DELETE returned 403 with "User is not authorized to access this resource"

**Root Cause**: Lambda Authorizer was returning method-specific IAM policies (e.g., only allowing `arn:aws:execute-api:[YOUR_REGION]:[AWS_ACCOUNT_ID]:[YOUR_API_ID]/prod/POST/customers`) instead of wildcard policies

**Solution Applied**:
Updated `generate_policy()` function in `src/authorizer/lambda_function.py` to return wildcard resource:
```python
def generate_policy(principal_id: str, effect: str, resource: str, context: Dict[str, str] = None) -> dict:
    # Extract the API Gateway ARN prefix and create a wildcard policy
    # Format: arn:aws:execute-api:region:account-id:api-id/stage/method/resource
    # We want: arn:aws:execute-api:region:account-id:api-id/*
    resource_parts = resource.split('/')
    if len(resource_parts) >= 2:
        wildcard_resource = resource_parts[0] + '/*'
    else:
        wildcard_resource = resource
    
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': wildcard_resource  # Wildcard instead of exact resource
            }]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy
```

**Files Modified**:
- `src/authorizer/lambda_function.py` (lines 223-256)

---

### Issue 5: Authorizer Cache Causing Stale Denials

**Problem**: After fixing authorizer, some requests still returned 403 due to cached authorization results

**Root Cause**: API Gateway caches authorizer results for 300 seconds by default

**Solution Applied**:
```powershell
# Disabled cache for testing (TTL = 0)
aws apigateway update-authorizer `
  --rest-api-id [YOUR_API_ID] `
  --authorizer-id [YOUR_AUTHORIZER_ID] `
  --patch-operations op=replace,path=/authorizerResultTtlInSeconds,value=0
```

**Note**: For production, re-enable caching with TTL=300 to reduce Lambda invocations and costs.

---

## Terraform State Issues Encountered

During the session, we attempted to run `terraform apply` to update the Lambda environment variables. This caused issues because:

1. **IAM Permission Restrictions**: Our AWS user doesn't have `iam:DetachRolePolicy` permission
2. **Resource Replacement**: Terraform tried to replace resources (Cognito User Pool, DynamoDB table, IAM roles) instead of updating them in place
3. **Duplicate Resources Created**: New resources were created before the old ones could be destroyed

**Resources Created by Failed Terraform Apply**:
- Cognito User Pool: `[TEMP_USER_POOL_ID]` (deleted)
- DynamoDB Table: `customers` (deleted)
- CloudWatch Log Groups: `/aws/lambda/customer-management-authorizer` and `/aws/lambda/customer-management-crud` (kept, as they don't conflict)

**Cleanup Performed**:
```powershell
aws cognito-idp delete-user-pool --user-pool-id [TEMP_USER_POOL_ID]
aws dynamodb delete-table --table-name customers
```

**Lesson Learned**: When only updating Lambda code or environment variables, use AWS CLI commands instead of Terraform to avoid triggering resource replacements.

---

## Current Infrastructure State

### AWS Resources (39 total)

**Cognito**:
- User Pool: `[YOUR_USER_POOL_ID]` (customer-management-dev-users)
- User Pool Client: `[YOUR_CLIENT_ID]` (customer-management-dev-client)
- Test User: `[YOUR_USERNAME]` (password: `[YOUR_SECURE_PASSWORD]`)

**DynamoDB**:
- Table: `customers-dev`
- Partition Key: `customer_id` (String)
- GSI: `email-index` on `email` attribute
- Billing Mode: PAY_PER_REQUEST

**Lambda Functions**:
- Authorizer: `customer-management-dev-authorizer`
  - Runtime: Python 3.11
  - Memory: 256 MB
  - Timeout: 5 seconds
  - Code Size: 23.32 MB (with dependencies)
  - Environment Variables:
    - `COGNITO_USER_POOL_ID`: [YOUR_USER_POOL_ID]
    - `COGNITO_CLIENT_ID`: [YOUR_CLIENT_ID]
    - `COGNITO_REGION`: [YOUR_REGION]

- CRUD: `customer-management-dev-crud`
  - Runtime: Python 3.11
  - Memory: 512 MB
  - Timeout: 30 seconds
  - Code Size: 16.97 MB (with dependencies)
  - Environment Variables:
    - `TABLE_NAME`: customers-dev
    - `REGION`: [YOUR_REGION]

**API Gateway**:
- REST API: `[YOUR_API_ID]` (customer-management-dev-api)
- Stage: `prod`
- Endpoint: `https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod`
- Authorizer: `[YOUR_AUTHORIZER_ID]` (customer-management-dev-authorizer)
  - Type: TOKEN
  - Identity Source: `method.request.header.Authorization`
  - Result TTL: 0 seconds (caching disabled for testing)

**CloudWatch Log Groups**:
- `/aws/lambda/customer-management-dev-authorizer`
- `/aws/lambda/customer-management-dev-crud`

**IAM Roles**:
- `customer-management-dev-authorizer-role` (with AWSLambdaBasicExecutionRole)
- `customer-management-dev-crud-role` (with AWSLambdaBasicExecutionRole + AmazonDynamoDBFullAccess)
- `customer-management-dev-api-gateway-authorizer-role` (with AWSLambdaRole)

---

## Testing Results

### Full API Test (test-api.ps1)

```
Step 1: Authenticating... ✅
Step 2: Creating customer... ✅
Step 3: Listing all customers... ✅
Step 4: Getting customer by ID... ✅
Step 5: Updating customer... ✅
Step 6: Deleting customer... ✅
```

**Sample Response**:
```json
{
  "customer_id": "5fb2fe3a-43ac-4ead-b0a0-4c8852bcc5bb",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "555-1234",
  "address": null,
  "company": "Acme Corp",
  "notes": null,
  "created_at": "2026-05-12T10:37:02.515382Z",
  "updated_at": "2026-05-12T10:37:02.515382Z"
}
```

---

## Files Modified in This Session

### Source Code
1. **src/authorizer/lambda_function.py**
   - Added JWT audience validation (lines 130-145)
   - Updated `generate_policy()` to return wildcard IAM policies (lines 223-256)

### Infrastructure
2. **infra/main.tf**
   - Added `COGNITO_CLIENT_ID` environment variable to authorizer Lambda (line 132)

### Documentation
3. **TROUBLESHOOTING.md**
   - Added Issue 8: Lambda Function Missing Dependencies
   - Added Issue 9: JWT Audience Validation Failed
   - Added Issue 10: API Gateway Cannot Invoke Lambda
   - Added Issue 11: Authorizer Allows POST but Denies GET/PUT/DELETE
   - Added Issue 12: Authorizer Cache Causing Stale Denials

4. **DEPLOYMENT_CHECKPOINT_2.md** (this file)
   - Comprehensive documentation of all fixes and current state

---

## Quick Start Commands

### Test the API
```powershell
# Run full test suite
.\test-api.ps1

# Get a fresh token
.\get-token.ps1
```

### View Logs
```powershell
# Authorizer logs
aws logs tail /aws/lambda/customer-management-dev-authorizer --follow

# CRUD logs
aws logs tail /aws/lambda/customer-management-dev-crud --follow
```

### Rebuild and Redeploy Lambda Functions
```powershell
# Build packages with dependencies
python build_lambdas.py

# Update authorizer
cd infra
aws lambda update-function-code --function-name customer-management-dev-authorizer --zip-file fileb://authorizer.zip

# Update CRUD
aws lambda update-function-code --function-name customer-management-dev-crud --zip-file fileb://crud.zip
```

---

## Known Limitations

1. **Authorizer Cache Disabled**: Currently set to TTL=0 for testing. Should be re-enabled to 300 seconds for production to reduce costs.

2. **IAM Permissions**: Our AWS user has limited IAM permissions:
   - Cannot use `iam:TagRole`
   - Cannot use `iam:PutRolePolicy` or `iam:DetachRolePolicy`
   - Must use AWS managed policies instead of inline policies

3. **Terraform State**: Some manual changes were made via AWS CLI that are not reflected in Terraform state. Future Terraform applies may try to revert these changes.

---

## Next Steps

### For Production Deployment

1. **Re-enable Authorizer Cache**:
   ```powershell
   aws apigateway update-authorizer `
     --rest-api-id [YOUR_API_ID] `
     --authorizer-id [YOUR_AUTHORIZER_ID] `
     --patch-operations op=replace,path=/authorizerResultTtlInSeconds,value=300
   ```

2. **Update Terraform State**: Import manual changes into Terraform state or update Terraform configuration to match current state

3. **Enable API Gateway Logging**: Configure CloudWatch logging for API Gateway stage

4. **Add Monitoring**: Set up CloudWatch alarms for Lambda errors, API Gateway 4xx/5xx errors, and DynamoDB throttling

5. **Security Hardening**:
   - Review IAM policies for least privilege
   - Enable AWS WAF for API Gateway
   - Configure VPC endpoints for Lambda (if needed)
   - Enable encryption at rest for DynamoDB

6. **Performance Optimization**:
   - Adjust Lambda memory/timeout based on actual usage
   - Configure DynamoDB auto-scaling (if switching from PAY_PER_REQUEST)
   - Enable API Gateway caching for read-heavy endpoints

---

## Contact Information

**AWS Account**: [AWS_ACCOUNT_ID]  
**Region**: [YOUR_REGION]  
**Profile**: [YOUR_AWS_PROFILE]

---

## Appendix: Key Code Changes

### A. JWT Audience Validation (src/authorizer/lambda_function.py)

```python
# Before
claims = jwt.decode(
    token,
    key,
    algorithms=['RS256'],
    issuer=issuer,
    options={
        'verify_signature': True,
        'verify_exp': True,
        'verify_iss': True
    }
)

# After
expected_audience = os.environ.get('COGNITO_CLIENT_ID', '')

claims = jwt.decode(
    token,
    key,
    algorithms=['RS256'],
    issuer=issuer,
    audience=expected_audience,
    options={
        'verify_signature': True,
        'verify_exp': True,
        'verify_iss': True,
        'verify_aud': True
    }
)
```

### B. Wildcard IAM Policy (src/authorizer/lambda_function.py)

```python
# Before
policy = {
    'principalId': principal_id,
    'policyDocument': {
        'Version': '2012-10-17',
        'Statement': [{
            'Action': 'execute-api:Invoke',
            'Effect': effect,
            'Resource': resource  # Exact resource only
        }]
    }
}

# After
resource_parts = resource.split('/')
if len(resource_parts) >= 2:
    wildcard_resource = resource_parts[0] + '/*'
else:
    wildcard_resource = resource

policy = {
    'principalId': principal_id,
    'policyDocument': {
        'Version': '2012-10-17',
        'Statement': [{
            'Action': 'execute-api:Invoke',
            'Effect': effect,
            'Resource': wildcard_resource  # Wildcard for all methods
        }]
    }
}
```

---

**End of Checkpoint 2**
