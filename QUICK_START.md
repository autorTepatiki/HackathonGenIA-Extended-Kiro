# Customer Management MVP - Quick Start Guide

> **Important**: This guide uses placeholder values. For actual credential values and setup instructions, see [SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md).

## 🎉 Deployment Status: COMPLETE

All infrastructure is deployed and ready for testing!

---

## 📋 Quick Reference

### API Endpoint
```
https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod
```

### Cognito Details
- **User Pool ID**: `[YOUR_USER_POOL_ID]`
- **Client ID**: `[YOUR_CLIENT_ID]`

### DynamoDB Table
- **Table Name**: `customers-dev`

---

## 🚀 Quick Test (3 Steps)

### Step 1: Create Test User
```powershell
aws cognito-idp admin-create-user `
  --user-pool-id [YOUR_USER_POOL_ID] `
  --username [YOUR_USERNAME] `
  --temporary-password "[YOUR_TEMP_PASSWORD]" `
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password `
  --user-pool-id [YOUR_USER_POOL_ID] `
  --username [YOUR_USERNAME] `
  --password "[YOUR_SECURE_PASSWORD]" `
  --permanent
```

### Step 2: Get JWT Token

**IMPORTANT**: You need the **ID Token**, not the Access Token!

```powershell
# Run the helper script
.\get-token.ps1
```

Or manually:
```powershell
aws cognito-idp initiate-auth `
  --auth-flow USER_PASSWORD_AUTH `
  --client-id [YOUR_CLIENT_ID] `
  --auth-parameters USERNAME=[YOUR_USERNAME],PASSWORD=[YOUR_SECURE_PASSWORD]
```

Copy the **`IdToken`** value (NOT the AccessToken) from the response.

### Step 3: Test API

**Option A: Automated Test (Recommended)**
```powershell
.\test-api.ps1
```

**Option B: Manual Test**
```powershell
# Set your ID token (from step 2)
$TOKEN = "paste-your-ID-token-here"

# Create a customer
curl -X POST https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod/customers `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"name":"John Doe","email":"john@example.com","phone":"555-1234"}'

# List customers
curl -X GET https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod/customers `
  -H "Authorization: Bearer $TOKEN"
```

**Common Issue**: If you get a 401 error, make sure you're using the **ID Token**, not the Access Token!

---

## 📚 Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /customers | Create new customer |
| GET | /customers | List all customers |
| GET | /customers/{id} | Get customer by ID |
| PUT | /customers/{id} | Update customer |
| DELETE | /customers/{id} | Delete customer |

**All endpoints require JWT token in Authorization header.**

---

## 📖 Documentation

- **Full Deployment Details**: See `DEPLOYMENT_CHECKPOINT.md`
- **Architecture & Design**: See `README.md`
- **Build Instructions**: See `BUILD.md`
- **Spec Documents**: See `.kiro/specs/customer-management-mvp/`

---

## 🔧 Useful Commands

### View Terraform Outputs
```powershell
cd infra
terraform output
```

### View Lambda Logs
```powershell
# Authorizer logs
aws logs tail /aws/lambda/customer-management-dev-authorizer --follow

# CRUD logs
aws logs tail /aws/lambda/customer-management-dev-crud --follow
```

### Check DynamoDB Table
```powershell
aws dynamodb scan --table-name customers-dev
```

### Redeploy Infrastructure
```powershell
.\deploy.ps1
```

---

## 🛑 Teardown

To remove all infrastructure:
```powershell
cd infra
terraform destroy -var-file="envs/dev.tfvars"
```

---

## ✅ What's Deployed

- ✅ DynamoDB table with email GSI
- ✅ Cognito User Pool for authentication
- ✅ Lambda Authorizer (JWT validation)
- ✅ Lambda CRUD (customer operations)
- ✅ API Gateway REST API with CORS
- ✅ CloudWatch Logs (7-day retention)
- ✅ IAM roles with managed policies

**Total Resources**: 39  
**Status**: All operational  
**Environment**: Development (dev)

---

## 📞 Support

For detailed information, see `DEPLOYMENT_CHECKPOINT.md`.

**Deployment Date**: December 5, 2026  
**AWS Account**: [AWS_ACCOUNT_ID]  
**Region**: [YOUR_REGION]
