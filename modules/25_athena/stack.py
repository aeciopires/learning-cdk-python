"""Module 25 - Athena: a query result bucket plus a dedicated Athena workgroup.

AWS docs used while writing this module:
- CfnWorkGroup construct (L1 - see note below): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_athena/CfnWorkGroup.html
  (nested property classes `WorkGroupConfigurationProperty` and
  `ResultConfigurationProperty` checked directly against the installed
  aws-cdk-lib==2.271.0 source for their exact field names - see README.md).
- Bucket construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3/Bucket.html
- Amazon Athena - Query result location and workgroups: https://docs.aws.amazon.com/athena/latest/ug/querying.html
- Amazon Athena pricing (per TB of data scanned, no hourly charge by
  itself): https://aws.amazon.com/athena/pricing/

**L1-only note:** `aws_cdk.aws_athena` has **no L2 (curated) construct** for
a workgroup - unlike `aws_s3.Bucket` or `aws_dynamodb.Table`, there is no
`athena.WorkGroup` class. This module therefore uses the L1
`athena.CfnWorkGroup` directly, a 1:1 mapping to the underlying
`AWS::Athena::WorkGroup` CloudFormation resource type - see CLAUDE.md
section 4, point 2.

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_athena as athena
from aws_cdk import aws_s3 as s3
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "AthenaStack"


class AthenaStack(Stack):
    """One S3 bucket for query results plus one Athena workgroup pointed at it.

    Athena itself has no separate resource to "create" beyond the workgroup
    - queries are run against tables cataloged elsewhere (typically AWS
    Glue Data Catalog, out of scope for this module) and their results are
    written to the S3 location configured here. `block_public_access=BLOCK_ALL`
    and `encryption=S3_MANAGED` follow the same secure-by-default pattern as
    every other bucket-creating module in this learning path;
    `auto_delete_objects=True` paired with `removal_policy=DESTROY` lets
    `cdk destroy` remove the bucket (and anything Athena wrote into it)
    without a manual empty-bucket step first.
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

        bucket_name = resource_name(config.product, config.environment, "athena", "results")
        self.results_bucket = s3.Bucket(
            self,
            "ResultsBucket",
            bucket_name=bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        apply_name_tag(self.results_bucket, bucket_name)

        workgroup_name = resource_name(config.product, config.environment, "athena", "primary")
        self.workgroup = athena.CfnWorkGroup(
            self,
            "WorkGroup",
            name=workgroup_name,
            description="Learning path Athena workgroup - query results are written to ResultsBucket.",
            work_group_configuration=athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.results_bucket.bucket_name}/athena-results/"
                )
            ),
        )


STACK_CLASS = AthenaStack
