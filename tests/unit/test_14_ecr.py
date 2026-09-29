"""Unit tests for modules/14_ecr. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

EcrStack = stack_class("14_ecr")


def _synth(config):
    app = cdk.App()
    stack = EcrStack(app, "TestEcrStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_repository(config):
    template = _synth(config)
    template.resource_count_is("AWS::ECR::Repository", 1)


def test_repository_scans_images_on_push(config):
    """The whole point of this module: every pushed image gets scanned automatically."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ECR::Repository",
        {"ImageScanningConfiguration": {"ScanOnPush": True}},
    )


def test_repository_empties_itself_on_delete(config):
    """Without this, `cdk destroy` cannot remove a repository that still has images."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ECR::Repository", {"EmptyOnDelete": True}
    )


def test_repository_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::ECR::Repository", {"Tags": Match.array_with([tag])}
        )
