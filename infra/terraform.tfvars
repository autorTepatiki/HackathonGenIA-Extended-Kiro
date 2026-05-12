# Default Terraform Variables
# Default values for infrastructure deployment

aws_region          = "us-east-1"
environment         = "dev"
project_name        = "customer-management"
lambda_runtime      = "python3.11"
dynamodb_table_name = "customers"
log_retention_days  = 7

# Lambda Configuration
authorizer_memory_size = 256
authorizer_timeout     = 5
crud_memory_size       = 512
crud_timeout           = 10
