"""Unit tests for modules/12_s3. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

S3Stack = stack_class("12_s3")


def _synth(config):
    app = cdk.App()
    stack = S3Stack(app, "TestS3Stack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_bucket(config):
    template = _synth(config)
    template.resource_count_is("AWS::S3::Bucket", 1)


def test_bucket_has_versioning_enabled(config):
    """The whole point of this module: object versions are kept, not overwritten."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {"VersioningConfiguration": {"Status": "Enabled"}},
    )


def test_bucket_blocks_all_public_access(config):
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


def test_bucket_has_default_encryption(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "BucketEncryption": Match.object_like(
                {
                    "ServerSideEncryptionConfiguration": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "ServerSideEncryptionByDefault": Match.object_like(
                                        {"SSEAlgorithm": "AES256"}
                                    )
                                }
                            )
                        ]
                    )
                }
            )
        },
    )


def test_bucket_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::S3::Bucket", {"Tags": Match.array_with([tag])}
        )
