"""Unit tests for modules/10_parameter_store. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

ParameterStoreStack = stack_class("10_parameter_store")


def _synth(config):
    app = cdk.App()
    stack = ParameterStoreStack(app, "TestParameterStoreStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_parameter(config):
    template = _synth(config)
    template.resource_count_is("AWS::SSM::Parameter", 1)


def test_parameter_uses_the_free_standard_tier(config):
    """The whole point of this module: the free Standard tier, not Advanced."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::SSM::Parameter", {"Tier": "Standard", "Type": "String"}
    )


def test_parameter_name_follows_the_slash_hierarchy(config):
    template = _synth(config)
    expected_name = f"/{config.product}/{config.environment}/app/greeting"
    template.has_resource_properties(
        "AWS::SSM::Parameter", {"Name": expected_name}
    )


def test_parameter_has_the_mandatory_tags(config):
    """AWS::SSM::Parameter's Tags property is a plain {key: value} map, not
    a list of {"Key": ..., "Value": ...} pairs like most other resources
    (confirmed against cdk.out/ParameterStoreStack.template.json) - so each
    mandatory tag is checked as one key/value entry of that object, still
    one Match call per tag as docs/TESTING.md recommends."""
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::SSM::Parameter",
            {"Tags": Match.object_like({tag["Key"]: tag["Value"]})},
        )
