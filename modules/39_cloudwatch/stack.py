"""Module 39 - CloudWatch: log group -> metric filter -> alarm -> dashboard.

AWS docs used while writing this module:
- LogGroup construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_logs/LogGroup.html
- MetricFilter construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_logs/MetricFilter.html
- FilterPattern construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_logs/FilterPattern.html
- Alarm construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html
- Dashboard / GraphWidget constructs: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html
- Using Amazon CloudWatch alarms: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/AlarmThatSendsEmail.html
- Searching and filtering log data (metric filter patterns): https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html

See README.md for the end-to-end pipeline this module teaches: a log line
becomes a custom metric, the metric drives an alarm, and the same metric is
plotted on a dashboard.
"""

from __future__ import annotations

from aws_cdk import Duration, Stack
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_logs as logs
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "CloudWatchStack"


class CloudWatchStack(Stack):
    """A log group, a metric filter counting "ERROR" lines, an alarm, and a dashboard.

    Nothing in this module writes log lines by itself (there is no compute
    resource here) - it wires up the *pipeline* a real application's
    CloudWatch Logs would flow through. See README.md's "Verify" section
    for how to `aws logs put-log-events` a sample "ERROR" line and watch the
    metric and alarm react.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: AppConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        apply_standard_tags(self, tags=config.to_standard_tags())

        log_group_name = resource_name(config.product, config.environment, "logs", "app")
        self.log_group = logs.LogGroup(
            self,
            "AppLogGroup",
            log_group_name=log_group_name,
            retention=logs.RetentionDays.ONE_WEEK,
        )
        apply_name_tag(self.log_group, log_group_name)

        metric_namespace = resource_name(config.product, config.environment, "app")
        metric_name = "ErrorCount"

        # FilterPattern.literal(...) takes a raw CloudWatch Logs filter
        # pattern string; a single quoted term like '"ERROR"' matches any
        # log event containing that substring - see the "Searching and
        # filtering log data" reference above for the full pattern syntax.
        self.error_metric_filter = logs.MetricFilter(
            self,
            "ErrorMetricFilter",
            log_group=self.log_group,
            filter_pattern=logs.FilterPattern.literal('"ERROR"'),
            metric_namespace=metric_namespace,
            metric_name=metric_name,
            metric_value="1",
        )

        # `MetricFilter.metric()` returns an `aws_cloudwatch.Metric` bound to
        # this filter's namespace/name, so the alarm and dashboard below
        # don't have to repeat metric_namespace/metric_name by hand.
        error_metric = self.error_metric_filter.metric(
            statistic="sum",
            period=Duration.minutes(5),
        )

        alarm_name = resource_name(config.product, config.environment, "cloudwatch", "error-alarm")
        self.error_alarm = cloudwatch.Alarm(
            self,
            "ErrorAlarm",
            alarm_name=alarm_name,
            alarm_description='Fires when at least one "ERROR" line is logged in a 5-minute period.',
            metric=error_metric,
            threshold=1,
            evaluation_periods=1,
            # No data (no log events at all in a period) is not the same as
            # a breach - treating it as NOT_BREACHING avoids a false alarm
            # on a quiet application, which is normal, not an incident.
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
        )
        apply_name_tag(self.error_alarm, alarm_name)

        dashboard_name = resource_name(config.product, config.environment, "cloudwatch", "dashboard")
        self.dashboard = cloudwatch.Dashboard(self, "Dashboard", dashboard_name=dashboard_name)
        self.dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Application ERROR log lines (5 min sum)",
                left=[error_metric],
            )
        )
        apply_name_tag(self.dashboard, dashboard_name)


STACK_CLASS = CloudWatchStack
