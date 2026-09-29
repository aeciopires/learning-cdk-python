"""Module 32 - CloudFront: a distribution in front of a private S3 bucket.

AWS docs used while writing this module:
- Distribution construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront/Distribution.html
- BehaviorOptions construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront/BehaviorOptions.html
- S3BucketOrigin construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront_origins/S3BucketOrigin.html
- Bucket construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3/Bucket.html
- Restricting access to an Amazon S3 origin (Origin Access Control):
  https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

`origins.S3BucketOrigin.with_origin_access_control(bucket)` was confirmed by
introspecting the installed `aws_cdk.aws_cloudfront_origins` module
(aws-cdk-lib 2.271.0): the module exposes `S3BucketOrigin` with a
`with_origin_access_control` classmethod, and its sibling `S3Origin` class
is documented (in the API reference) as deprecated in favor of
`S3BucketOrigin`. Origin Access Control (OAC) is the current AWS-recommended
way for CloudFront to read from a private S3 bucket - it replaces the older
Origin Access Identity (OAI) mechanism `S3Origin` (and
`with_origin_access_identity`) used. This module therefore uses
`S3BucketOrigin.with_origin_access_control`, which also creates and attaches
the bucket policy CloudFront needs automatically.

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_s3 as s3
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "CloudFrontStack"


class CloudFrontStack(Stack):
    """A CloudFront distribution serving a private S3 bucket via Origin Access Control.

    The bucket is created with `block_public_access=s3.BlockPublicAccess
    .BLOCK_ALL` - it is never directly reachable over the internet.
    CloudFront reaches it instead through Origin Access Control (OAC), a
    signed-request mechanism configured entirely by
    `S3BucketOrigin.with_origin_access_control(bucket)`, which also updates
    the bucket policy to allow only this distribution to read from it.

    `removal_policy=RemovalPolicy.DESTROY` + `auto_delete_objects=True` are
    set so `cdk destroy` fully cleans up this learning module (the default,
    `RETAIN`, would otherwise leave the bucket behind) - reconsider both for
    a bucket holding real data.
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

        bucket_name = resource_name(config.product, config.environment, "s3", "cdn-origin")
        self.origin_bucket = s3.Bucket(
            self,
            "OriginBucket",
            bucket_name=bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        apply_name_tag(self.origin_bucket, bucket_name)

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            comment=resource_name(config.product, config.environment, "cloudfront", "cdn"),
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(self.origin_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
        )
        apply_name_tag(
            self.distribution,
            resource_name(config.product, config.environment, "cloudfront", "cdn"),
        )


STACK_CLASS = CloudFrontStack
