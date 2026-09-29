"""Module 34 - API Gateway (REST): a backend-free REST API using MockIntegration.

AWS docs used while writing this module:
- RestApi construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RestApi.html
- MockIntegration construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/MockIntegration.html
- IntegrationResponse construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/IntegrationResponse.html
- MethodResponse construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/MethodResponse.html
- Set up a mock integration: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-create-api-as-simple-proxy-for-lambda.html
- API Gateway REST APIs vs. HTTP APIs: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html

This module deliberately uses `aws_cdk.aws_apigateway` (REST APIs), the
stable module for API Gateway in aws-cdk-lib - not `aws_cdk.aws_apigatewayv2`
(HTTP APIs), whose Lambda/HTTP integrations packages have historically lived
in separate alpha (`-alpha`) packages this repository never uses (see
CLAUDE.md section 4). `apigateway.MockIntegration` was confirmed via the API
reference page above before writing this module.

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_apigateway as apigateway
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "ApiGatewayStack"


class ApiGatewayStack(Stack):
    """A REST API with one GET method backed by MockIntegration - no Lambda, no backend.

    `apigateway.MockIntegration` is a real, documented way to test API
    Gateway's routing, request/response mapping, and deployment mechanics
    without any backend at all: API Gateway itself returns a canned
    response, built from `request_templates` (what API Gateway pretends the
    "backend" received) and `integration_responses` (what it sends back),
    matched to the method's declared `method_responses`. This makes the
    whole module deployable and testable with zero other AWS resources -
    modules 17 (Lambda) and 35 (a real backend integration, if added later)
    show a real backend behind API Gateway instead.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: AppConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        apply_standard_tags(self, tags=config.to_standard_tags())

        api_name = resource_name(config.product, config.environment, "apigateway", "demo")
        self.rest_api = apigateway.RestApi(
            self,
            "RestApi",
            rest_api_name=api_name,
            description="Backend-free demo REST API using MockIntegration - see modules/34_api_gateway/README.md.",
        )
        apply_name_tag(self.rest_api, api_name)

        mock_integration = apigateway.MockIntegration(
            integration_responses=[
                apigateway.IntegrationResponse(
                    status_code="200",
                    response_templates={
                        "application/json": '{"message": "hello from a MockIntegration, no backend involved"}'
                    },
                )
            ],
            request_templates={"application/json": '{"statusCode": 200}'},
        )

        demo_resource = self.rest_api.root.add_resource("demo")
        demo_resource.add_method(
            "GET",
            mock_integration,
            method_responses=[apigateway.MethodResponse(status_code="200")],
        )


STACK_CLASS = ApiGatewayStack
