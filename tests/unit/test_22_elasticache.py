"""Unit tests for modules/22_elasticache. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

ElastiCacheStack = stack_class("22_elasticache")


def _synth(config):
    app = cdk.App()
    stack = ElastiCacheStack(app, "TestElastiCacheStack", config=config)
    return Template.from_stack(stack)


@pytest.fixture(autouse=True)
def default_engine(monkeypatch):
    """Every test starts from the default engine, whatever your shell exports."""
    monkeypatch.delenv("CDK_ELASTICACHE_ENGINE", raising=False)


def test_creates_one_replication_group_and_no_cache_cluster(config):
    template = _synth(config)
    template.resource_count_is("AWS::ElastiCache::ReplicationGroup", 1)
    # AWS::ElastiCache::CacheCluster can't run Valkey - see stack.py.
    template.resource_count_is("AWS::ElastiCache::CacheCluster", 0)


def test_creates_exactly_one_cache_subnet_group(config):
    template = _synth(config)
    template.resource_count_is("AWS::ElastiCache::SubnetGroup", 1)


def test_valkey_is_the_default_engine(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ElastiCache::ReplicationGroup",
        {
            "Engine": "valkey",
            "ReplicationGroupId": f"{config.product}-{config.environment}-valkey",
        },
    )


@pytest.mark.parametrize("engine", ["valkey", "redis", " REDIS "])
def test_engine_is_chosen_by_cdk_elasticache_engine(config, monkeypatch, engine):
    monkeypatch.setenv("CDK_ELASTICACHE_ENGINE", engine)
    expected = engine.strip().lower()

    template = _synth(config)

    template.has_resource_properties(
        "AWS::ElastiCache::ReplicationGroup",
        {
            "Engine": expected,
            "ReplicationGroupId": f"{config.product}-{config.environment}-{expected}",
        },
    )


def test_an_unknown_engine_is_rejected(config, monkeypatch):
    monkeypatch.setenv("CDK_ELASTICACHE_ENGINE", "memcached")
    with pytest.raises(ValueError, match="must be one of valkey, redis"):
        _synth(config)


@pytest.mark.parametrize("engine", ["valkey", "redis"])
def test_single_encrypted_micro_node_for_both_engines(config, monkeypatch, engine):
    monkeypatch.setenv("CDK_ELASTICACHE_ENGINE", engine)
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ElastiCache::ReplicationGroup",
        {
            "CacheNodeType": "cache.t3.micro",
            "NumCacheClusters": 1,
            "AutomaticFailoverEnabled": False,
            "TransitEncryptionEnabled": True,  # required for a new Valkey group
            "AtRestEncryptionEnabled": True,
        },
    )


def test_security_group_opens_6379_to_the_vpc_only(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "SecurityGroupIngress": [
                Match.object_like({"FromPort": 6379, "ToPort": 6379, "IpProtocol": "tcp"})
            ]
        },
    )


def test_switching_engine_does_not_change_the_security_group(config, monkeypatch):
    """A named security group can't be replaced ("already exists"), so the
    engine must not leak into anything that would force a replacement."""

    def security_group(engine):
        monkeypatch.setenv("CDK_ELASTICACHE_ENGINE", engine)
        return _synth(config).find_resources("AWS::EC2::SecurityGroup")

    assert security_group("valkey") == security_group("redis")


def test_replication_group_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::ElastiCache::ReplicationGroup", {"Tags": Match.array_with([tag])}
        )
