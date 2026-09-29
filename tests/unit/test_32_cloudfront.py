"""Unit tests for modules/32_cloudfront. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

CloudFrontStack = stack_class("32_cloudfront")


def _synth(config):
    app = cdk.App()
    stack = CloudFrontStack(app, "TestCloudFrontStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_distribution(config):
    template = _synth(config)
    template.resource_count_is("AWS::CloudFront::Distribution", 1)


def test_distribution_redirects_http_to_https(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": Match.object_like(
                {
                    "DefaultCacheBehavior": Match.object_like(
                        {"ViewerProtocolPolicy": "redirect-to-https"}
                    )
                }
            )
        },
    )


def test_origin_bucket_blocks_all_public_access(config):
    """The point of Origin Access Control: the bucket is never public - CloudFront reaches it privately."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )


def test_distribution_has_the_mandatory_tags(config):
    # AWS::CloudFront::Distribution does support a top-level "Tags" property
    # (confirmed in the real synthesized template), unlike some resources
    # whose tags live under a differently-named property - see
    # test_33_route53.py's HostedZoneTags for a case where that is not true.
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::CloudFront::Distribution", {"Tags": Match.array_with([tag])}
        )
