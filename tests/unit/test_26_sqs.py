"""Unit tests for modules/26_sqs. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

SqsStack = stack_class("26_sqs")


def _synth(config):
    app = cdk.App()
    stack = SqsStack(app, "TestSqsStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_two_queues(config):
    """The main queue and its dead-letter queue."""
    template = _synth(config)
    template.resource_count_is("AWS::SQS::Queue", 2)


def test_main_queue_has_a_redrive_policy_pointing_at_the_dlq(config):
    """The whole point of this module: a message that fails 3 times moves to the DLQ."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::SQS::Queue",
        {"RedrivePolicy": Match.object_like({"maxReceiveCount": 3})},
    )


def test_queues_use_sqs_managed_encryption(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::SQS::Queue", {"SqsManagedSseEnabled": True}
    )


def test_queues_have_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::SQS::Queue", {"Tags": Match.array_with([tag])}
        )
