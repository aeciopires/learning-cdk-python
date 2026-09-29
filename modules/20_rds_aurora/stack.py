"""Module 20 - Aurora: a PostgreSQL-compatible Aurora cluster with one writer instance.

AWS docs used while writing this module:
- DatabaseCluster construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseCluster.html
- ClusterInstance construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/ClusterInstance.html
- DatabaseClusterEngine construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseClusterEngine.html
- AuroraPostgresEngineVersion construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/AuroraPostgresEngineVersion.html
- Credentials construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/Credentials.html
- Amazon Aurora User Guide: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/CHAP_AuroraOverview.html
- Amazon Aurora pricing (hourly per instance, typically pricier than
  standalone RDS): https://aws.amazon.com/rds/aurora/pricing/

**API-churn note (checked directly against the installed aws-cdk-lib==2.271.0
source in .venv, not recalled from memory):** `DatabaseCluster`/
`DatabaseClusterProps` still accept the older `instances=<int>` and
`instance_props=` combination, but that shape is documented in the CDK
source only for `DatabaseClusterFromSnapshot` back-compat and is superseded
by `writer=`/`readers=`. This stack uses the current, non-deprecated shape:
`writer=rds.ClusterInstance.provisioned("Writer", instance_type=...)`, with
no `readers=` (a single-instance cluster, to keep this module's cost as low
as an Aurora cluster gets - see README.md).

See README.md in this directory for the full explanation, deploy steps, and
- most importantly for this module - the cost warning before deploying to a
real AWS account (Aurora is typically pricier than standalone RDS for an
equivalent instance size).
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "RdsAuroraStack"


class RdsAuroraStack(Stack):
    """A small, dedicated 2-AZ VPC plus one Aurora PostgreSQL cluster (one writer, no readers).

    See modules/18_rds_mysql/stack.py for the reasoning behind the 2-AZ VPC
    (Aurora clusters, like standalone RDS instances, need a DB subnet group
    spanning at least two Availability Zones) and the `PRIVATE_ISOLATED`
    subnet placement.

    Unlike modules 18/19 (`rds.DatabaseInstance`, one instance), this module
    uses `rds.DatabaseCluster` - Aurora's storage layer is a separate,
    cluster-level resource shared by one or more compute instances attached
    to it. `writer=` provisions the one required instance; `readers=` is
    left unset, since a read replica is a second billed instance and this
    module's goal is to show the cluster/instance split at the lowest
    possible cost, not to demonstrate read scaling.
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "rds-aurora")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.22.0.0/16"),
            max_azs=2,
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

        cluster_name = resource_name(config.product, config.environment, "rds", "aurora")
        self.cluster = rds.DatabaseCluster(
            self,
            "Cluster",
            cluster_identifier=cluster_name,
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_17_9
            ),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            credentials=rds.Credentials.from_generated_secret("dbadmin"),
            writer=rds.ClusterInstance.provisioned(
                "Writer",
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )
        apply_name_tag(self.cluster, cluster_name)


STACK_CLASS = RdsAuroraStack
