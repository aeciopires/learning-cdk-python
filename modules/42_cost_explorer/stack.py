"""Module 42 - Cost Explorer: automated cost anomaly detection (not Cost Explorer itself).

AWS docs used while writing this module:
- CfnAnomalyMonitor (L1) construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ce/CfnAnomalyMonitor.html
- CfnAnomalySubscription (L1) construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ce/CfnAnomalySubscription.html
- AWS::CE::AnomalySubscription CloudFormation resource (ThresholdExpression shape): https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ce-anomalysubscription.html
- Cost Anomaly Detection: https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html
- Enabling Cost Explorer (a manual, one-time, console-only step - see README.md): https://docs.aws.amazon.com/cost-management/latest/userguide/ce-enable.html

**Important - read this before assuming this module "turns on Cost
Explorer"**: it does not, and cannot. See README.md's "Notes and cautions"
for why Cost Explorer's reporting UI has no CloudFormation/CDK resource at
all, and what this stack actually automates instead (Cost Anomaly
Detection, a related but separate feature that *is* CloudFormation-capable).

There is **no CDK L2 construct** for either resource here - this module
uses the L1 `ce.CfnAnomalyMonitor` / `ce.CfnAnomalySubscription`, 1:1
mappings to their CloudFormation resources.
"""

from __future__ import annotations

import json

from aws_cdk import Stack
from aws_cdk import aws_ce as ce
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "CostExplorerStack"


class CostExplorerStack(Stack):
    """A per-service cost anomaly monitor plus a daily email subscription.

    `monitor_type="DIMENSIONAL"` with `monitor_dimension="SERVICE"` asks
    Cost Anomaly Detection to build a per-AWS-service cost model and flag
    unusual spend - the built-in, zero-configuration monitor type. The
    subscription's `threshold_expression` is a JSON *string* (not a nested
    CDK property object - confirmed against the CloudFormation resource
    reference above, where `ThresholdExpression` is typed as `String`, an
    `Expression` object serialized to JSON), so it is built here with
    `json.dumps(...)` rather than a `CfnAnomalySubscription.*Property`
    class.
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

        monitor_name = resource_name(config.product, config.environment, "ce", "service-monitor")
        self.monitor = ce.CfnAnomalyMonitor(
            self,
            "AnomalyMonitor",
            monitor_name=monitor_name,
            monitor_type="DIMENSIONAL",
            monitor_dimension="SERVICE",
        )
        apply_name_tag(self.monitor, monitor_name)

        subscription_name = resource_name(config.product, config.environment, "ce", "daily-subscription")
        # A generic, non-company placeholder address - see CLAUDE.md
        # section 1. Replace with a real, verified address before deploying
        # to a real account.
        alert_address = "changeme@example.com"
        self.subscription = ce.CfnAnomalySubscription(
            self,
            "AnomalySubscription",
            subscription_name=subscription_name,
            frequency="DAILY",
            monitor_arn_list=[self.monitor.attr_monitor_arn],
            subscribers=[
                {"type": "EMAIL", "address": alert_address, "status": "CONFIRMED"},
            ],
            # Alert only on anomalies with at least $100 of total impact -
            # see the CloudFormation reference above for the full
            # Expression grammar (Dimensions/And/Or/Not).
            threshold_expression=json.dumps(
                {
                    "Dimensions": {
                        "Key": "ANOMALY_TOTAL_IMPACT_ABSOLUTE",
                        "MatchOptions": ["GREATER_THAN_OR_EQUAL"],
                        "Values": ["100"],
                    }
                }
            ),
        )
        apply_name_tag(self.subscription, subscription_name)


STACK_CLASS = CostExplorerStack
