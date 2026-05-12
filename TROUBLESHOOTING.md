# Troubleshooting Guide

> **Note**: All examples use placeholder values like `[YOUR_USER_POOL_ID]`, `[YOUR_CLIENT_ID]`, etc. For actual values and credential setup, see [SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md).

## Common Issues and Solutions

### 1. 401 Unauthorized Error

**Symptom**: API returns 401 error when calling endpoints

**Cause**: Using Access Token instead of ID Token

**Solution**:
```powershell
# Get the correct token
.\get-token.ps1

# Or manually extract the IdToken (not AccessToken) from:
aws cognito-idp initiate-auth `
  --auth-flow USER_PASSWORD_AUTH `
  --client-id [YOUR_CLIENT_ID] `
  --auth-parameters USERNAME=[YOUR_USERNAME],PASSWORD=[YOUR_PASSWORD]
```

**How to identify the token type**:
- Decode your JWT at https://jwt.io
- Look for the `token_use` claim:
  - ❌ `"token_use": "access"` → Wrong token (Access Token)
  - ✅ `"token_use": "id"` → Correct token (ID Token)

### 2. Token Expired

**Symptom**: API returns 403 Forbidden or "Token expired" error

**Cause**: ID tokens expire after 1 hour

**Solution**:
```powershell
# Get a fresh token
.\get-token.ps1
```

### 3. User Does Not Exist

**Symptom**: Authentication fails with "User does not exist"

**Solution**:
```powershell
# Create the user
aws cognito-idp admin-create-user `
  --user-pool-id [YOUR_USER_POOL_ID] `
  --username [YOUR_USERNAME] `
  --temporary-password "[YOUR_TEMP_PASSWORD]" `
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password `
  --user-pool-id [YOUR_USER_POOL_ID] `
  --username [YOUR_USERNAME] `
  --password "[YOUR_SECURE_PASSWORD]" `
  --permanent
```

### 4. Invalid Email Format

**Symptom**: API returns 400 Bad Request with "Invalid email format"

**Cause**: Email doesn't match the validation regex

**Solution**: Use a valid email format (e.g., `user@example.com`)

### 5. Duplicate Email

**Symptom**: API returns 409 Conflict with "Email already exists"

**Cause**: Another customer already has this email

**Solution**: Use a different email or delete the existing customer first

### 6. Missing Required Fields

**Symptom**: API returns 400 Bad Request with "Missing required field"

**Cause**: Request body missing `name` or `email`

**Solution**: Include both required fields:
```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

### 7. CORS Error in Browser

**Symptom**: Browser console shows CORS error

**Cause**: Browser is blocking the request due to CORS policy

**Solution**: 
- CORS is already configured on the API
- Make sure you're including the Authorization header
- Try using curl or Postman instead of browser fetch

### 8. Lambda Function Missing Dependencies

**Symptom**: API returns 500 Internal Server Error, Lambda logs show "No module named 'jose'" or similar import errors

**Cause**: Lambda deployment package doesn't include Python dependencies from requirements.txt

**Solution**: Build Lambda packages with dependencies included
```powershell
# Build Lambda packages with dependencies
python build_lambdas.py

# Update Lambda functions
cd infra
aws lambda update-function-code --function-name customer-management-dev-authorizer --zip-file fileb://authorizer.zip
aws lambda update-function-code --function-name customer-management-dev-crud --zip-file fileb://crud.zip
```

**Note**: Terraform's `archive_file` data source does NOT install Python dependencies. Always use `build_lambdas.py` to create deployment packages.

### 9. JWT Audience Validation Failed

**Symptom**: API returns 403 Forbidden, Authorizer logs show "Invalid audience" or "Token claims validation failed"

**Cause**: Lambda Authorizer is validating JWT audience claim but `COGNITO_CLIENT_ID` environment variable is not set

**Solution**: Add the `COGNITO_CLIENT_ID` environment variable to the Authorizer Lambda
```powershell
# Update Lambda environment variables
aws lambda update-function-configuration `
  --function-name customer-management-dev-authorizer `
  --environment "Variables={COGNITO_USER_POOL_ID=[YOUR_USER_POOL_ID],COGNITO_CLIENT_ID=[YOUR_CLIENT_ID],COGNITO_REGION=[YOUR_REGION]}"
```

**Terraform Fix**: Add to `infra/main.tf` in the authorizer Lambda resource:
```hcl
environment {
  variables = {
    COGNITO_USER_POOL_ID = aws_cognito_user_pool.users.id
    COGNITO_CLIENT_ID    = aws_cognito_user_pool_client.client.id  # Add this line
    COGNITO_REGION       = var.aws_region
  }
}
```

### 10. API Gateway Cannot Invoke Lambda

**Symptom**: API returns 500 Internal Server Error, no logs appear in Lambda CloudWatch

**Cause**: API Gateway doesn't have permission to invoke the Lambda function (missing `aws_lambda_permission` resource)

**Solution**: Add Lambda permission for API Gateway
```powershell
aws lambda add-permission `
  --function-name customer-management-dev-crud `
  --statement-id AllowAPIGatewayInvoke `
  --action lambda:InvokeFunction `
  --principal apigateway.amazonaws.com `
  --source-arn "arn:aws:execute-api:[YOUR_REGION]:[AWS_ACCOUNT_ID]:[YOUR_API_ID]/*"
```

**Verification**: Check if permission exists
```powershell
aws lambda get-policy --function-name customer-management-dev-crud
```

### 11. Authorizer Allows POST but Denies GET/PUT/DELETE

**Symptom**: POST /customers works, but GET/PUT/DELETE return 403 Forbidden with "User is not authorized to access this resource"

**Cause**: Lambda Authorizer returns method-specific IAM policy instead of wildcard policy

**Solution**: Update the `generate_policy` function in `src/authorizer/lambda_function.py` to return wildcard resource:
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
                'Resource': wildcard_resource  # Use wildcard instead of exact resource
            }]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy
```

Then rebuild and redeploy:
```powershell
python build_lambdas.py
cd infra
aws lambda update-function-code --function-name customer-management-dev-authorizer --zip-file fileb://authorizer.zip
```

### 12. Authorizer Cache Causing Stale Denials

**Symptom**: After fixing authorizer issues, API still returns 403 for some requests

**Cause**: API Gateway caches authorizer results for 300 seconds (5 minutes) by default

**Solution**: Disable or reduce authorizer cache TTL
```powershell
# Disable cache (TTL = 0) for testing
aws apigateway update-authorizer `
  --rest-api-id [YOUR_API_ID] `
  --authorizer-id [YOUR_AUTHORIZER_ID] `
  --patch-operations op=replace,path=/authorizerResultTtlInSeconds,value=0

# Or set to 300 seconds for production
aws apigateway update-authorizer `
  --rest-api-id [YOUR_API_ID] `
  --authorizer-id [YOUR_AUTHORIZER_ID] `
  --patch-operations op=replace,path=/authorizerResultTtlInSeconds,value=300
```

**Note**: With cache disabled (TTL=0), the authorizer Lambda is invoked on every request, which increases costs but ensures fresh authorization decisions.

### 13. Lambda Function Errors

**Symptom**: API returns 500 Internal Server Error

**Solution**: Check CloudWatch Logs
```powershell
# View Authorizer logs
aws logs tail /aws/lambda/customer-management-dev-authorizer --follow

# View CRUD logs
aws logs tail /aws/lambda/customer-management-dev-crud --follow
```

### 9. DynamoDB Access Denied

**Symptom**: Lambda logs show "AccessDeniedException" for DynamoDB

**Cause**: IAM role doesn't have DynamoDB permissions

**Solution**: Verify IAM role has AmazonDynamoDBFullAccess policy attached
```powershell
aws iam list-attached-role-policies --role-name customer-management-dev-crud-role
```

### 10. API Gateway Not Found

**Symptom**: curl returns "Could not resolve host"

**Cause**: Wrong API endpoint URL

**Solution**: Verify the endpoint:
```powershell
cd infra
terraform output api_endpoint
```

Should return: `https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod`

---

## Debugging Commands

### Check if user exists
```powershell
aws cognito-idp admin-get-user `
  --user-pool-id [YOUR_USER_POOL_ID] `
  --username [YOUR_USERNAME]
```

### List all customers in DynamoDB
```powershell
aws dynamodb scan --table-name customers-dev
```

### Delete a customer from DynamoDB
```powershell
aws dynamodb delete-item `
  --table-name customers-dev `
  --key '{"customer_id":{"S":"YOUR-CUSTOMER-ID"}}'
```

### Test Lambda function directly
```powershell
# Test Authorizer
aws lambda invoke `
  --function-name customer-management-dev-authorizer `
  --payload '{"type":"TOKEN","authorizationToken":"Bearer YOUR-ID-TOKEN","methodArn":"arn:aws:execute-api:[YOUR_REGION]:[AWS_ACCOUNT_ID]:[YOUR_API_ID]/prod/GET/customers"}' `
  response.json

# Test CRUD
aws lambda invoke `
  --function-name customer-management-dev-crud `
  --payload '{"httpMethod":"GET","path":"/customers","headers":{"Authorization":"Bearer YOUR-ID-TOKEN"}}' `
  response.json
```

### View API Gateway logs
```powershell
# Enable logging first (if not already enabled)
aws apigateway update-stage `
  --rest-api-id [YOUR_API_ID] `
  --stage-name prod `
  --patch-operations op=replace,path=/accessLogSettings/destinationArn,value=arn:aws:logs:[YOUR_REGION]:[AWS_ACCOUNT_ID]:log-group:/aws/apigateway/customer-management-dev
```

---

## Token Comparison

### Access Token (❌ Don't use this)
```json
{
  "token_use": "access",
  "scope": "aws.cognito.signin.user.admin",
  "username": "748834c8-0021-70d5-a862-434bd2c60bfe"
}
```

### ID Token (✅ Use this)
```json
{
  "token_use": "id",
  "email": "[YOUR_EMAIL]",
  "cognito:username": "[YOUR_USERNAME]"
}
```

---

## Quick Test Script

Run the automated test to verify everything works:
```powershell
.\test-api.ps1
```

This script will:
1. Authenticate and get ID token
2. Create a customer
3. List all customers
4. Get customer by ID
5. Update customer
6. Delete customer

---

## Still Having Issues?

1. Check `DEPLOYMENT_CHECKPOINT.md` for detailed infrastructure info
2. Review CloudWatch Logs for error details
3. Verify AWS credentials are valid
4. Ensure all Terraform resources are deployed:
   ```powershell
   cd infra
   terraform state list
   ```

Should show 39 resources.
