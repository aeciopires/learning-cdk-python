"""Unit tests for modules/33_route53. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

Route53Stack = stack_class("33_route53")


def _synth(config):
    app = cdk.App()
    stack = Route53Stack(app, "TestRoute53Stack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_private_hosted_zone(config):
    template = _synth(config)
    template.resource_count_is("AWS::Route53::HostedZone", 1)


def test_hosted_zone_is_associated_with_the_vpc(config):
    """What makes it "private" - a public hosted zone has no VPCs property."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Route53::HostedZone",
        {"VPCs": Match.array_with([Match.object_like({"VPCId": Match.any_value()})])},
    )


def test_creates_the_a_record_pointing_at_the_expected_ip(config):
    template = _synth(config)
    template.resource_count_is("AWS::Route53::RecordSet", 1)
    template.has_resource_properties(
        "AWS::Route53::RecordSet",
        {"Type": "A", "ResourceRecords": ["10.0.0.10"]},
    )


def test_hosted_zone_has_the_mandatory_tags(config):
    # AWS::Route53::HostedZone tags live under "HostedZoneTags", not "Tags" -
    # this is a real exception to the "Tags" property name used by most other
    # resource types in this repository (confirmed in the real synthesized
    # template).
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::Route53::HostedZone", {"HostedZoneTags": Match.array_with([tag])}
        )
