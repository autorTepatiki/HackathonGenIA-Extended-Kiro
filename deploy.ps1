# Customer Management MVP - Deployment Script
# This script deploys the infrastructure to AWS

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Customer Management MVP Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS credentials are configured
Write-Host "Checking AWS credentials..." -ForegroundColor Yellow
$callerIdentity = aws sts get-caller-identity 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ AWS credentials not configured or expired" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please configure AWS credentials using one of these methods:" -ForegroundColor Yellow
    Write-Host "  1. aws configure (for permanent credentials)"
    Write-Host "  2. aws login (for SSO)"
    Write-Host "  3. Set environment variables:"
    Write-Host "     `$env:AWS_ACCESS_KEY_ID='...'"
    Write-Host "     `$env:AWS_SECRET_ACCESS_KEY='...'"
    Write-Host "     `$env:AWS_SESSION_TOKEN='...' (if using temporary credentials)"
    Write-Host "     `$env:AWS_DEFAULT_REGION='us-east-1'"
    Write-Host ""
    exit 1
}

Write-Host "✓ AWS credentials valid" -ForegroundColor Green
$callerIdentity | ConvertFrom-Json | Format-List
Write-Host ""

# Navigate to infra directory
Set-Location -Path "$PSScriptRoot\infra"

# Check if Lambda packages exist
Write-Host "Checking Lambda deployment packages..." -ForegroundColor Yellow
if (-not (Test-Path "authorizer.zip")) {
    Write-Host "❌ authorizer.zip not found" -ForegroundColor Red
    Write-Host "Run: python build_lambdas.py" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path "crud.zip")) {
    Write-Host "❌ crud.zip not found" -ForegroundColor Red
    Write-Host "Run: python build_lambdas.py" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Lambda packages found" -ForegroundColor Green
Write-Host ""

# Initialize Terraform
Write-Host "Initializing Terraform..." -ForegroundColor Yellow
terraform init
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform init failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Terraform initialized" -ForegroundColor Green
Write-Host ""

# Validate configuration
Write-Host "Validating Terraform configuration..." -ForegroundColor Yellow
terraform validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform validation failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Configuration valid" -ForegroundColor Green
Write-Host ""

# Create plan
Write-Host "Creating Terraform plan..." -ForegroundColor Yellow
terraform plan -var-file="envs/dev.tfvars" -out=tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform plan failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Plan created successfully" -ForegroundColor Green
Write-Host ""

# Ask for confirmation
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ready to deploy infrastructure!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will create the following resources:" -ForegroundColor Yellow
Write-Host "  • DynamoDB table (customers-dev)"
Write-Host "  • Cognito User Pool"
Write-Host "  • Lambda Authorizer function"
Write-Host "  • Lambda CRUD function"
Write-Host "  • API Gateway REST API"
Write-Host "  • CloudWatch Log Groups"
Write-Host "  • IAM Roles and Policies"
Write-Host ""
$confirmation = Read-Host "Do you want to proceed with deployment? (yes/no)"

if ($confirmation -ne "yes") {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

# Apply the plan
Write-Host ""
Write-Host "Deploying infrastructure..." -ForegroundColor Yellow
terraform apply tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Terraform apply failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ Deployment Successful!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Get outputs
Write-Host "Infrastructure Outputs:" -ForegroundColor Cyan
terraform output
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Create a Cognito user:"
Write-Host "     aws cognito-idp admin-create-user --user-pool-id <pool-id> --username testuser"
Write-Host ""
Write-Host "  2. Set user password:"
Write-Host "     aws cognito-idp admin-set-user-password --user-pool-id <pool-id> --username testuser --password 'YourPassword123!' --permanent"
Write-Host ""
Write-Host "  3. Test the API:"
Write-Host "     curl -X GET <api-endpoint>/customers -H 'Authorization: Bearer <jwt-token>'"
Write-Host ""
