"""Unit tests for modules/38_guardduty. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

GuardDutyStack = stack_class("38_guardduty")


def _synth(config):
    app = cdk.App()
    stack = GuardDutyStack(app, "TestGuardDutyStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_detector(config):
    template = _synth(config)
    template.resource_count_is("AWS::GuardDuty::Detector", 1)


def test_detector_is_enabled(config):
    """The whole point of this module: threat detection is actually turned on."""
    template = _synth(config)
    template.has_resource_properties("AWS::GuardDuty::Detector", {"Enable": True})


def test_detector_publishes_findings_every_fifteen_minutes(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::GuardDuty::Detector",
        {"FindingPublishingFrequency": "FIFTEEN_MINUTES"},
    )


def test_detector_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::GuardDuty::Detector", {"Tags": Match.array_with([tag])}
        )
