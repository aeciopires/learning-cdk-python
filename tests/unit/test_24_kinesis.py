"""Unit tests for modules/24_kinesis. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

KinesisStack = stack_class("24_kinesis")


def _synth(config):
    app = cdk.App()
    stack = KinesisStack(app, "TestKinesisStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_stream(config):
    template = _synth(config)
    template.resource_count_is("AWS::Kinesis::Stream", 1)


def test_stream_has_one_shard_and_24_hour_retention(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Kinesis::Stream",
        {"ShardCount": 1, "RetentionPeriodHours": 24},
    )


def test_stream_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::Kinesis::Stream", {"Tags": Match.array_with([tag])}
        )
