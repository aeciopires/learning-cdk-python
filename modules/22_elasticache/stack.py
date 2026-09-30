"""Module 22 - ElastiCache: a single-node Valkey or Redis OSS cache.

AWS docs used while writing this module:
- CfnReplicationGroup construct (L1 - see note below): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnReplicationGroup.html
- CfnSubnetGroup construct (L1): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnSubnetGroup.html
- AWS::ElastiCache::ReplicationGroup (Engine: "valkey" or "redis"; TransitEncryptionEnabled is required for a new Valkey group): https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-elasticache-replicationgroup.html
- AWS::ElastiCache::CacheCluster (Engine: "memcached" or "redis" only - "To create a Valkey cluster, use AWS::ElastiCache::ReplicationGroup"): https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-elasticache-cachecluster.html
- Amazon ElastiCache - What is Amazon ElastiCache?: https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.html
- Amazon ElastiCache pricing (hourly per node): https://aws.amazon.com/elasticache/pricing/

**L1-only note:** `aws_cdk.aws_elasticache` has **no L2 (curated) construct**
- unlike `aws_ec2.Vpc` or `aws_rds.DatabaseInstance`, there is no
`elasticache.ReplicationGroup` class wrapping sensible defaults. This module
therefore uses the L1 `Cfn*` constructs directly (`CfnReplicationGroup`,
`CfnSubnetGroup`), which are a 1:1 mapping to the underlying
`AWS::ElastiCache::ReplicationGroup` / `AWS::ElastiCache::SubnetGroup`
CloudFormation resource types - see CLAUDE.md section 4, point 2, for why
this repository always says so explicitly when it happens.

**Choosing the engine:** set `CDK_ELASTICACHE_ENGINE` to `valkey` (the
default) or `redis` before `cdk synth`/`cdk deploy` - see .env.example and
README.md. Both engines speak the same protocol on port 6379, so the only
thing that changes is the `Engine` property and the resource names.

See README.md in this directory for the full explanation, deploy steps, and
the real-AWS cost warning (ElastiCache nodes bill hourly the moment they
exist, like RDS).
"""

from __future__ import annotations

import os

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticache as elasticache
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "ElastiCacheStack"

# The two engines AWS::ElastiCache::ReplicationGroup accepts - see the
# CloudFormation reference linked above. The first one is the default.
ENGINES: tuple[str, ...] = ("valkey", "redis")
ENGINE_ENV_VAR = "CDK_ELASTICACHE_ENGINE"


def engine_from_env() -> str:
    """Return the engine named by CDK_ELASTICACHE_ENGINE (default: "valkey").

    Raises ValueError for anything other than "valkey" or "redis", so a typo
    fails at `cdk synth` instead of at deploy time.
    """
    engine = os.getenv(ENGINE_ENV_VAR, ENGINES[0]).strip().lower()
    if engine not in ENGINES:
        raise ValueError(
            f"Invalid {ENGINE_ENV_VAR}={engine!r}: must be one of {', '.join(ENGINES)}"
        )
    return engine


class ElastiCacheStack(Stack):
    """A small, dedicated single-AZ VPC plus one cache.t3.micro Valkey/Redis OSS node.

    A single Availability Zone is enough here (`max_azs=1`): unlike RDS/
    Aurora's DB subnet group, ElastiCache's cache subnet group has no
    requirement to span multiple AZs for a single-node cache - see
    modules/18_rds_mysql/stack.py for the contrasting case where AWS *does*
    require 2 AZs.

    Why a replication group, not a cache cluster: `AWS::ElastiCache::
    CacheCluster` (the resource this module used before) only accepts the
    `memcached` and `redis` engines. `AWS::ElastiCache::ReplicationGroup`
    accepts both `valkey` and `redis`, so it is the one resource that lets
    this module switch engines. With `num_cache_clusters=1` it is still a
    single node - a "replication group" with only a primary and no replicas.
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

        self.engine = engine_from_env()

        vpc_name = resource_name(config.product, config.environment, "vpc", "elasticache")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.23.0.0/16"),
            max_azs=1,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
        apply_name_tag(self.vpc, vpc_name)

        sg_name = resource_name(config.product, config.environment, "sg", "elasticache")
        self.security_group = ec2.SecurityGroup(
            self,
            "CacheSecurityGroup",
            vpc=self.vpc,
            security_group_name=sg_name,
            # Deliberately engine-neutral: changing a security group's
            # description replaces it, and a named security group can't be
            # replaced in place ("already exists") - so this text must not
            # change when CDK_ELASTICACHE_ENGINE does.
            description="Allows inbound Valkey/Redis OSS (6379) from within the VPC only.",
            allow_all_outbound=True,
        )
        # Valkey is compatible with Redis OSS clients, and this module serves
        # both engines on the same port, so one rule covers both.
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description="Valkey/Redis OSS from inside the VPC",
        )
        apply_name_tag(self.security_group, sg_name)

        subnet_group_name = resource_name(config.product, config.environment, "cache-subnet")
        self.subnet_group = elasticache.CfnSubnetGroup(
            self,
            "CacheSubnetGroup",
            description="Subnet group for the learning path's ElastiCache node.",
            subnet_ids=self.vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ).subnet_ids,
            cache_subnet_group_name=subnet_group_name,
        )
        apply_name_tag(self.subnet_group, subnet_group_name)

        # ReplicationGroupId: 1-40 characters, must start with a letter (see
        # the CloudFormation reference above) - e.g. "learning-cdk-python-dev-valkey".
        group_id = resource_name(config.product, config.environment, self.engine)
        self.replication_group = elasticache.CfnReplicationGroup(
            self,
            "ReplicationGroup",
            replication_group_id=group_id,
            replication_group_description=f"Learning path single-node {self.engine} cache.",
            engine=self.engine,
            cache_node_type="cache.t3.micro",
            num_cache_clusters=1,
            automatic_failover_enabled=False,  # needs >= 2 nodes - see Notes and cautions
            cache_subnet_group_name=self.subnet_group.ref,
            security_group_ids=[self.security_group.security_group_id],
            # Required when creating a Valkey replication group, and good
            # practice for Redis OSS too - so both engines behave the same.
            transit_encryption_enabled=True,
            at_rest_encryption_enabled=True,
        )
        # add_dependency() is deprecated in aws-cdk-lib in favor of
        # add_resource_dependency() - see modules/04_internet_gateway/stack.py
        # for the same fix applied to another Cfn* construct.
        self.replication_group.add_resource_dependency(self.subnet_group)
        apply_name_tag(self.replication_group, group_id)


STACK_CLASS = ElastiCacheStack
