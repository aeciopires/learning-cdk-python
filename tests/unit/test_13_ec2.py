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


def test_ami_is_resolved_at_launch_not_through_an_ssm_template_parameter(config):
    """An SSM-typed template parameter makes `cdk deploy` redeploy the stack
    every time (duplicating the instance on floci); `resolve:ssm:` doesn't."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::EC2::Instance",
        {"ImageId": "resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64"},
    )
    parameters = template.to_json().get("Parameters", {})
    ssm_parameters = [
        name
        for name, parameter in parameters.items()
        if parameter["Type"].startswith("AWS::SSM::Parameter") and name != "BootstrapVersion"
    ]
    assert ssm_parameters == []
