"""Module 28 - EventBridge: a rule matching a custom application event.

AWS docs used while writing this module:
- Rule construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/Rule.html
- EventPattern construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/EventPattern.html
- CloudWatchLogGroup target: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events_targets/CloudWatchLogGroup.html
- LogGroup construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_logs/LogGroup.html
- Amazon EventBridge event patterns: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html
- Sending events with PutEvents: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevent.html

See README.md in this directory for the full explanation, what an event bus
and a rule are, and how to send a test event.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as events_targets
from aws_cdk import aws_logs as logs
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "EventBridgeStack"


class EventBridgeStack(Stack):
    """A rule on the account's default event bus, matching a custom app event.

    `events.Rule` is the CDK L2 construct for an EventBridge rule. No
    `event_bus=` is passed here, so the rule is created on the account's
    default event bus - the one every AWS account already has, and the one
    `aws events put-events` targets unless told otherwise.

    The rule's `event_pattern` matches a *custom application event* - one
    this learning path's example application would publish itself (via
    `aws events put-events` or the SDK), not an event AWS itself emits (like
    an EC2 state change). Custom events are simpler to explain and to test:
    `source` and `detail_type` are values the publisher makes up, not values
    tied to a specific AWS service's event catalog - see README.md for the
    exact `aws events put-events` command that matches this pattern.

    The rule's target is a CloudWatch Logs log group
    (`events_targets.CloudWatchLogGroup`) - the simplest possible target to
    verify: every matching event's JSON body is written as a new log event,
    visible with `aws logs tail` or in the floci UI, with no Lambda function
    or other compute needed.
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

        log_group_name = resource_name(config.product, config.environment, "logs", "order-events")
        self.log_group = logs.LogGroup(
            self,
            "OrderEventsLogGroup",
            log_group_name=log_group_name,
            retention=logs.RetentionDays.ONE_WEEK,
        )
        apply_name_tag(self.log_group, log_group_name)

        rule_name = resource_name(config.product, config.environment, "events", "order-placed")
        self.rule = events.Rule(
            self,
            "OrderPlacedRule",
            rule_name=rule_name,
            description="Matches custom OrderPlaced application events and logs them.",
            event_pattern=events.EventPattern(
                source=["learning-cdk-python.demo"],
                detail_type=["OrderPlaced"],
            ),
        )
        self.rule.add_target(
            events_targets.CloudWatchLogGroup(
                self.log_group,
                # This target's log-group resource policy is created by a
                # CDK custom resource. install_latest_aws_sdk=False keeps it
                # from downloading the latest AWS SDK at deploy time (the
                # default), which needs outbound internet access - not
                # guaranteed, and not needed, when deploying against floci.
                install_latest_aws_sdk=False,
            )
        )
        apply_name_tag(self.rule, rule_name)


STACK_CLASS = EventBridgeStack
