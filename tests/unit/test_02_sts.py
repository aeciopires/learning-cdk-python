"""Unit tests for modules/02_sts. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

StsStack = stack_class("02_sts")


def _synth(config):
    app = cdk.App()
    stack = StsStack(app, "TestStsStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_role(config):
    template = _synth(config)
    template.resource_count_is("AWS::IAM::Role", 1)


def test_trust_policy_requires_the_external_id_condition(config):
    """The "confused deputy" protection this module exists to teach - see README.md."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": Match.object_like(
                {
                    "Statement": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "Action": "sts:AssumeRole",
                                    "Effect": "Allow",
                                    "Condition": {
                                        "StringEquals": Match.object_like(
                                            {"sts:ExternalId": Match.any_value()}
                                        )
                                    },
                                }
                            )
                        ]
                    )
                }
            )
        },
    )


def test_role_grants_only_the_one_trivial_action(config):
    template = _synth(config)
    policies = template.find_resources("AWS::IAM::Policy")
    all_actions = []
    for policy in policies.values():
        for statement in policy["Properties"]["PolicyDocument"]["Statement"]:
            actions = statement["Action"]
            all_actions.extend(actions if isinstance(actions, list) else [actions])
    assert all_actions == ["s3:ListAllMyBuckets"]


def test_role_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::IAM::Role", {"Tags": Match.array_with([tag])}
        )
