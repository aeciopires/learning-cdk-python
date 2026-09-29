"""Unit tests for modules/25_athena. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

AthenaStack = stack_class("25_athena")


def _synth(config):
    app = cdk.App()
    stack = AthenaStack(app, "TestAthenaStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_workgroup(config):
    template = _synth(config)
    template.resource_count_is("AWS::Athena::WorkGroup", 1)


def test_creates_exactly_one_results_bucket(config):
    template = _synth(config)
    template.resource_count_is("AWS::S3::Bucket", 1)


def test_workgroup_points_its_result_configuration_at_the_bucket(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Athena::WorkGroup",
        {
            "WorkGroupConfiguration": Match.object_like(
                {
                    "ResultConfiguration": Match.object_like(
                        {"OutputLocation": Match.any_value()}
                    )
                }
            )
        },
    )


def test_results_bucket_blocks_all_public_access(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": Match.object_like(
                {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True,
                }
            )
        },
    )


def test_workgroup_has_the_mandatory_tags(config):
    """The workgroup has no `apply_name_tag()` call in stack.py (only the
    bucket does), so only the 6 stack-wide mandatory tags are asserted here -
    no `Name` tag on this resource. See stack.py."""
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::Athena::WorkGroup", {"Tags": Match.array_with([tag])}
        )


def test_results_bucket_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::S3::Bucket", {"Tags": Match.array_with([tag])}
        )
