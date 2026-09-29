"""Unit tests for modules/05_nat_gateway. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

NatGatewayStack = stack_class("05_nat_gateway")


def _synth(config):
    app = cdk.App()
    stack = NatGatewayStack(app, "TestNatGatewayStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_nat_gateway(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::NatGateway", 1)


def test_creates_exactly_one_elastic_ip(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::EIP", 1)


def test_nat_gateway_uses_the_elastic_ips_allocation(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::EC2::NatGateway",
        {"AllocationId": {"Fn::GetAtt": ["NatElasticIp", "AllocationId"]}},
    )


def test_private_subnet_default_route_targets_the_nat_gateway(config):
    """The whole point of this module: the private subnet's outbound route
    points at the NAT Gateway, not directly at an Internet Gateway."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::EC2::Route",
        {
            "DestinationCidrBlock": "0.0.0.0/0",
            "NatGatewayId": {"Ref": "NatGateway"},
        },
    )


def test_nat_gateway_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::EC2::NatGateway", {"Tags": Match.array_with([tag])}
        )
