# Test script for Customer Management API
# This script gets the ID token and tests all API endpoints

# Load configuration from environment variables
# Set these before running the script:
#   $env:API_ENDPOINT = "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod"
#   $env:COGNITO_USER_POOL_ID = "us-east-1_xxxxxxxxx"
#   $env:COGNITO_CLIENT_ID = "your-client-id"
#   $env:TEST_USERNAME = "your-username"
#   $env:TEST_PASSWORD = "your-password"

$ApiEndpoint = $env:API_ENDPOINT
$UserPoolId = $env:COGNITO_USER_POOL_ID
$ClientId = $env:COGNITO_CLIENT_ID
$Username = $env:TEST_USERNAME
$Password = $env:TEST_PASSWORD

# Validate required environment variables
if (-not $ApiEndpoint) {
    Write-Host "ERROR: API_ENDPOINT environment variable is not set" -ForegroundColor Red
    Write-Host "Set it with: `$env:API_ENDPOINT='https://your-api-id.execute-api.us-east-1.amazonaws.com/prod'" -ForegroundColor Yellow
    exit 1
}

if (-not $UserPoolId) {
    Write-Host "ERROR: COGNITO_USER_POOL_ID environment variable is not set" -ForegroundColor Red
    Write-Host "Set it with: `$env:COGNITO_USER_POOL_ID='us-east-1_xxxxxxxxx'" -ForegroundColor Yellow
    exit 1
}

if (-not $ClientId) {
    Write-Host "ERROR: COGNITO_CLIENT_ID environment variable is not set" -ForegroundColor Red
    Write-Host "Set it with: `$env:COGNITO_CLIENT_ID='your-client-id'" -ForegroundColor Yellow
    exit 1
}

if (-not $Username) {
    Write-Host "ERROR: TEST_USERNAME environment variable is not set" -ForegroundColor Red
    Write-Host "Set it with: `$env:TEST_USERNAME='your-username'" -ForegroundColor Yellow
    exit 1
}

if (-not $Password) {
    Write-Host "ERROR: TEST_PASSWORD environment variable is not set" -ForegroundColor Red
    Write-Host "Set it with: `$env:TEST_PASSWORD='your-password'" -ForegroundColor Yellow
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Customer Management API Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get ID Token
Write-Host "Step 1: Authenticating..." -ForegroundColor Yellow
try {
    $authResponse = aws cognito-idp initiate-auth `
      --auth-flow USER_PASSWORD_AUTH `
      --client-id $ClientId `
      --auth-parameters USERNAME=$Username,PASSWORD=$Password `
      --output json | ConvertFrom-Json
    
    $IdToken = $authResponse.AuthenticationResult.IdToken
    Write-Host "Authentication successful!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "Authentication failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure the user exists:" -ForegroundColor Yellow
    Write-Host "  aws cognito-idp admin-create-user --user-pool-id $UserPoolId --username $Username --temporary-password `"[YOUR_TEMP_PASSWORD]`" --message-action SUPPRESS"
    Write-Host "  aws cognito-idp admin-set-user-password --user-pool-id $UserPoolId --username $Username --password `"$Password`" --permanent"
    exit 1
}

# Prepare headers
$headers = @{
    "Authorization" = "Bearer $IdToken"
    "Content-Type" = "application/json"
}

# Step 2: Create a customer
Write-Host "Step 2: Creating customer..." -ForegroundColor Yellow
try {
    $createBody = @{
        name = "John Doe"
        email = "john@example.com"
        phone = "555-1234"
        company = "Acme Corp"
    } | ConvertTo-Json
    
    $customer = Invoke-RestMethod -Uri "$ApiEndpoint/customers" -Method POST -Headers $headers -Body $createBody
    $customerId = $customer.customer_id
    
    Write-Host "Response:" -ForegroundColor Cyan
    Write-Host ($customer | ConvertTo-Json -Depth 10)
    Write-Host ""
    Write-Host "Customer created with ID: $customerId" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "Failed to create customer" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    $customerId = $null
}

# Step 3: List all customers
Write-Host "Step 3: Listing all customers..." -ForegroundColor Yellow
try {
    $customers = Invoke-RestMethod -Uri "$ApiEndpoint/customers" -Method GET -Headers $headers
    
    Write-Host "Response:" -ForegroundColor Cyan
    Write-Host ($customers | ConvertTo-Json -Depth 10)
    Write-Host ""
    Write-Host "Found $($customers.Count) customer(s)" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "Failed to list customers" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Step 4: Get customer by ID (if we have one)
if ($customerId) {
    Write-Host "Step 4: Getting customer by ID..." -ForegroundColor Yellow
    try {
        $customer = Invoke-RestMethod -Uri "$ApiEndpoint/customers/$customerId" -Method GET -Headers $headers
        
        Write-Host "Response:" -ForegroundColor Cyan
        Write-Host ($customer | ConvertTo-Json -Depth 10)
        Write-Host ""
        Write-Host "Customer retrieved successfully" -ForegroundColor Green
        Write-Host ""
    } catch {
        Write-Host "Failed to get customer" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
    
    # Step 5: Update customer
    Write-Host "Step 5: Updating customer..." -ForegroundColor Yellow
    try {
        $updateBody = @{
            phone = "555-9999"
            company = "New Corp"
        } | ConvertTo-Json
        
        $updatedCustomer = Invoke-RestMethod -Uri "$ApiEndpoint/customers/$customerId" -Method PUT -Headers $headers -Body $updateBody
        
        Write-Host "Response:" -ForegroundColor Cyan
        Write-Host ($updatedCustomer | ConvertTo-Json -Depth 10)
        Write-Host ""
        Write-Host "Customer updated successfully" -ForegroundColor Green
        Write-Host ""
    } catch {
        Write-Host "Failed to update customer" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
    
    # Step 6: Delete customer
    Write-Host "Step 6: Deleting customer..." -ForegroundColor Yellow
    try {
        $deleteResponse = Invoke-RestMethod -Uri "$ApiEndpoint/customers/$customerId" -Method DELETE -Headers $headers
        
        Write-Host "Response:" -ForegroundColor Cyan
        Write-Host ($deleteResponse | ConvertTo-Json -Depth 10)
        Write-Host ""
        Write-Host "Customer deleted successfully" -ForegroundColor Green
        Write-Host ""
    } catch {
        Write-Host "Failed to delete customer" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  API Test Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your ID Token (valid for 1 hour):" -ForegroundColor Yellow
Write-Host $IdToken
Write-Host ""
