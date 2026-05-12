# Input Variables
# Defines configurable parameters for the infrastructure

variable "aws_region" {
  description = "AWS region for resource deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "customer-management"
}

variable "lambda_runtime" {
  description = "Lambda function runtime"
  type        = string
  default     = "python3.11"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for customer data"
  type        = string
  default     = "customers"
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 7
}

variable "authorizer_memory_size" {
  description = "Memory allocation for authorizer Lambda (MB)"
  type        = number
  default     = 256
}

variable "authorizer_timeout" {
  description = "Timeout for authorizer Lambda (seconds)"
  type        = number
  default     = 5
}

variable "crud_memory_size" {
  description = "Memory allocation for CRUD Lambda (MB)"
  type        = number
  default     = 512
}

variable "crud_timeout" {
  description = "Timeout for CRUD Lambda (seconds)"
  type        = number
  default     = 10
}
