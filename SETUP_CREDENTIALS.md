# Setting Up Credentials for Testing

This guide explains how to securely configure credentials for testing the Customer Management API.

## 🔒 Security First

**NEVER commit credentials to version control!**

All credentials are now stored in environment variables, not in the code. This prevents accidental exposure of sensitive information.

---

## Quick Setup (3 Steps)

### Step 1: Create Your .env File

Copy the example file and fill in your values:

```powershell
# Copy the template
Copy-Item .env.example .env

# Edit the file with your actual values
notepad .env
```

Your `.env` file should look like this:

```bash
# API Configuration
API_ENDPOINT=https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod

# Cognito Configuration
COGNITO_USER_POOL_ID=[YOUR_USER_POOL_ID]
COGNITO_CLIENT_ID=[YOUR_CLIENT_ID]

# Test User Credentials
TEST_USERNAME=[YOUR_USERNAME]
TEST_PASSWORD=[YOUR_SECURE_PASSWORD]
```

**Important**: The `.env` file is automatically excluded from git via `.gitignore`.

### Step 2: Load Environment Variables

Run the helper script to load variables into your PowerShell session:

```powershell
.\load-env.ps1
```

This will load all variables from your `.env` file.

### Step 3: Run Tests

Now you can run the test scripts:

```powershell
# Get authentication token
.\get-token.ps1

# Test all API endpoints
.\test-api.ps1
```

---

## Alternative: Manual Setup

If you prefer not to use a `.env` file, you can set environment variables manually:

### PowerShell (Current Session)

```powershell
$env:API_ENDPOINT = "https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod"
$env:COGNITO_USER_POOL_ID = "[YOUR_USER_POOL_ID]"
$env:COGNITO_CLIENT_ID = "[YOUR_CLIENT_ID]"
$env:TEST_USERNAME = "[YOUR_USERNAME]"
$env:TEST_PASSWORD = "[YOUR_SECURE_PASSWORD]"
```

### PowerShell (Persistent - User Level)

```powershell
[System.Environment]::SetEnvironmentVariable("API_ENDPOINT", "https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod", "User")
[System.Environment]::SetEnvironmentVariable("COGNITO_USER_POOL_ID", "[YOUR_USER_POOL_ID]", "User")
[System.Environment]::SetEnvironmentVariable("COGNITO_CLIENT_ID", "[YOUR_CLIENT_ID]", "User")
[System.Environment]::SetEnvironmentVariable("TEST_USERNAME", "[YOUR_USERNAME]", "User")
[System.Environment]::SetEnvironmentVariable("TEST_PASSWORD", "[YOUR_SECURE_PASSWORD]", "User")
```

**Note**: Restart PowerShell after setting user-level variables.

### Windows System Environment Variables

1. Open System Properties → Advanced → Environment Variables
2. Under "User variables", click "New"
3. Add each variable:
   - Variable name: `API_ENDPOINT`
   - Variable value: `https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod`
4. Repeat for all variables
5. Restart PowerShell

---

## CI/CD Setup

For automated testing in CI/CD pipelines:

### GitHub Actions

```yaml
name: Test API
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run API Tests
        env:
          API_ENDPOINT: ${{ secrets.API_ENDPOINT }}
          COGNITO_USER_POOL_ID: ${{ secrets.COGNITO_USER_POOL_ID }}
          COGNITO_CLIENT_ID: ${{ secrets.COGNITO_CLIENT_ID }}
          TEST_USERNAME: ${{ secrets.TEST_USERNAME }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: |
          pwsh ./test-api.ps1
```

Store secrets in: Repository Settings → Secrets and variables → Actions

### GitLab CI

```yaml
test:
  script:
    - pwsh ./test-api.ps1
  variables:
    API_ENDPOINT: $API_ENDPOINT
    COGNITO_USER_POOL_ID: $COGNITO_USER_POOL_ID
    COGNITO_CLIENT_ID: $COGNITO_CLIENT_ID
    TEST_USERNAME: $TEST_USERNAME
    TEST_PASSWORD: $TEST_PASSWORD
```

Store secrets in: Settings → CI/CD → Variables

---

## AWS Secrets Manager (Production)

For production environments, use AWS Secrets Manager:

### Store Credentials

```powershell
aws secretsmanager create-secret `
  --name customer-mgmt/test-credentials `
  --description "Test credentials for Customer Management API" `
  --secret-string '{
    "username": "[YOUR_USERNAME]",
    "password": "[YOUR_SECURE_PASSWORD]",
    "api_endpoint": "https://[YOUR_API_ID].execute-api.[YOUR_REGION].amazonaws.com/prod",
    "user_pool_id": "[YOUR_USER_POOL_ID]",
    "client_id": "[YOUR_CLIENT_ID]"
  }'
```

### Retrieve Credentials

```powershell
# Get secret
$secret = aws secretsmanager get-secret-value `
  --secret-id customer-mgmt/test-credentials `
  --query SecretString `
  --output text | ConvertFrom-Json

# Set environment variables
$env:API_ENDPOINT = $secret.api_endpoint
$env:COGNITO_USER_POOL_ID = $secret.user_pool_id
$env:COGNITO_CLIENT_ID = $secret.client_id
$env:TEST_USERNAME = $secret.username
$env:TEST_PASSWORD = $secret.password

# Run tests
.\test-api.ps1
```

---

## Troubleshooting

### "Environment variable is not set" Error

**Problem**: Script shows error about missing environment variables.

**Solution**: 
1. Make sure you ran `.\load-env.ps1` first
2. Or set the variables manually (see Alternative Setup above)
3. Verify variables are set: `Get-ChildItem Env: | Where-Object Name -like "*COGNITO*"`

### .env File Not Found

**Problem**: `load-env.ps1` says ".env file not found"

**Solution**:
1. Copy `.env.example` to `.env`: `Copy-Item .env.example .env`
2. Edit `.env` with your actual values
3. Run `.\load-env.ps1` again

### Variables Not Persisting

**Problem**: Variables disappear when you close PowerShell

**Solution**: 
- Use `.\load-env.ps1` in each new PowerShell session
- Or set user-level environment variables (see Alternative Setup)
- Or use Windows System Environment Variables

---

## Security Best Practices

✅ **DO**:
- Use `.env` files for local development
- Use AWS Secrets Manager for production
- Use CI/CD secret management for pipelines
- Rotate credentials regularly
- Use strong, unique passwords

❌ **DON'T**:
- Commit `.env` files to git
- Share credentials via email or chat
- Use the same password across environments
- Store credentials in code or documentation
- Use weak or default passwords

---

## Getting Your Values

If you don't know your configuration values:

### API Endpoint
```powershell
cd infra
terraform output api_endpoint
```

### Cognito User Pool ID
```powershell
cd infra
terraform output user_pool_id
```

### Cognito Client ID
```powershell
cd infra
terraform output user_pool_client_id
```

### Create Test User
```powershell
# Create user
aws cognito-idp admin-create-user `
  --user-pool-id <YOUR_USER_POOL_ID> `
  --username [YOUR_USERNAME] `
  --temporary-password "[YOUR_TEMP_PASSWORD]" `
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password `
  --user-pool-id <YOUR_USER_POOL_ID> `
  --username [YOUR_USERNAME] `
  --password "[YOUR_SECURE_PASSWORD]" `
  --permanent
```

---

## Need Help?

- Check `TROUBLESHOOTING.md` for common issues
- Review `SECURITY_ALERT.md` for security guidelines
- See `README.md` for project overview
