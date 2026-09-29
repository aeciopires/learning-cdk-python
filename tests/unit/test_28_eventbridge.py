"""Unit tests for modules/28_eventbridge. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

EventBridgeStack = stack_class("28_eventbridge")


def _synth(config):
    app = cdk.App()
    stack = EventBridgeStack(app, "TestEventBridgeStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_rule(config):
    template = _synth(config)
    template.resource_count_is("AWS::Events::Rule", 1)


def test_rule_matches_the_custom_orderplaced_event(config):
    """The event pattern this module exists to teach - see README.md."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Events::Rule",
        {
            "EventPattern": {
                "source": ["learning-cdk-python.demo"],
                "detail-type": ["OrderPlaced"],
            }
        },
    )


def test_creates_exactly_one_log_group_target(config):
    template = _synth(config)
    template.resource_count_is("AWS::Logs::LogGroup", 1)
    template.has_resource_properties(
        "AWS::Events::Rule",
        {"Targets": Match.array_with([Match.object_like({"Id": "Target0"})])},
    )


def test_rule_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::Events::Rule", {"Tags": Match.array_with([tag])}
        )
