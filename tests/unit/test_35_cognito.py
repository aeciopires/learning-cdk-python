"""Unit tests for modules/35_cognito. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

CognitoStack = stack_class("35_cognito")


def _synth(config):
    app = cdk.App()
    stack = CognitoStack(app, "TestCognitoStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_user_pool(config):
    template = _synth(config)
    template.resource_count_is("AWS::Cognito::UserPool", 1)


def test_creates_exactly_one_user_pool_client(config):
    template = _synth(config)
    template.resource_count_is("AWS::Cognito::UserPoolClient", 1)


def test_user_pool_enforces_a_strong_password_policy(config):
    """The whole point of this module's sign-up flow: no weak passwords."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Cognito::UserPool",
        {
            "Policies": Match.object_like(
                {
                    "PasswordPolicy": Match.object_like(
                        {
                            "MinimumLength": 12,
                            "RequireLowercase": True,
                            "RequireNumbers": True,
                            "RequireSymbols": True,
                            "RequireUppercase": True,
                        }
                    )
                }
            )
        },
    )


def test_user_pool_client_is_public_with_no_secret(config):
    """A browser/mobile client cannot keep a secret confidential - see README.md."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Cognito::UserPoolClient", {"GenerateSecret": False}
    )


def test_user_pool_has_the_mandatory_tags(config):
    """AWS::Cognito::UserPool tags as `UserPoolTags`, an object/map (key ->
    value), not the `Tags` list of `{"Key": ..., "Value": ...}` pairs most
    other resources use - confirmed by reading the real synthesized
    `cdk.out/CognitoStack.template.json`. A map has no ordering concern the
    way a `Tags` array does (see `tests/_helpers.mandatory_tag_pairs`
    docstring), so one `Match.object_like(...)` call covering every tag is
    fine here - the array_with-per-tag discipline is specific to `Tags` lists.

    `AWS::Cognito::UserPoolClient` has no tagging property at all (absent
    from the synthesized template), so there is no equivalent test for it.
    """
    template = _synth(config)
    expected = {pair["Key"]: pair["Value"] for pair in mandatory_tag_pairs(config)}
    template.has_resource_properties(
        "AWS::Cognito::UserPool", {"UserPoolTags": Match.object_like(expected)}
    )
