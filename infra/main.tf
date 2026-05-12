# Main Infrastructure Configuration
# Defines all AWS resources for the Customer Management MVP

# ============================================================================
# DynamoDB Table
# ============================================================================

resource "aws_dynamodb_table" "customers" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "customer_id"

  attribute {
    name = "customer_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-table"
  }
}

# ============================================================================
# CloudWatch Log Groups
# ============================================================================

resource "aws_cloudwatch_log_group" "authorizer" {
  name              = "/aws/lambda/${var.project_name}-authorizer"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-authorizer-logs"
  }
}

resource "aws_cloudwatch_log_group" "crud" {
  name              = "/aws/lambda/${var.project_name}-crud"
  retention_in_days = var.log_retention_days

  tags = {
    Name = "${var.project_name}-crud-logs"
  }
}

# ============================================================================
# IAM Roles and Policies
# ============================================================================

# Authorizer Lambda IAM Role
resource "aws_iam_role" "authorizer_role" {
  name = "${var.project_name}-authorizer-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Authorizer Lambda CloudWatch Logs Policy - Using AWS Managed Policy
resource "aws_iam_role_policy_attachment" "authorizer_logs" {
  role       = aws_iam_role.authorizer_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CRUD Lambda IAM Role
resource "aws_iam_role" "crud_role" {
  name = "${var.project_name}-crud-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# CRUD Lambda CloudWatch Logs Policy - Using AWS Managed Policy
resource "aws_iam_role_policy_attachment" "crud_logs" {
  role       = aws_iam_role.crud_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# CRUD Lambda DynamoDB Policy - Using AWS Managed Policy
resource "aws_iam_role_policy_attachment" "crud_dynamodb" {
  role       = aws_iam_role.crud_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# ============================================================================
# Lambda Functions
# ============================================================================

# Authorizer Lambda Function
resource "aws_lambda_function" "authorizer" {
  function_name    = "${var.project_name}-authorizer"
  role             = aws_iam_role.authorizer_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = var.lambda_runtime
  filename         = "${path.module}/authorizer.zip"
  source_code_hash = filebase64sha256("${path.module}/authorizer.zip")
  memory_size      = var.authorizer_memory_size
  timeout          = var.authorizer_timeout

  environment {
    variables = {
      COGNITO_USER_POOL_ID = aws_cognito_user_pool.users.id
      COGNITO_CLIENT_ID    = aws_cognito_user_pool_client.client.id
      COGNITO_REGION       = var.aws_region
    }
  }

  tags = {
    Name = "${var.project_name}-authorizer"
  }
}

# CRUD Lambda Function
resource "aws_lambda_function" "crud" {
  function_name    = "${var.project_name}-crud"
  role             = aws_iam_role.crud_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = var.lambda_runtime
  filename         = "${path.module}/crud.zip"
  source_code_hash = filebase64sha256("${path.module}/crud.zip")
  memory_size      = var.crud_memory_size
  timeout          = var.crud_timeout

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.customers.name
      REGION     = var.aws_region
    }
  }

  tags = {
    Name = "${var.project_name}-crud"
  }
}

# ============================================================================
# Cognito User Pool
# ============================================================================

resource "aws_cognito_user_pool" "users" {
  name = "${var.project_name}-users"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }

  tags = {
    Name = "${var.project_name}-user-pool"
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name         = "${var.project_name}-client"
  user_pool_id = aws_cognito_user_pool.users.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  generate_secret = false

  # Token expiration configuration - 1 hour (3600 seconds)
  access_token_validity  = 1
  id_token_validity      = 1
  refresh_token_validity = 1
  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}

# ============================================================================
# API Gateway
# ============================================================================

resource "aws_api_gateway_rest_api" "customer_api" {
  name        = "${var.project_name}-api"
  description = "Customer Management REST API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.project_name}-api"
  }
}

# API Gateway Authorizer
resource "aws_api_gateway_authorizer" "lambda_authorizer" {
  name                             = "${var.project_name}-authorizer"
  rest_api_id                      = aws_api_gateway_rest_api.customer_api.id
  authorizer_uri                   = aws_lambda_function.authorizer.invoke_arn
  authorizer_credentials           = aws_iam_role.api_gateway_authorizer_role.arn
  type                             = "TOKEN"
  identity_source                  = "method.request.header.Authorization"
  authorizer_result_ttl_in_seconds = 300
}

# IAM Role for API Gateway to invoke Authorizer
resource "aws_iam_role" "api_gateway_authorizer_role" {
  name = "${var.project_name}-api-gateway-authorizer-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_gateway_authorizer_policy" {
  role       = aws_iam_role.api_gateway_authorizer_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
}

# /customers resource
resource "aws_api_gateway_resource" "customers" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id
  parent_id   = aws_api_gateway_rest_api.customer_api.root_resource_id
  path_part   = "customers"
}

# /customers/{customer_id} resource
resource "aws_api_gateway_resource" "customer_id" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id
  parent_id   = aws_api_gateway_resource.customers.id
  path_part   = "{customer_id}"
}

# POST /customers
resource "aws_api_gateway_method" "post_customers" {
  rest_api_id   = aws_api_gateway_rest_api.customer_api.id
  resource_id   = aws_api_gateway_resource.customers.id
  http_method   = "POST"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id
}

resource "aws_api_gateway_integration" "post_customers" {
  rest_api_id             = aws_api_gateway_rest_api.customer_api.id
  resource_id             = aws_api_gateway_resource.customers.id
  http_method             = aws_api_gateway_method.post_customers.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crud.invoke_arn
}

# GET /customers
resource "aws_api_gateway_method" "get_customers" {
  rest_api_id   = aws_api_gateway_rest_api.customer_api.id
  resource_id   = aws_api_gateway_resource.customers.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id
}

resource "aws_api_gateway_integration" "get_customers" {
  rest_api_id             = aws_api_gateway_rest_api.customer_api.id
  resource_id             = aws_api_gateway_resource.customers.id
  http_method             = aws_api_gateway_method.get_customers.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crud.invoke_arn
}

# OPTIONS /customers (CORS preflight)
resource "aws_api_gateway_method" "options_customers" {
  rest_api_id   = aws_api_gateway_rest_api.customer_api.id
  resource_id   = aws_api_gateway_resource.customers.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_customers" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id
  resource_id = aws_api_gateway_resource.customers.id
  http_method = aws_api_gateway_method.options_customers.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_customers" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id
  resource_id = aws_api_gateway_resource.customers.id
  http_method = aws_api_gateway_method.options_customers.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_customers" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id
  resource_id = aws_api_gateway_resource.customers.id
  http_method = aws_api_gateway_method.options_customers.http_method
  status_code = aws_api_gateway_method_response.options_customers.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [aws_api_gateway_integration.options_customers]
}

# GET /customers/{customer_id}
resource "aws_api_gateway_method" "get_customer" {
  rest_api_id   = aws_api_gateway_rest_api.customer_api.id
  resource_id   = aws_api_gateway_resource.customer_id.id
  http_method   = "GET"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id
}

resource "aws_api_gateway_integration" "get_customer" {
  rest_api_id             = aws_api_gateway_rest_api.customer_api.id
  resource_id             = aws_api_gateway_resource.customer_id.id
  http_method             = aws_api_gateway_method.get_customer.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crud.invoke_arn
}

# PUT /customers/{customer_id}
resource "aws_api_gateway_method" "put_customer" {
  rest_api_id   = aws_api_gateway_rest_api.customer_api.id
  resource_id   = aws_api_gateway_resource.customer_id.id
  http_method   = "PUT"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id
}

resource "aws_api_gateway_integration" "put_customer" {
  rest_api_id             = aws_api_gateway_rest_api.customer_api.id
  resource_id             = aws_api_gateway_resource.customer_id.id
  http_method             = aws_api_gateway_method.put_customer.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crud.invoke_arn
}

# DELETE /customers/{customer_id}
resource "aws_api_gateway_method" "delete_customer" {
  rest_api_id   = aws_api_gateway_rest_api.customer_api.id
  resource_id   = aws_api_gateway_resource.customer_id.id
  http_method   = "DELETE"
  authorization = "CUSTOM"
  authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id
}

resource "aws_api_gateway_integration" "delete_customer" {
  rest_api_id             = aws_api_gateway_rest_api.customer_api.id
  resource_id             = aws_api_gateway_resource.customer_id.id
  http_method             = aws_api_gateway_method.delete_customer.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.crud.invoke_arn
}

# OPTIONS /customers/{customer_id} (CORS preflight)
resource "aws_api_gateway_method" "options_customer_id" {
  rest_api_id   = aws_api_gateway_rest_api.customer_api.id
  resource_id   = aws_api_gateway_resource.customer_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_customer_id" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id
  resource_id = aws_api_gateway_resource.customer_id.id
  http_method = aws_api_gateway_method.options_customer_id.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_customer_id" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id
  resource_id = aws_api_gateway_resource.customer_id.id
  http_method = aws_api_gateway_method.options_customer_id.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options_customer_id" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id
  resource_id = aws_api_gateway_resource.customer_id.id
  http_method = aws_api_gateway_method.options_customer_id.http_method
  status_code = aws_api_gateway_method_response.options_customer_id.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [aws_api_gateway_integration.options_customer_id]
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_gateway_crud" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.crud.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.customer_api.execution_arn}/*/*"
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "prod" {
  rest_api_id = aws_api_gateway_rest_api.customer_api.id

  depends_on = [
    aws_api_gateway_integration.post_customers,
    aws_api_gateway_integration.get_customers,
    aws_api_gateway_integration.options_customers,
    aws_api_gateway_integration.get_customer,
    aws_api_gateway_integration.put_customer,
    aws_api_gateway_integration.delete_customer,
    aws_api_gateway_integration.options_customer_id
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.prod.id
  rest_api_id   = aws_api_gateway_rest_api.customer_api.id
  stage_name    = "prod"

  tags = {
    Name = "${var.project_name}-prod-stage"
  }
}
