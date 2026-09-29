"""Unit tests for modules/07_vpc_peering. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

VpcPeeringStack = stack_class("07_vpc_peering")


def _synth(config):
    app = cdk.App()
    stack = VpcPeeringStack(app, "TestVpcPeeringStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_peering_connection(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::VPCPeeringConnection", 1)


def test_peering_connection_links_both_vpcs(config):
    template = _synth(config)
    vpc_logical_ids = set(template.find_resources("AWS::EC2::VPC").keys())
    assert len(vpc_logical_ids) == 2

    (peering,) = template.find_resources("AWS::EC2::VPCPeeringConnection").values()
    props = peering["Properties"]
    referenced_ids = {props["VpcId"]["Ref"], props["PeerVpcId"]["Ref"]}
    assert referenced_ids == vpc_logical_ids


def test_each_vpc_gets_a_route_to_the_others_cidr(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::Route", 2)
    template.has_resource_properties(
        "AWS::EC2::Route", {"DestinationCidrBlock": "10.40.0.0/16"}
    )
    template.has_resource_properties(
        "AWS::EC2::Route", {"DestinationCidrBlock": "10.30.0.0/16"}
    )


def test_routes_depend_explicitly_on_the_peering_connection(config):
    """This module's pedagogical point: even though CfnRoute already
    references the peering connection via vpc_peering_connection_id (so
    CloudFormation can infer the ordering), stack.py still calls
    add_resource_dependency() explicitly - see the class docstring."""
    template = _synth(config)
    (peering_id,) = template.find_resources("AWS::EC2::VPCPeeringConnection").keys()
    routes = template.find_resources("AWS::EC2::Route")
    for route in routes.values():
        assert peering_id in route.get("DependsOn", [])


def test_peering_connection_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::EC2::VPCPeeringConnection", {"Tags": Match.array_with([tag])}
        )
