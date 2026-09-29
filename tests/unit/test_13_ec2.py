"""Unit tests for modules/13_ec2. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

Ec2Stack = stack_class("13_ec2")


def _synth(config):
    app = cdk.App()
    stack = Ec2Stack(app, "TestEc2Stack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_instance(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::Instance", 1)


def test_instance_type_is_t3_micro(config):
    """The whole point of this module: the cheapest general-purpose instance type."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::EC2::Instance", {"InstanceType": "t3.micro"}
    )


def test_security_group_has_no_inbound_rules(config):
    """No SSH port open - reach the instance via SSM Session Manager instead."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {"SecurityGroupIngress": Match.absent()},
    )


def test_instance_role_only_attaches_the_ssm_managed_policy(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "ManagedPolicyArns": Match.array_with(
                [
                    {
                        "Fn::Join": [
                            "",
                            Match.array_with(
                                [Match.string_like_regexp("AmazonSSMManagedInstanceCore")]
                            ),
                        ]
                    }
                ]
            )
        },
    )


def test_instance_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::EC2::Instance", {"Tags": Match.array_with([tag])}
        )
