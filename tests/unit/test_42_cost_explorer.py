"""Unit tests for modules/42_cost_explorer. See docs/TESTING.md for how these work."""

from __future__ import annotations

import json

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

CostExplorerStack = stack_class("42_cost_explorer")


def _synth(config):
    app = cdk.App()
    stack = CostExplorerStack(app, "TestCostExplorerStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_anomaly_monitor(config):
    template = _synth(config)
    template.resource_count_is("AWS::CE::AnomalyMonitor", 1)


def test_creates_exactly_one_anomaly_subscription(config):
    template = _synth(config)
    template.resource_count_is("AWS::CE::AnomalySubscription", 1)


def test_monitor_builds_a_per_service_cost_model(config):
    """The built-in, zero-configuration monitor type this module uses."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::CE::AnomalyMonitor",
        {"MonitorType": "DIMENSIONAL", "MonitorDimension": "SERVICE"},
    )


def test_subscription_only_alerts_above_100_dollars_of_impact(config):
    """`ThresholdExpression` is a JSON *string* on this CloudFormation
    resource (not a nested property object - see stack.py's docstring), so
    it must be parsed with `json.loads(...)` before its contents can be
    asserted on, the same way `test_01_iam.py` inspects a policy document
    it pulled out with `find_resources(...)`.
    """
    template = _synth(config)
    subscriptions = template.find_resources("AWS::CE::AnomalySubscription")
    assert len(subscriptions) == 1
    (subscription,) = subscriptions.values()
    threshold_expression = json.loads(subscription["Properties"]["ThresholdExpression"])
    assert threshold_expression == {
        "Dimensions": {
            "Key": "ANOMALY_TOTAL_IMPACT_ABSOLUTE",
            "MatchOptions": ["GREATER_THAN_OR_EQUAL"],
            "Values": ["100"],
        }
    }


def test_anomaly_monitor_has_the_mandatory_tags(config):
    """Both `CE` resources tag via `ResourceTags` (still a `Tags`-shaped list
    of `{"Key": ..., "Value": ...}` pairs, just under a different property
    name - confirmed in the real synthesized
    `cdk.out/CostExplorerStack.template.json`), so the usual one-
    `array_with`-call-per-tag discipline still applies.
    """
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::CE::AnomalyMonitor", {"ResourceTags": Match.array_with([tag])}
        )


def test_anomaly_subscription_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::CE::AnomalySubscription", {"ResourceTags": Match.array_with([tag])}
        )
