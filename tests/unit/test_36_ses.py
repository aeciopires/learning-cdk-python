"""Unit tests for modules/36_ses. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

SesStack = stack_class("36_ses")


def _synth(config):
    app = cdk.App()
    stack = SesStack(app, "TestSesStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_email_identity(config):
    template = _synth(config)
    template.resource_count_is("AWS::SES::EmailIdentity", 1)


def test_email_identity_verifies_the_expected_sender_address(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::SES::EmailIdentity", {"EmailIdentity": "noreply@example.com"}
    )


def test_email_identity_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::SES::EmailIdentity", {"Tags": Match.array_with([tag])}
        )
