"""Unit tests for modules/04_internet_gateway. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

InternetGatewayStack = stack_class("04_internet_gateway")


def _synth(config):
    app = cdk.App()
    stack = InternetGatewayStack(app, "TestInternetGatewayStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_internet_gateway(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::InternetGateway", 1)


def test_creates_exactly_one_gateway_attachment(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::VPCGatewayAttachment", 1)


def test_default_route_targets_the_internet_gateway(config):
    template = _synth(config)
    routes = template.find_resources("AWS::EC2::Route")
    assert len(routes) == 1
    (route,) = routes.values()
    assert route["Properties"]["DestinationCidrBlock"] == "0.0.0.0/0"
    assert route["Properties"]["GatewayId"] == {"Ref": "InternetGateway"}


def test_default_route_depends_on_the_gateway_attachment(config):
    """The whole point of this module: CloudFormation cannot infer this
    dependency from CfnRoute's own properties, so stack.py adds it
    explicitly with add_resource_dependency() - see its class docstring."""
    template = _synth(config)
    routes = template.find_resources("AWS::EC2::Route")
    (route,) = routes.values()
    assert "InternetGatewayAttachment" in route.get("DependsOn", [])


def test_internet_gateway_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::EC2::InternetGateway", {"Tags": Match.array_with([tag])}
        )
