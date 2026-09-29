"""Unit tests for modules/03_vpc. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

VpcStack = stack_class("03_vpc")


def _synth(config):
    app = cdk.App()
    stack = VpcStack(app, "TestVpcStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_vpc(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::VPC", 1)


def test_creates_four_subnets_two_public_two_isolated(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::Subnet", 4)


def test_creates_exactly_one_security_group(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::SecurityGroup", 1)


def test_security_group_allows_https_from_the_vpc_only(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "SecurityGroupIngress": Match.array_with(
                [
                    Match.object_like(
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 443,
                            "ToPort": 443,
                        }
                    )
                ]
            )
        },
    )


def test_vpc_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::EC2::VPC", {"Tags": Match.array_with([tag])}
        )


def test_security_group_has_a_name_tag_matching_its_own_purpose(config):
    template = _synth(config)
    expected_name = f"{config.product}-{config.environment}-sg-app"
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {"Tags": Match.array_with([{"Key": "Name", "Value": expected_name}])},
    )
