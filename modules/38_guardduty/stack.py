"""Module 38 - GuardDuty: an account's threat-detection detector.

AWS docs used while writing this module:
- CfnDetector (L1) construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_guardduty/CfnDetector.html
- What is Amazon GuardDuty (one detector per account/region): https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html
- GuardDuty pricing: https://aws.amazon.com/guardduty/pricing/

There is **no CDK L2 construct for GuardDuty** in the current stable
`aws-cdk-lib` - this module uses the L1 `guardduty.CfnDetector`, a 1:1
mapping to the `AWS::GuardDuty::Detector` CloudFormation resource.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_guardduty as guardduty
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "GuardDutyStack"


class GuardDutyStack(Stack):
    """The account's GuardDuty detector, publishing findings every 15 minutes.

    **Read this before deploying to a real account**: GuardDuty allows only
    **one detector per account per region** - see "What is Amazon
    GuardDuty", linked above. If GuardDuty is already enabled in the target
    account/region (directly, or via an AWS Organizations delegated
    administrator), deploying this stack will fail with a "detector already
    exists" error. floci has no such pre-existing detector, so this is only
    a real-AWS concern - see README.md.
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

        self.detector = guardduty.CfnDetector(
            self,
            "Detector",
            enable=True,
            finding_publishing_frequency="FIFTEEN_MINUTES",
        )
        apply_name_tag(
            self.detector,
            resource_name(config.product, config.environment, "guardduty", "detector"),
        )


STACK_CLASS = GuardDutyStack
