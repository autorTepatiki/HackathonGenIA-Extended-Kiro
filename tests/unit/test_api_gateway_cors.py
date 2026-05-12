"""
Unit tests for API Gateway CORS configuration.

Tests verify that CORS is properly configured for all API Gateway resources.
"""

import re


def test_cors_options_method_for_customers_resource():
    """Test that OPTIONS method is defined for /customers resource."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for OPTIONS method on /customers
    assert 'resource "aws_api_gateway_method" "options_customers"' in content
    assert 'http_method   = "OPTIONS"' in content
    assert 'authorization = "NONE"' in content


def test_cors_options_method_for_customer_id_resource():
    """Test that OPTIONS method is defined for /customers/{customer_id} resource."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for OPTIONS method on /customers/{customer_id}
    assert 'resource "aws_api_gateway_method" "options_customer_id"' in content


def test_cors_integration_for_customers():
    """Test that CORS integration is configured for /customers resource."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for OPTIONS integration
    assert 'resource "aws_api_gateway_integration" "options_customers"' in content
    assert 'type        = "MOCK"' in content


def test_cors_integration_for_customer_id():
    """Test that CORS integration is configured for /customers/{customer_id} resource."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for OPTIONS integration
    assert 'resource "aws_api_gateway_integration" "options_customer_id"' in content


def test_cors_headers_for_customers():
    """Test that CORS headers are properly configured for /customers resource."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for CORS headers in integration response
    assert '"method.response.header.Access-Control-Allow-Headers" = "\'Content-Type,Authorization\'"' in content
    assert '"method.response.header.Access-Control-Allow-Methods" = "\'GET,POST,OPTIONS\'"' in content
    assert '"method.response.header.Access-Control-Allow-Origin"  = "\'*\'"' in content


def test_cors_headers_for_customer_id():
    """Test that CORS headers are properly configured for /customers/{customer_id} resource."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Check for CORS headers in integration response
    assert '"method.response.header.Access-Control-Allow-Methods" = "\'GET,PUT,DELETE,OPTIONS\'"' in content


def test_deployment_depends_on_cors_integrations():
    """Test that API Gateway deployment depends on CORS integrations."""
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
    
    # Check that CORS integrations are in depends_on
    assert 'aws_api_gateway_integration.options_customers' in depends_on
    assert 'aws_api_gateway_integration.options_customer_id' in depends_on


def test_post_method_has_authorizer():
    """Test that POST /customers method has authorizer attached."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find POST method definition
    post_match = re.search(
        r'resource "aws_api_gateway_method" "post_customers" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert post_match is not None
    post_content = post_match.group(1)
    
    assert 'authorization = "CUSTOM"' in post_content
    assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in post_content


def test_get_method_has_authorizer():
    """Test that GET /customers method has authorizer attached."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find GET method definition
    get_match = re.search(
        r'resource "aws_api_gateway_method" "get_customers" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert get_match is not None
    get_content = get_match.group(1)
    
    assert 'authorization = "CUSTOM"' in get_content
    assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in get_content


def test_post_method_has_lambda_proxy_integration():
    """Test that POST /customers has Lambda proxy integration."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find POST integration definition
    post_integration_match = re.search(
        r'resource "aws_api_gateway_integration" "post_customers" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert post_integration_match is not None
    integration_content = post_integration_match.group(1)
    
    assert 'type                    = "AWS_PROXY"' in integration_content
    assert 'uri                     = aws_lambda_function.crud.invoke_arn' in integration_content


def test_get_method_has_lambda_proxy_integration():
    """Test that GET /customers has Lambda proxy integration."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find GET integration definition
    get_integration_match = re.search(
        r'resource "aws_api_gateway_integration" "get_customers" \{(.*?)\}',
        content,
        re.DOTALL
    )
    
    assert get_integration_match is not None
    integration_content = get_integration_match.group(1)
    
    assert 'type                    = "AWS_PROXY"' in integration_content
    assert 'uri                     = aws_lambda_function.crud.invoke_arn' in integration_content
