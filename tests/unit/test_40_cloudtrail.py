"""Unit tests for modules/40_cloudtrail. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

CloudTrailStack = stack_class("40_cloudtrail")


def _synth(config):
    app = cdk.App()
    stack = CloudTrailStack(app, "TestCloudTrailStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_trail(config):
    template = _synth(config)
    template.resource_count_is("AWS::CloudTrail::Trail", 1)


def test_trail_creates_its_own_log_bucket(config):
    """`Trail(...)` was called with no `bucket=` - it creates one for us."""
    template = _synth(config)
    template.resource_count_is("AWS::S3::Bucket", 1)


def test_trail_is_multi_region_with_file_validation(config):
    """This module's whole point: every region's activity, tamper-evident."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::CloudTrail::Trail",
        {
            "IsMultiRegionTrail": True,
            "EnableLogFileValidation": True,
            "IsLogging": True,
        },
    )


def test_trail_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::CloudTrail::Trail", {"Tags": Match.array_with([tag])}
        )
