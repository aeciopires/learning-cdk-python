"""Unit tests for modules/08_kms. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

KmsStack = stack_class("08_kms")


def _synth(config):
    app = cdk.App()
    stack = KmsStack(app, "TestKmsStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_key(config):
    template = _synth(config)
    template.resource_count_is("AWS::KMS::Key", 1)


def test_key_rotation_is_enabled(config):
    """The whole point of this module: automatic yearly key rotation."""
    template = _synth(config)
    template.has_resource_properties("AWS::KMS::Key", {"EnableKeyRotation": True})


def test_creates_exactly_one_alias(config):
    template = _synth(config)
    template.resource_count_is("AWS::KMS::Alias", 1)


def test_alias_name_has_the_alias_prefix(config):
    template = _synth(config)
    expected_alias = f"alias/{config.product}-{config.environment}-kms-app"
    template.has_resource_properties("AWS::KMS::Alias", {"AliasName": expected_alias})


def test_key_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::KMS::Key", {"Tags": Match.array_with([tag])}
        )
