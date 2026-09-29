"""Unit tests for modules/43_resource_group_tagging.

See docs/TESTING.md for how these work.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

ResourceGroupTaggingStack = stack_class("43_resource_group_tagging")


def _synth(config):
    app = cdk.App()
    stack = ResourceGroupTaggingStack(app, "TestResourceGroupTaggingStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_resource_group(config):
    template = _synth(config)
    template.resource_count_is("AWS::ResourceGroups::Group", 1)


def test_resource_group_filters_by_the_product_tag(config):
    """This module's whole point: a dynamic group of every `product`-tagged
    resource, computed live by AWS - see README.md and stack.py.
    """
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ResourceGroups::Group",
        {
            "ResourceQuery": Match.object_like(
                {
                    "Type": "TAG_FILTERS_1_0",
                    "Query": Match.object_like(
                        {
                            "ResourceTypeFilters": ["AWS::AllSupported"],
                            "TagFilters": Match.array_with(
                                [
                                    Match.object_like(
                                        {
                                            "Key": "product",
                                            "Values": [config.product],
                                        }
                                    )
                                ]
                            ),
                        }
                    ),
                }
            )
        },
    )


def test_resource_group_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::ResourceGroups::Group", {"Tags": Match.array_with([tag])}
        )
