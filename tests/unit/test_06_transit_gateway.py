"""Unit tests for modules/06_transit_gateway. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

TransitGatewayStack = stack_class("06_transit_gateway")


def _synth(config):
    app = cdk.App()
    stack = TransitGatewayStack(app, "TestTransitGatewayStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_transit_gateway(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::TransitGateway", 1)


def test_creates_two_vpc_attachments(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::TransitGatewayVpcAttachment", 2)


def test_creates_one_explicit_route_table_with_two_associations(config):
    """The whole point of this module: CfnTransitGateway exposes no
    attribute for AWS's auto-created default route table, so stack.py
    creates its own explicit one and associates both attachments with it -
    see the class docstring in stack.py."""
    template = _synth(config)
    template.resource_count_is("AWS::EC2::TransitGatewayRouteTable", 1)
    template.resource_count_is("AWS::EC2::TransitGatewayRouteTableAssociation", 2)


def test_each_vpc_gets_a_route_through_the_others_attachment(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::TransitGatewayRoute", 2)
    template.has_resource_properties(
        "AWS::EC2::TransitGatewayRoute",
        {
            "DestinationCidrBlock": "10.20.0.0/16",
            "TransitGatewayAttachmentId": {"Ref": "VpcBAttachment"},
        },
    )
    template.has_resource_properties(
        "AWS::EC2::TransitGatewayRoute",
        {
            "DestinationCidrBlock": "10.10.0.0/16",
            "TransitGatewayAttachmentId": {"Ref": "VpcAAttachment"},
        },
    )


def test_transit_gateway_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::EC2::TransitGateway", {"Tags": Match.array_with([tag])}
        )
