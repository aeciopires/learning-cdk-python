"""Module 22 - ElastiCache: a single-node Redis OSS cache cluster.

AWS docs used while writing this module:
- CfnCacheCluster construct (L1 - see note below): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnCacheCluster.html
- CfnSubnetGroup construct (L1): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnSubnetGroup.html
- Amazon ElastiCache - What is Amazon ElastiCache?: https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/WhatIs.html
- Amazon ElastiCache pricing (hourly per node): https://aws.amazon.com/elasticache/pricing/

**L1-only note:** `aws_cdk.aws_elasticache` has **no L2 (curated) construct**
- unlike `aws_ec2.Vpc` or `aws_rds.DatabaseInstance`, there is no
`elasticache.CacheCluster` class wrapping sensible defaults. This module
therefore uses the L1 `Cfn*` constructs directly (`CfnCacheCluster`,
`CfnSubnetGroup`), which are a 1:1 mapping to the underlying
`AWS::ElastiCache::CacheCluster` / `AWS::ElastiCache::SubnetGroup`
CloudFormation resource types - see CLAUDE.md section 4, point 2, for why
this repository always says so explicitly when it happens.

See README.md in this directory for the full explanation, deploy steps, and
the real-AWS cost warning (ElastiCache nodes bill hourly the moment they
exist, like RDS).
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticache as elasticache
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "ElastiCacheStack"


class ElastiCacheStack(Stack):
    """A small, dedicated single-AZ VPC plus one cache.t3.micro Redis OSS node.

    A single Availability Zone is enough here (`max_azs=1`): unlike RDS/
    Aurora's DB subnet group, ElastiCache's cache subnet group has no
    requirement to span multiple AZs for a single-node cluster - see
    modules/18_rds_mysql/stack.py for the contrasting case where AWS *does*
    require 2 AZs.
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
            description="Allows inbound Redis (6379) from within the VPC only.",
            allow_all_outbound=True,
        )
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description="Redis from inside the VPC",
        )
        apply_name_tag(self.security_group, sg_name)

        subnet_group_name = resource_name(config.product, config.environment, "cache-subnet")
        self.subnet_group = elasticache.CfnSubnetGroup(
            self,
            "CacheSubnetGroup",
            description="Subnet group for the learning path's ElastiCache Redis OSS node.",
            subnet_ids=self.vpc.select_subnets(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ).subnet_ids,
            cache_subnet_group_name=subnet_group_name,
        )
        apply_name_tag(self.subnet_group, subnet_group_name)

        cluster_name = resource_name(config.product, config.environment, "redis")
        self.cache_cluster = elasticache.CfnCacheCluster(
            self,
            "CacheCluster",
            cluster_name=cluster_name,
            cache_node_type="cache.t3.micro",
            engine="redis",
            num_cache_nodes=1,
            cache_subnet_group_name=self.subnet_group.ref,
            vpc_security_group_ids=[self.security_group.security_group_id],
        )
        # add_dependency() is deprecated in aws-cdk-lib in favor of
        # add_resource_dependency() - see modules/04_internet_gateway/stack.py
        # for the same fix applied to another Cfn* construct.
        self.cache_cluster.add_resource_dependency(self.subnet_group)
        apply_name_tag(self.cache_cluster, cluster_name)


STACK_CLASS = ElastiCacheStack
