"""Unit tests for modules/34_api_gateway. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

ApiGatewayStack = stack_class("34_api_gateway")


def _synth(config):
    app = cdk.App()
    stack = ApiGatewayStack(app, "TestApiGatewayStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_rest_api(config):
    template = _synth(config)
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_creates_exactly_one_get_method_with_mock_integration(config):
    """The whole point of this module: no Lambda/backend, just MockIntegration."""
    template = _synth(config)
    template.resource_count_is("AWS::ApiGateway::Method", 1)
    template.has_resource_properties(
        "AWS::ApiGateway::Method",
        {
            "HttpMethod": "GET",
            "Integration": Match.object_like({"Type": "MOCK"}),
        },
    )


def test_method_returns_a_200_response(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ApiGateway::Method",
        {
            "MethodResponses": Match.array_with(
                [Match.object_like({"StatusCode": "200"})]
            )
        },
    )


def test_rest_api_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::ApiGateway::RestApi", {"Tags": Match.array_with([tag])}
        )
