"""
Unit tests for API Gateway /customers/{customer_id} resource configuration.

Tests verify that the /customers/{customer_id} resource is properly configured with:
- Path parameter definition
- GET, PUT, DELETE methods with Lambda proxy integration
- Authorizer attached to all methods
- CORS enabled for all methods

Validates Requirements: 8.1, 8.2, 8.4, 8.5
"""

import re


def test_customer_id_resource_exists():
    """Test that /customers/{customer_id} resource is defined."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for customer_id resource definition
    assert 'resource "aws_api_gateway_resource" "customer_id"' in content
    
    # Verify path parameter is correctly defined
    assert 'path_part   = "{customer_id}"' in content
    
    # Verify parent is /customers resource
    resource_match = re.search(
        r'resource "aws_api_gateway_resource" "customer_id".*?parent_id\s*=\s*aws_api_gateway_resource\.customers\.id',
        content,
        re.DOTALL
    )
    
    assert resource_match is not None


def test_get_customer_method_exists():
    """Test that GET method is defined for /customers/{customer_id}."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for GET method definition
    assert 'resource "aws_api_gateway_method" "get_customer"' in content
    
    # Find GET method definition
    get_match = re.search(
        r'resource "aws_api_gateway_method" "get_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert get_match is not None
    get_content = get_match.group(1)
    
    # Verify it's on the customer_id resource
    assert 'resource_id   = aws_api_gateway_resource.customer_id.id' in get_content
    # Verify HTTP method
    assert 'http_method   = "GET"' in get_content


def test_get_customer_has_authorizer():
    """Test that GET /customers/{customer_id} method has authorizer attached."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find GET method definition
    get_match = re.search(
        r'resource "aws_api_gateway_method" "get_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert get_match is not None
    get_content = get_match.group(1)
    
    # Verify authorizer is attached
    assert 'authorization = "CUSTOM"' in get_content
    assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in get_content


def test_get_customer_has_lambda_proxy_integration():
    """Test that GET /customers/{customer_id} has Lambda proxy integration to CRUD Lambda."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find GET integration definition
    get_integration_match = re.search(
        r'resource "aws_api_gateway_integration" "get_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert get_integration_match is not None
    integration_content = get_integration_match.group(1)
    
    # Verify Lambda proxy integration
    assert 'type                    = "AWS_PROXY"' in integration_content
    # Verify it points to CRUD Lambda
    assert 'uri                     = aws_lambda_function.crud.invoke_arn' in integration_content
    # Verify integration HTTP method is POST (required for Lambda proxy)
    assert 'integration_http_method = "POST"' in integration_content


def test_put_customer_method_exists():
    """Test that PUT method is defined for /customers/{customer_id}."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for PUT method definition
    assert 'resource "aws_api_gateway_method" "put_customer"' in content
    
    # Find PUT method definition
    put_match = re.search(
        r'resource "aws_api_gateway_method" "put_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert put_match is not None
    put_content = put_match.group(1)
    
    # Verify it's on the customer_id resource
    assert 'resource_id   = aws_api_gateway_resource.customer_id.id' in put_content
    # Verify HTTP method
    assert 'http_method   = "PUT"' in put_content


def test_put_customer_has_authorizer():
    """Test that PUT /customers/{customer_id} method has authorizer attached."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find PUT method definition
    put_match = re.search(
        r'resource "aws_api_gateway_method" "put_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert put_match is not None
    put_content = put_match.group(1)
    
    # Verify authorizer is attached
    assert 'authorization = "CUSTOM"' in put_content
    assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in put_content


def test_put_customer_has_lambda_proxy_integration():
    """Test that PUT /customers/{customer_id} has Lambda proxy integration to CRUD Lambda."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find PUT integration definition
    put_integration_match = re.search(
        r'resource "aws_api_gateway_integration" "put_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert put_integration_match is not None
    integration_content = put_integration_match.group(1)
    
    # Verify Lambda proxy integration
    assert 'type                    = "AWS_PROXY"' in integration_content
    # Verify it points to CRUD Lambda
    assert 'uri                     = aws_lambda_function.crud.invoke_arn' in integration_content
    # Verify integration HTTP method is POST (required for Lambda proxy)
    assert 'integration_http_method = "POST"' in integration_content


def test_delete_customer_method_exists():
    """Test that DELETE method is defined for /customers/{customer_id}."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for DELETE method definition
    assert 'resource "aws_api_gateway_method" "delete_customer"' in content
    
    # Find DELETE method definition
    delete_match = re.search(
        r'resource "aws_api_gateway_method" "delete_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert delete_match is not None
    delete_content = delete_match.group(1)
    
    # Verify it's on the customer_id resource
    assert 'resource_id   = aws_api_gateway_resource.customer_id.id' in delete_content
    # Verify HTTP method
    assert 'http_method   = "DELETE"' in delete_content


def test_delete_customer_has_authorizer():
    """Test that DELETE /customers/{customer_id} method has authorizer attached."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find DELETE method definition
    delete_match = re.search(
        r'resource "aws_api_gateway_method" "delete_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert delete_match is not None
    delete_content = delete_match.group(1)
    
    # Verify authorizer is attached
    assert 'authorization = "CUSTOM"' in delete_content
    assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in delete_content


def test_delete_customer_has_lambda_proxy_integration():
    """Test that DELETE /customers/{customer_id} has Lambda proxy integration to CRUD Lambda."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find DELETE integration definition
    delete_integration_match = re.search(
        r'resource "aws_api_gateway_integration" "delete_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert delete_integration_match is not None
    integration_content = delete_integration_match.group(1)
    
    # Verify Lambda proxy integration
    assert 'type                    = "AWS_PROXY"' in integration_content
    # Verify it points to CRUD Lambda
    assert 'uri                     = aws_lambda_function.crud.invoke_arn' in integration_content
    # Verify integration HTTP method is POST (required for Lambda proxy)
    assert 'integration_http_method = "POST"' in integration_content


def test_customer_id_cors_enabled():
    """Test that CORS is enabled for /customers/{customer_id} resource."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for OPTIONS method (CORS preflight)
    assert 'resource "aws_api_gateway_method" "options_customer_id"' in content
    
    # Find OPTIONS method definition
    options_match = re.search(
        r'resource "aws_api_gateway_method" "options_customer_id" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert options_match is not None
    options_content = options_match.group(1)
    
    # Verify it's on the customer_id resource
    assert 'resource_id   = aws_api_gateway_resource.customer_id.id' in options_content
    # Verify HTTP method
    assert 'http_method   = "OPTIONS"' in options_content
    # Verify no authorization for OPTIONS (CORS preflight)
    assert 'authorization = "NONE"' in options_content


def test_customer_id_cors_integration():
    """Test that CORS integration is configured for /customers/{customer_id}."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for OPTIONS integration
    assert 'resource "aws_api_gateway_integration" "options_customer_id"' in content
    
    # Find OPTIONS integration definition
    options_integration_match = re.search(
        r'resource "aws_api_gateway_integration" "options_customer_id" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert options_integration_match is not None
    integration_content = options_integration_match.group(1)
    
    # Verify MOCK integration for CORS
    assert 'type        = "MOCK"' in integration_content


def test_customer_id_cors_headers():
    """Test that CORS headers are properly configured for /customers/{customer_id}."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find OPTIONS integration response
    options_response_match = re.search(
        r'resource "aws_api_gateway_integration_response" "options_customer_id" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert options_response_match is not None
    response_content = options_response_match.group(1)
    
    # Verify CORS headers are present
    assert '"method.response.header.Access-Control-Allow-Headers" = "\'Content-Type,Authorization\'"' in response_content
    assert '"method.response.header.Access-Control-Allow-Origin"  = "\'*\'"' in response_content
    # Verify methods include GET, PUT, DELETE, OPTIONS
    assert '"method.response.header.Access-Control-Allow-Methods" = "\'GET,PUT,DELETE,OPTIONS\'"' in response_content


def test_deployment_includes_customer_id_methods():
    """Test that API Gateway deployment depends on all /customers/{customer_id} methods."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find the deployment resource
    deployment_match = re.search(
        r'resource "aws_api_gateway_deployment" "prod" \{.*?depends_on = \[(.*?)\]',
        content,
        re.DOTALL
    )
    
    assert deployment_match is not None
    depends_on = deployment_match.group(1)
    
    # Check that all customer_id integrations are in depends_on
    assert 'aws_api_gateway_integration.get_customer' in depends_on
    assert 'aws_api_gateway_integration.put_customer' in depends_on
    assert 'aws_api_gateway_integration.delete_customer' in depends_on
    assert 'aws_api_gateway_integration.options_customer_id' in depends_on


def test_all_methods_use_same_crud_lambda():
    """Test that all methods (GET, PUT, DELETE) integrate with the same CRUD Lambda."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find all three integration definitions
    get_integration = re.search(
        r'resource "aws_api_gateway_integration" "get_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    put_integration = re.search(
        r'resource "aws_api_gateway_integration" "put_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    delete_integration = re.search(
        r'resource "aws_api_gateway_integration" "delete_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert get_integration is not None
    assert put_integration is not None
    assert delete_integration is not None
    
    # Verify all point to the same Lambda
    assert 'uri                     = aws_lambda_function.crud.invoke_arn' in get_integration.group(1)
    assert 'uri                     = aws_lambda_function.crud.invoke_arn' in put_integration.group(1)
    assert 'uri                     = aws_lambda_function.crud.invoke_arn' in delete_integration.group(1)


def test_all_methods_use_same_authorizer():
    """Test that all methods (GET, PUT, DELETE) use the same Lambda Authorizer."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find all three method definitions
    get_method = re.search(
        r'resource "aws_api_gateway_method" "get_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    put_method = re.search(
        r'resource "aws_api_gateway_method" "put_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    delete_method = re.search(
        r'resource "aws_api_gateway_method" "delete_customer" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert get_method is not None
    assert put_method is not None
    assert delete_method is not None
    
    # Verify all use the same authorizer
    assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in get_method.group(1)
    assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in put_method.group(1)
    assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in delete_method.group(1)
