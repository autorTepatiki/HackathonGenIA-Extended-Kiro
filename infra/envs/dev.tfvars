# Development Environment Variables
# Configuration specific to development environment

aws_region          = "us-east-1"
environment         = "dev"
project_name        = "customer-management-dev"
lambda_runtime      = "python3.11"
dynamodb_table_name = "customers-dev"
log_retention_days  = 7

# Lambda Configuration
authorizer_memory_size = 256
authorizer_timeout     = 5
crud_memory_size       = 512
crud_timeout           = 10
