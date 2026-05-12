# Copyright (c) 2024 AnyCompany. All rights reserved.
# Lambda Authorizer for Customer Management API
# Validates JWT tokens issued by Cognito User Pool

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any
import boto3
from jose import jwt, jwk
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
import requests

# Configure logging with JSON formatter
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def log_json(level: str, message: str, **kwargs):
    """
    Log structured JSON message.
    
    Args:
        level: Log level (INFO, WARNING, ERROR)
        message: Log message
        **kwargs: Additional fields to include in JSON log
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'level': level,
        'message': message,
        **kwargs
    }
    
    log_message = json.dumps(log_entry)
    
    if level == 'INFO':
        logger.info(log_message)
    elif level == 'WARNING':
        logger.warning(log_message)
    elif level == 'ERROR':
        logger.error(log_message)
    else:
        logger.info(log_message)

# Environment variables
COGNITO_REGION = os.environ.get('COGNITO_REGION', 'us-east-1')
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID', '')

# Cache for Cognito public keys
_cognito_keys_cache = None


def get_cognito_public_keys():
    """
    Retrieve Cognito User Pool public keys (JWKS).
    
    Returns:
        list: List of public keys from Cognito JWKS endpoint
    """
    global _cognito_keys_cache
    
    if _cognito_keys_cache is not None:
        return _cognito_keys_cache
    
    # Construct JWKS URL
    jwks_url = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json'
    
    try:
        response = requests.get(jwks_url, timeout=5)
        response.raise_for_status()
        jwks = response.json()
        _cognito_keys_cache = jwks.get('keys', [])
        log_json('INFO', 'Retrieved Cognito public keys', key_count=len(_cognito_keys_cache))
        return _cognito_keys_cache
    except Exception as e:
        log_json('ERROR', 'Failed to retrieve Cognito public keys', error=str(e))
        raise


def extract_token(authorization_header: str) -> str:
    """
    Extract JWT token from 'Bearer <token>' format.
    
    Args:
        authorization_header: Authorization header value
    
    Returns:
        str: Extracted JWT token
    
    Raises:
        ValueError: If token format is invalid
    """
    if not authorization_header:
        raise ValueError("Missing authentication token")
    
    parts = authorization_header.split()
    
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise ValueError("Invalid token format. Expected 'Bearer <token>'")
    
    return parts[1]


def verify_token_signature(token: str, cognito_keys: list) -> Dict[str, Any]:
    """
    Verify JWT signature against Cognito public keys.
    
    Args:
        token: JWT token string
        cognito_keys: List of Cognito public keys from JWKS
    
    Returns:
        dict: Decoded token claims
    
    Raises:
        JWTError: If token signature is invalid
    """
    # Get the key ID from token header
    try:
        headers = jwt.get_unverified_headers(token)
        kid = headers.get('kid')
        
        if not kid:
            raise JWTError("Token missing 'kid' in header")
        
        # Find the matching public key
        key = None
        for cognito_key in cognito_keys:
            if cognito_key.get('kid') == kid:
                key = cognito_key
                break
        
        if not key:
            raise JWTError(f"Public key not found for kid: {kid}")
        
        # Verify and decode the token
        # Construct the expected issuer
        issuer = f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
        
        # Get the expected audience (Cognito Client ID) from environment variable
        # For ID tokens, the audience is the Cognito Client ID
        expected_audience = os.environ.get('COGNITO_CLIENT_ID', '')
        
        claims = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            issuer=issuer,
            audience=expected_audience,
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_iss': True,
                'verify_aud': True
            }
        )
        
        return claims
        
    except ExpiredSignatureError:
        log_json('WARNING', 'Token validation failed', reason='expired')
        raise JWTError("Token has expired")
    except JWTClaimsError as e:
        log_json('WARNING', 'Token validation failed', reason='claims_validation_failed', error=str(e))
        raise JWTError(f"Token claims validation failed: {str(e)}")
    except JWTError as e:
        log_json('WARNING', 'Token validation failed', reason='signature_verification_failed', error=str(e))
        raise
    except Exception as e:
        log_json('ERROR', 'Token validation failed', reason='unexpected_error', error=str(e))
        raise JWTError(f"Token verification failed: {str(e)}")


def validate_token_expiration(token_claims: dict) -> bool:
    """
    Check if token is expired based on 'exp' claim.
    
    Args:
        token_claims: Decoded JWT claims
    
    Returns:
        bool: True if token is valid (not expired), False otherwise
    """
    exp = token_claims.get('exp')
    
    if not exp:
        log_json('WARNING', 'Token validation failed', reason='missing_exp_claim')
        return False
    
    current_time = datetime.utcnow().timestamp()
    
    if current_time >= exp:
        log_json('WARNING', 'Token validation failed', reason='expired', current_time=current_time, expiration=exp)
        return False
    
    return True


def extract_user_identity(token_claims: dict) -> Dict[str, str]:
    """
    Extract user identifier from token claims.
    
    Args:
        token_claims: Decoded JWT claims
    
    Returns:
        dict: User identity information containing sub, username, and email
    """
    user_identity = {
        'sub': token_claims.get('sub', ''),
        'username': token_claims.get('cognito:username', token_claims.get('username', '')),
        'email': token_claims.get('email', '')
    }
    
    log_json('INFO', 'User identity extracted', user_id=user_identity['sub'], username=user_identity['username'])
    
    return user_identity


def generate_policy(principal_id: str, effect: str, resource: str, context: Dict[str, str] = None) -> dict:
    """
    Generate IAM policy document for API Gateway.
    
    Args:
        principal_id: User identifier
        effect: 'Allow' or 'Deny'
        resource: API Gateway method ARN
        context: Optional context to pass to downstream Lambda
    
    Returns:
        dict: IAM policy document
    """
    # Extract the API Gateway ARN prefix and create a wildcard policy
    # This allows the user to access all methods in the API, not just the one they called
    # Format: arn:aws:execute-api:region:account-id:api-id/stage/method/resource
    # We want: arn:aws:execute-api:region:account-id:api-id/*
    resource_parts = resource.split('/')
    if len(resource_parts) >= 2:
        # Create wildcard resource: arn:aws:execute-api:region:account-id:api-id/*
        wildcard_resource = resource_parts[0] + '/*'
    else:
        # Fallback to exact resource if parsing fails
        wildcard_resource = resource
    
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': wildcard_resource
                }
            ]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy


def lambda_handler(event, context):
    """
    Lambda Authorizer handler for API Gateway.
    
    Args:
        event: API Gateway authorizer event containing:
            - authorizationToken: Bearer token from Authorization header
            - methodArn: ARN of the API Gateway method being invoked
        context: Lambda context object
    
    Returns:
        IAM policy document with Allow or Deny effect
    """
    method_arn = event.get('methodArn', '')
    
    try:
        # Log the authorization attempt
        log_json('INFO', 'Authentication attempt started', method_arn=method_arn)
        
        # Extract token from Authorization header
        authorization_header = event.get('authorizationToken', '')
        
        try:
            token = extract_token(authorization_header)
        except ValueError as e:
            # Log authentication failure - missing token
            log_json(
                'WARNING',
                'Authentication failed',
                validation_result='denied',
                reason='missing_token',
                error_message=str(e),
                user_identity=None
            )
            # Return Deny policy with 401 context for missing token
            return generate_policy(
                'user',
                'Deny',
                method_arn,
                {
                    'error': 'Unauthorized',
                    'message': 'Missing authentication token',
                    'statusCode': '401'
                }
            )
        
        # Get Cognito public keys
        cognito_keys = get_cognito_public_keys()
        
        # Verify token signature and decode claims
        try:
            token_claims = verify_token_signature(token, cognito_keys)
        except JWTError as e:
            # Log authentication failure - invalid token
            log_json(
                'WARNING',
                'Authentication failed',
                validation_result='denied',
                reason='invalid_or_expired_token',
                error_message=str(e),
                user_identity=None
            )
            # Return Deny policy with 403 context for invalid/expired token
            return generate_policy(
                'user',
                'Deny',
                method_arn,
                {
                    'error': 'Forbidden',
                    'message': 'Invalid or expired token',
                    'statusCode': '403'
                }
            )
        
        # Additional expiration validation (redundant with jwt.decode but explicit)
        if not validate_token_expiration(token_claims):
            # Log authentication failure - expired token
            log_json(
                'WARNING',
                'Authentication failed',
                validation_result='denied',
                reason='token_expired',
                error_message='Token expiration validation failed',
                user_identity=None
            )
            return generate_policy(
                'user',
                'Deny',
                method_arn,
                {
                    'error': 'Forbidden',
                    'message': 'Invalid or expired token',
                    'statusCode': '403'
                }
            )
        
        # Extract user identity
        user_identity = extract_user_identity(token_claims)
        
        # Log successful authentication
        log_json(
            'INFO',
            'Authentication successful',
            validation_result='allowed',
            user_identity={
                'user_id': user_identity['sub'],
                'username': user_identity['username'],
                'email': user_identity['email']
            }
        )
        
        # Return Allow policy with user context
        return generate_policy(
            user_identity['sub'],
            'Allow',
            method_arn,
            {
                'sub': user_identity['sub'],
                'username': user_identity['username'],
                'email': user_identity['email']
            }
        )
        
    except Exception as e:
        # Log unexpected errors
        log_json(
            'ERROR',
            'Authentication failed',
            validation_result='denied',
            reason='unexpected_error',
            error_message=str(e),
            user_identity=None
        )
        
        # Return Deny policy for unexpected errors
        return generate_policy(
            'user',
            'Deny',
            method_arn,
            {
                'error': 'Forbidden',
                'message': 'Invalid or expired token',
                'statusCode': '403'
            }
        )
