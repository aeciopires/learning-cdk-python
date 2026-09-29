"""Unit tests for modules/22_elasticache. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

ElastiCacheStack = stack_class("22_elasticache")


def _synth(config):
    app = cdk.App()
    stack = ElastiCacheStack(app, "TestElastiCacheStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_cache_cluster(config):
    template = _synth(config)
    template.resource_count_is("AWS::ElastiCache::CacheCluster", 1)


def test_creates_exactly_one_cache_subnet_group(config):
    template = _synth(config)
    template.resource_count_is("AWS::ElastiCache::SubnetGroup", 1)


def test_cache_cluster_uses_redis_on_a_single_micro_node(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ElastiCache::CacheCluster",
        {
            "Engine": "redis",
            "CacheNodeType": "cache.t3.micro",
            "NumCacheNodes": 1,
        },
    )


def test_cache_cluster_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::ElastiCache::CacheCluster", {"Tags": Match.array_with([tag])}
        )
