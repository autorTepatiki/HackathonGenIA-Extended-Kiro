# Production Environment Variables
# Configuration specific to production environment

aws_region          = "us-east-1"
environment         = "prod"
project_name        = "customer-management-prod"
lambda_runtime      = "python3.11"
dynamodb_table_name = "customers-prod"
log_retention_days  = 30

# Lambda Configuration
authorizer_memory_size = 256
authorizer_timeout     = 5
crud_memory_size       = 512
crud_timeout           = 10
