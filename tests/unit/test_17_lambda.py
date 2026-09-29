"""Unit tests for modules/17_lambda. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

LambdaStack = stack_class("17_lambda")


def _synth(config):
    app = cdk.App()
    stack = LambdaStack(app, "TestLambdaStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_function(config):
    template = _synth(config)
    template.resource_count_is("AWS::Lambda::Function", 1)


def test_function_uses_the_python_3_13_runtime(config):
    """The whole point of this module: a plain, dependency-free Python 3.13 function."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Runtime": "python3.13", "Handler": "index.handler"},
    )


def test_function_code_is_inline_not_an_asset(config):
    """`Code.from_inline` - no S3 asset bundling, matching this module's whole point."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Code": Match.object_like({"ZipFile": Match.string_like_regexp("hello from")})},
    )


def test_creates_exactly_one_execution_role(config):
    template = _synth(config)
    template.resource_count_is("AWS::IAM::Role", 1)


def test_execution_role_trust_policy_only_allows_lambda_to_assume_it(config):
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


def test_function_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::Lambda::Function", {"Tags": Match.array_with([tag])}
        )
