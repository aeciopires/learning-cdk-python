"""S3: same `s3.Bucket` call verified in modules/12_s3/stack.py."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class S3ResourceBuilder(ResourceBuilder):
    key = "s3"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        bucket_name = resource_name(config.product, config.environment, cell, "s3", "app-data")
        bucket = s3.Bucket(
            scope,
            "AppDataBucket",
            bucket_name=bucket_name,
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        apply_name_tag(bucket, bucket_name)

        context.shared["s3_bucket"] = bucket
