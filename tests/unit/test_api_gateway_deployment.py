"""
Unit tests for API Gateway deployment and stage configuration.

Tests verify that:
- Deployment resource depends on all API methods
- Stage is named "prod"
- API endpoint output is configured

Requirements: 9.3
"""

import re
import unittest


class TestAPIGatewayDeployment(unittest.TestCase):
    """Test API Gateway deployment and stage configuration."""

    def setUp(self):
        """Load Terraform configuration."""
        with open('infra/main.tf', 'r') as f:
            self.main_tf_content = f.read()
        
        with open('infra/outputs.tf', 'r') as f:
            self.outputs_tf_content = f.read()

    def test_deployment_resource_exists(self):
        """Test that API Gateway deployment resource is defined."""
        self.assertIn(
            'resource "aws_api_gateway_deployment" "prod"',
            self.main_tf_content,
            "API Gateway deployment resource should be defined"
        )

    def test_deployment_depends_on_all_methods(self):
        """Test that deployment depends on all API method integrations."""
        # Find the deployment resource
        deployment_match = re.search(
            r'resource "aws_api_gateway_deployment" "prod" \{.*?depends_on = \[(.*?)\]',
            self.main_tf_content,
            re.DOTALL
        )
        
        self.assertIsNotNone(
            deployment_match,
            "Deployment resource should have depends_on block"
        )
        
        depends_on_content = deployment_match.group(1)
        
        # Verify all required integrations are in depends_on
        required_integrations = [
            'aws_api_gateway_integration.post_customers',
            'aws_api_gateway_integration.get_customers',
            'aws_api_gateway_integration.options_customers',
            'aws_api_gateway_integration.get_customer',
            'aws_api_gateway_integration.put_customer',
            'aws_api_gateway_integration.delete_customer',
            'aws_api_gateway_integration.options_customer_id'
        ]
        
        for integration in required_integrations:
            self.assertIn(
                integration,
                depends_on_content,
                f"Deployment should depend on {integration}"
            )

    def test_deployment_has_create_before_destroy(self):
        """Test that deployment has create_before_destroy lifecycle."""
        deployment_match = re.search(
            r'resource "aws_api_gateway_deployment" "prod" \{.*?lifecycle \{.*?create_before_destroy = true.*?\}',
            self.main_tf_content,
            re.DOTALL
        )
        
        self.assertIsNotNone(
            deployment_match,
            "Deployment should have create_before_destroy lifecycle"
        )

    def test_stage_resource_exists(self):
        """Test that API Gateway stage resource is defined."""
        self.assertIn(
            'resource "aws_api_gateway_stage" "prod"',
            self.main_tf_content,
            "API Gateway stage resource should be defined"
        )

    def test_stage_name_is_prod(self):
        """Test that stage name is 'prod'."""
        stage_match = re.search(
            r'resource "aws_api_gateway_stage" "prod" \{.*?stage_name\s*=\s*"([^"]+)"',
            self.main_tf_content,
            re.DOTALL
        )
        
        self.assertIsNotNone(
            stage_match,
            "Stage resource should have stage_name attribute"
        )
        
        stage_name = stage_match.group(1)
        self.assertEqual(
            stage_name,
            "prod",
            "Stage name should be 'prod'"
        )

    def test_stage_references_deployment(self):
        """Test that stage references the deployment resource."""
        stage_match = re.search(
            r'resource "aws_api_gateway_stage" "prod" \{.*?deployment_id\s*=\s*([^\n]+)',
            self.main_tf_content,
            re.DOTALL
        )
        
        self.assertIsNotNone(
            stage_match,
            "Stage should have deployment_id attribute"
        )
        
        deployment_id = stage_match.group(1).strip()
        self.assertIn(
            'aws_api_gateway_deployment.prod.id',
            deployment_id,
            "Stage should reference deployment resource"
        )

    def test_stage_references_rest_api(self):
        """Test that stage references the REST API resource."""
        stage_match = re.search(
            r'resource "aws_api_gateway_stage" "prod" \{.*?rest_api_id\s*=\s*([^\n]+)',
            self.main_tf_content,
            re.DOTALL
        )
        
        self.assertIsNotNone(
            stage_match,
            "Stage should have rest_api_id attribute"
        )
        
        rest_api_id = stage_match.group(1).strip()
        self.assertIn(
            'aws_api_gateway_rest_api.customer_api.id',
            rest_api_id,
            "Stage should reference REST API resource"
        )

    def test_api_endpoint_output_exists(self):
        """Test that API endpoint output is defined."""
        self.assertIn(
            'output "api_endpoint"',
            self.outputs_tf_content,
            "API endpoint output should be defined"
        )

    def test_api_endpoint_output_uses_stage_invoke_url(self):
        """Test that API endpoint output uses stage invoke URL."""
        output_match = re.search(
            r'output "api_endpoint" \{.*?value\s*=\s*([^\n]+)',
            self.outputs_tf_content,
            re.DOTALL
        )
        
        self.assertIsNotNone(
            output_match,
            "API endpoint output should have value attribute"
        )
        
        output_value = output_match.group(1).strip()
        self.assertIn(
            'aws_api_gateway_stage.prod.invoke_url',
            output_value,
            "API endpoint output should use stage invoke URL"
        )

    def test_deployment_references_rest_api(self):
        """Test that deployment references the REST API resource."""
        deployment_match = re.search(
            r'resource "aws_api_gateway_deployment" "prod" \{.*?rest_api_id\s*=\s*([^\n]+)',
            self.main_tf_content,
            re.DOTALL
        )
        
        self.assertIsNotNone(
            deployment_match,
            "Deployment should have rest_api_id attribute"
        )
        
        rest_api_id = deployment_match.group(1).strip()
        self.assertIn(
            'aws_api_gateway_rest_api.customer_api.id',
            rest_api_id,
            "Deployment should reference REST API resource"
        )


if __name__ == '__main__':
    unittest.main()
