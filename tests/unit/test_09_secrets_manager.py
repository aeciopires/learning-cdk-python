"""Unit tests for modules/09_secrets_manager. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

SecretsManagerStack = stack_class("09_secrets_manager")


def _synth(config):
    app = cdk.App()
    stack = SecretsManagerStack(app, "TestSecretsManagerStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_secret(config):
    template = _synth(config)
    template.resource_count_is("AWS::SecretsManager::Secret", 1)


def test_secret_value_is_generated_not_hardcoded(config):
    """The whole point of this module: no real-looking secret value ever
    appears in the code or the template - only the shape Secrets Manager
    should generate at deploy time."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::SecretsManager::Secret",
        {
            "GenerateSecretString": Match.object_like(
                {
                    "GenerateStringKey": "password",
                    "PasswordLength": 32,
                    "ExcludePunctuation": True,
                }
            )
        },
    )
    (secret,) = template.find_resources("AWS::SecretsManager::Secret").values()
    assert "SecretString" not in secret["Properties"], (
        "a real secret value must never be written into the template"
    )


def test_secret_name_matches_the_naming_convention(config):
    template = _synth(config)
    expected_name = f"{config.product}-{config.environment}-secret-app-credential"
    template.has_resource_properties(
        "AWS::SecretsManager::Secret", {"Name": expected_name}
    )


def test_secret_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::SecretsManager::Secret", {"Tags": Match.array_with([tag])}
        )
