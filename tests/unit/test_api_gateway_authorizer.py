"""
Unit tests for API Gateway Authorizer configuration.

Tests verify that the Lambda Authorizer is properly configured with:
- TOKEN type authorization
- Authorization header as identity source
- 300 second result TTL
- Proper IAM role and permissions

Requirements: 8.2, 8.3
"""

import re


def extract_resource_block(content, resource_type, resource_name):
    """Helper function to extract a Terraform resource block.
    
    Args:
        content: The full Terraform file content
        resource_type: The resource type (e.g., "aws_api_gateway_authorizer")
        resource_name: The resource name (e.g., "lambda_authorizer")
    
    Returns:
        The resource block content as a string
    """
    search_str = f'resource "{resource_type}" "{resource_name}"'
    start = content.find(search_str)
    if start == -1:
        return None
    
    # Find the opening brace
    block_start = content.find('{', start)
    if block_start == -1:
        return None
    
    # Find the matching closing brace
    brace_count = 0
    i = block_start
    while i < len(content):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[block_start:i+1]
        i += 1
    
    return None


def test_authorizer_resource_exists():
    """Test that API Gateway Authorizer resource is defined."""
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Verify authorizer resource exists
    assert 'resource "aws_api_gateway_authorizer" "lambda_authorizer"' in content


def test_authorizer_type_is_token():
    """Test that authorizer type is set to TOKEN.
    
    Requirement 8.2: The authorizer SHALL use TOKEN type for JWT validation.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    authorizer_block = extract_resource_block(content, "aws_api_gateway_authorizer", "lambda_authorizer")
    assert authorizer_block is not None, "Lambda authorizer resource not found"
    
    # Verify type is TOKEN
    assert 'type' in authorizer_block
    assert '"TOKEN"' in authorizer_block


def test_authorizer_identity_source():
    """Test that identity source is configured as Authorization header.
    
    Requirement 8.3: The authorizer SHALL extract tokens from the Authorization header.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    authorizer_block = extract_resource_block(content, "aws_api_gateway_authorizer", "lambda_authorizer")
    assert authorizer_block is not None, "Lambda authorizer resource not found"
    
    # Verify identity source is Authorization header
    assert 'identity_source' in authorizer_block
    assert 'method.request.header.Authorization' in authorizer_block


def test_authorizer_result_ttl():
    """Test that authorizer result TTL is set to 300 seconds.
    
    Requirement 8.3: The authorizer SHALL cache results for 300 seconds to improve performance.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    authorizer_block = extract_resource_block(content, "aws_api_gateway_authorizer", "lambda_authorizer")
    assert authorizer_block is not None, "Lambda authorizer resource not found"
    
    # Verify TTL is 300 seconds
    assert 'authorizer_result_ttl_in_seconds' in authorizer_block
    assert '= 300' in authorizer_block


def test_authorizer_uses_lambda_function():
    """Test that authorizer is configured to use the Lambda Authorizer function.
    
    Requirement 8.2: The authorizer SHALL invoke the Lambda Authorizer function.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    authorizer_block = extract_resource_block(content, "aws_api_gateway_authorizer", "lambda_authorizer")
    assert authorizer_block is not None, "Lambda authorizer resource not found"
    
    # Verify authorizer_uri references the Lambda function
    assert 'authorizer_uri' in authorizer_block
    assert 'aws_lambda_function.authorizer.invoke_arn' in authorizer_block


def test_authorizer_has_iam_role():
    """Test that authorizer has IAM role configured for invoking Lambda.
    
    Requirement 8.2: API Gateway SHALL have permissions to invoke the authorizer Lambda.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    authorizer_block = extract_resource_block(content, "aws_api_gateway_authorizer", "lambda_authorizer")
    assert authorizer_block is not None, "Lambda authorizer resource not found"
    
    # Verify authorizer_credentials references IAM role
    assert 'authorizer_credentials' in authorizer_block
    assert 'aws_iam_role.api_gateway_authorizer_role.arn' in authorizer_block


def test_api_gateway_authorizer_iam_role_exists():
    """Test that IAM role for API Gateway to invoke authorizer exists.
    
    Requirement 8.2: API Gateway SHALL have an IAM role with Lambda invoke permissions.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    role_block = extract_resource_block(content, "aws_iam_role", "api_gateway_authorizer_role")
    assert role_block is not None, "API Gateway authorizer IAM role not found"
    
    # Verify assume role policy allows API Gateway
    assert 'assume_role_policy' in role_block
    assert 'apigateway.amazonaws.com' in role_block


def test_api_gateway_authorizer_iam_policy_exists():
    """Test that IAM policy grants Lambda invoke permissions.
    
    Requirement 8.2: API Gateway SHALL have permission to invoke the authorizer Lambda.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    policy_block = extract_resource_block(content, "aws_iam_role_policy", "api_gateway_authorizer_policy")
    assert policy_block is not None, "API Gateway authorizer IAM policy not found"
    
    # Verify policy grants lambda:InvokeFunction
    assert 'lambda:InvokeFunction' in policy_block
    assert 'aws_lambda_function.authorizer.arn' in policy_block


def test_authorizer_attached_to_rest_api():
    """Test that authorizer is attached to the REST API.
    
    Requirement 8.2: The authorizer SHALL be associated with the Customer Management API.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    authorizer_block = extract_resource_block(content, "aws_api_gateway_authorizer", "lambda_authorizer")
    assert authorizer_block is not None, "Lambda authorizer resource not found"
    
    # Verify rest_api_id references the customer API
    assert 'rest_api_id' in authorizer_block
    assert 'aws_api_gateway_rest_api.customer_api.id' in authorizer_block


def test_all_protected_methods_use_authorizer():
    """Test that all API methods (except OPTIONS) use the authorizer.
    
    Requirement 8.2: All customer management endpoints SHALL require authentication.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Find all API Gateway methods
    method_pattern = r'resource "aws_api_gateway_method" "(\w+)" \{([^}]+)\}'
    methods = re.findall(method_pattern, content, re.DOTALL)
    
    protected_methods = []
    options_methods = []
    
    for method_name, method_block in methods:
        if 'options' in method_name.lower():
            options_methods.append(method_name)
            # OPTIONS methods should not require authorization
            assert 'authorization = "NONE"' in method_block, \
                f"OPTIONS method {method_name} should have authorization = NONE"
        else:
            protected_methods.append(method_name)
            # All other methods should use CUSTOM authorization
            assert 'authorization = "CUSTOM"' in method_block, \
                f"Method {method_name} should have authorization = CUSTOM"
            assert 'authorizer_id = aws_api_gateway_authorizer.lambda_authorizer.id' in method_block, \
                f"Method {method_name} should reference the lambda_authorizer"
    
    # Verify we found the expected methods
    assert len(protected_methods) >= 5, "Should have at least 5 protected methods (POST, GET, GET by ID, PUT, DELETE)"
    assert len(options_methods) >= 2, "Should have at least 2 OPTIONS methods for CORS"


def test_authorizer_configuration_complete():
    """Integration test verifying all authorizer components are properly configured.
    
    Requirements 8.2, 8.3: Complete authorizer setup with all required components.
    """
    with open('infra/main.tf', 'r') as f:
        content = f.read()
    
    # Verify all required components exist
    required_components = [
        'resource "aws_api_gateway_authorizer" "lambda_authorizer"',
        'resource "aws_iam_role" "api_gateway_authorizer_role"',
        'resource "aws_iam_role_policy" "api_gateway_authorizer_policy"',
        'type                             = "TOKEN"',
        'identity_source                  = "method.request.header.Authorization"',
        'authorizer_result_ttl_in_seconds = 300',
        'authorizer_uri                   = aws_lambda_function.authorizer.invoke_arn',
        'authorizer_credentials           = aws_iam_role.api_gateway_authorizer_role.arn'
    ]
    
    for component in required_components:
        assert component in content, f"Missing required component: {component}"
