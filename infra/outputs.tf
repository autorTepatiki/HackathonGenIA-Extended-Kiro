# Output Values
# Exports important resource identifiers and endpoints after deployment

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_stage.prod.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.customer_api.id
}

output "user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.users.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.users.arn
}

output "user_pool_client_id" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.client.id
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.customers.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.customers.arn
}

output "authorizer_lambda_arn" {
  description = "Lambda Authorizer function ARN"
  value       = aws_lambda_function.authorizer.arn
}

output "crud_lambda_arn" {
  description = "Customer CRUD Lambda function ARN"
  value       = aws_lambda_function.crud.arn
}

output "authorizer_log_group" {
  description = "CloudWatch Log Group for Authorizer Lambda"
  value       = aws_cloudwatch_log_group.authorizer.name
}

output "crud_log_group" {
  description = "CloudWatch Log Group for CRUD Lambda"
  value       = aws_cloudwatch_log_group.crud.name
}
