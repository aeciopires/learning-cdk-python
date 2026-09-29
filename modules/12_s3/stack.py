"""Module 12 - S3: a versioned, encrypted, fully private bucket.

AWS docs used while writing this module:
- Bucket construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3/Bucket.html
- BlockPublicAccess: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3/BlockPublicAccess.html
- Amazon S3 - What is Amazon S3: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html
- Amazon S3 bucket naming rules: https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "S3Stack"


class S3Stack(Stack):
    """One S3 bucket: versioned, S3-managed encryption, fully blocked from public access.

    `removal_policy=cdk.RemovalPolicy.DESTROY` plus `auto_delete_objects=True`
    is a **learning-path choice, not a production default**: production
    buckets usually keep `RemovalPolicy.RETAIN` (the CDK default) so a
    `cdk destroy`, or a mistaken stack deletion, can never take customer data
    with it. Here, `auto_delete_objects=True` lets `cdk destroy` fully clean
    up floci (and a real sandbox account) without a manual "empty the
    bucket" step first - see "Notes and cautions" in README.md for what this
    provisions under the hood (a small custom-resource Lambda function).
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

        bucket_name = resource_name(config.product, config.environment, "s3", "app-data")
        self.bucket = s3.Bucket(
            self,
            "AppDataBucket",
            bucket_name=bucket_name,
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        apply_name_tag(self.bucket, bucket_name)


STACK_CLASS = S3Stack
