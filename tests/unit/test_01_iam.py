"""Unit tests for modules/01_iam. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

IamStack = stack_class("01_iam")


def _synth(config):
    app = cdk.App()
    stack = IamStack(app, "TestIamStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_role(config):
    template = _synth(config)
    template.resource_count_is("AWS::IAM::Role", 1)


def test_role_trust_policy_only_allows_lambda_to_assume_it(config):
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
                                    "Principal": {"Service": "lambda.amazonaws.com"},
                                }
                            )
                        ]
                    )
                }
            )
        },
    )


def test_creates_exactly_one_customer_managed_policy(config):
    template = _synth(config)
    template.resource_count_is("AWS::IAM::ManagedPolicy", 1)


def test_read_only_policy_does_not_grant_write_actions(config):
    """The whole point of this module: no s3:PutObject/DeleteObject anywhere."""
    template = _synth(config)
    policies = template.find_resources("AWS::IAM::ManagedPolicy")
    for policy in policies.values():
        statements = policy["Properties"]["PolicyDocument"]["Statement"]
        for statement in statements:
            actions = statement["Action"]
            actions = actions if isinstance(actions, list) else [actions]
            for action in actions:
                assert not action.startswith("s3:Put"), f"unexpected write action: {action}"
                assert not action.startswith("s3:Delete"), f"unexpected write action: {action}"
                assert action != "s3:*", "policy should not grant s3:* (least privilege)"


def test_role_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::IAM::Role", {"Tags": Match.array_with([tag])}
        )
