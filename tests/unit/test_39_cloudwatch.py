"""Unit tests for modules/39_cloudwatch. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

CloudWatchStack = stack_class("39_cloudwatch")


def _synth(config):
    app = cdk.App()
    stack = CloudWatchStack(app, "TestCloudWatchStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_log_group(config):
    template = _synth(config)
    template.resource_count_is("AWS::Logs::LogGroup", 1)


def test_creates_exactly_one_metric_filter(config):
    template = _synth(config)
    template.resource_count_is("AWS::Logs::MetricFilter", 1)


def test_creates_exactly_one_alarm(config):
    template = _synth(config)
    template.resource_count_is("AWS::CloudWatch::Alarm", 1)


def test_creates_exactly_one_dashboard(config):
    template = _synth(config)
    template.resource_count_is("AWS::CloudWatch::Dashboard", 1)


def test_metric_filter_counts_error_log_lines(config):
    """The pipeline's first hop: an "ERROR" log line becomes a custom metric."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Logs::MetricFilter",
        {
            "FilterPattern": '"ERROR"',
            "MetricTransformations": Match.array_with(
                [
                    Match.object_like(
                        {
                            "MetricName": "ErrorCount",
                            "MetricValue": "1",
                        }
                    )
                ]
            ),
        },
    )


def test_alarm_fires_on_at_least_one_error_in_five_minutes(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {
            "MetricName": "ErrorCount",
            "ComparisonOperator": "GreaterThanOrEqualToThreshold",
            "Threshold": 1,
            "EvaluationPeriods": 1,
            "Period": 300,
        },
    )


def test_log_group_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::Logs::LogGroup", {"Tags": Match.array_with([tag])}
        )


def test_alarm_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::CloudWatch::Alarm", {"Tags": Match.array_with([tag])}
        )


def test_dashboard_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::CloudWatch::Dashboard", {"Tags": Match.array_with([tag])}
        )


# AWS::Logs::MetricFilter has no tagging property at all (absent from the
# real synthesized cdk.out/CloudWatchStack.template.json), so there is no
# mandatory-tags test for it.
