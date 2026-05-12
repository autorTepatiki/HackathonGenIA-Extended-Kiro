# Script to get the correct ID token from Cognito
# The API requires an ID token, not an access token

# Load configuration from environment variables
# Set these before running the script:
#   $env:COGNITO_USER_POOL_ID = "us-east-1_xxxxxxxxx"
#   $env:COGNITO_CLIENT_ID = "your-client-id"
#   $env:TEST_USERNAME = "your-username"
#   $env:TEST_PASSWORD = "your-password"

$UserPoolId = $env:COGNITO_USER_POOL_ID
$ClientId = $env:COGNITO_CLIENT_ID
$Username = $env:TEST_USERNAME
$Password = $env:TEST_PASSWORD

# Validate required environment variables
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

Write-Host "Getting authentication tokens from Cognito..." -ForegroundColor Yellow
Write-Host ""

# Authenticate and get tokens
$response = aws cognito-idp initiate-auth `
  --auth-flow USER_PASSWORD_AUTH `
  --client-id $ClientId `
  --auth-parameters USERNAME=$Username,PASSWORD=$Password `
  --output json | ConvertFrom-Json

if ($response.AuthenticationResult) {
    $IdToken = $response.AuthenticationResult.IdToken
    $AccessToken = $response.AuthenticationResult.AccessToken
    $RefreshToken = $response.AuthenticationResult.RefreshToken
    
    Write-Host "Authentication successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "ID Token (use this for API calls):" -ForegroundColor Cyan
    Write-Host $IdToken
    Write-Host ""
    Write-Host "Access Token:" -ForegroundColor Yellow
    Write-Host $AccessToken
    Write-Host ""
    
    # Save to environment variable
    $env:ID_TOKEN = $IdToken
    
    Write-Host "Environment variable set: `$env:ID_TOKEN" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now you can test the API with these commands:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "# Create customer" -ForegroundColor Cyan
    Write-Host 'Invoke-RestMethod -Uri "$env:API_ENDPOINT/customers" -Method POST -Headers @{Authorization="Bearer $env:ID_TOKEN"} -ContentType "application/json" -Body ''{"name":"John Doe","email":"john@example.com"}'''
    Write-Host ""
    Write-Host "# List customers" -ForegroundColor Cyan
    Write-Host 'Invoke-RestMethod -Uri "$env:API_ENDPOINT/customers" -Method GET -Headers @{Authorization="Bearer $env:ID_TOKEN"}'
    Write-Host ""
} else {
    Write-Host "Authentication failed!" -ForegroundColor Red
    Write-Host ""
    if ($response) {
        Write-Host "Error details:" -ForegroundColor Red
        Write-Host ($response | ConvertTo-Json -Depth 10)
    }
    Write-Host ""
    Write-Host "Make sure the user exists and password is correct." -ForegroundColor Yellow
    Write-Host "To create/update the user, run:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "aws cognito-idp admin-set-user-password --user-pool-id $UserPoolId --username $Username --password `"$Password`" --permanent"
    Write-Host ""
}
