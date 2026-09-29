"""Module 40 - CloudTrail: a multi-region trail of account activity.

AWS docs used while writing this module:
- Trail (L2) construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudtrail/Trail.html
- CloudTrail concepts: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html
- AWS CloudTrail pricing: https://aws.amazon.com/cloudtrail/pricing/

`aws_cdk.aws_cloudtrail.Trail` (verified against the API reference above)
does **not** require an explicit `bucket=`: when omitted, it creates a new
S3 bucket, with the correct CloudTrail bucket policy already attached, to
hold the delivered log files.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_cloudtrail as cloudtrail
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "CloudTrailStack"


class CloudTrailStack(Stack):
    """One multi-region trail, with log file integrity validation enabled.

    `is_multi_region_trail=True` records API activity from every AWS
    region into this one trail/bucket, not just the region this stack is
    deployed to. `enable_file_validation=True` adds a per-file digital
    signature/digest so tampering with a delivered log file after the fact
    can be detected - see "CloudTrail concepts", linked above.
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

        trail_name = resource_name(config.product, config.environment, "cloudtrail", "main")
        self.trail = cloudtrail.Trail(
            self,
            "Trail",
            trail_name=trail_name,
            is_multi_region_trail=True,
            enable_file_validation=True,
        )
        apply_name_tag(self.trail, trail_name)


STACK_CLASS = CloudTrailStack
