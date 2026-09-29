"""Unit tests for modules/27_sns. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

SnsStack = stack_class("27_sns")


def _synth(config):
    app = cdk.App()
    stack = SnsStack(app, "TestSnsStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_topic(config):
    template = _synth(config)
    template.resource_count_is("AWS::SNS::Topic", 1)


def test_creates_exactly_one_sqs_subscription(config):
    """The fan-out: the topic delivers into the queue via an SQS subscription."""
    template = _synth(config)
    template.resource_count_is("AWS::SNS::Subscription", 1)
    template.has_resource_properties(
        "AWS::SNS::Subscription", {"Protocol": "sqs"}
    )


def test_creates_exactly_one_queue(config):
    template = _synth(config)
    template.resource_count_is("AWS::SQS::Queue", 1)


def test_topic_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::SNS::Topic", {"Tags": Match.array_with([tag])}
        )
