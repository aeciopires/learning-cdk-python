"""Module 19 - RDS for PostgreSQL: a single-AZ managed PostgreSQL database instance.

AWS docs used while writing this module:
- DatabaseInstance construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstance.html
- DatabaseInstanceEngine construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstanceEngine.html
- PostgresEngineVersion construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/PostgresEngineVersion.html
  (checked directly against the installed aws-cdk-lib==2.271.0 source: the
  highest constant defined is VER_18_3, not marked deprecated - see
  README.md for how this was verified).
- Credentials construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/Credentials.html
- Amazon RDS - Overview of Amazon RDS: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html
- Amazon RDS pricing (hourly billing while the instance exists): https://aws.amazon.com/rds/postgresql/pricing/

See README.md in this directory for the full explanation, deploy steps, and
- most importantly for this module - the cost warning before deploying to a
real AWS account. This module is the same shape as modules/18_rds_mysql,
with the PostgreSQL engine instead of MySQL - see that module's stack.py
docstring for the reasoning behind the 2-AZ VPC and the generated-secret
credentials, not repeated here.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "RdsPostgresqlStack"


class RdsPostgresqlStack(Stack):
    """A small, dedicated VPC plus one db.t3.micro RDS for PostgreSQL instance.

    See modules/18_rds_mysql/stack.py for the full explanation of the 2-AZ
    VPC (required by RDS's DB subnet group even for a single-AZ instance),
    the `PRIVATE_ISOLATED` subnet placement, and the generated-secret
    credentials (ties into module 09, Secrets Manager).
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "rds-postgresql")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.21.0.0/16"),
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

        instance_name = resource_name(config.product, config.environment, "rds", "postgresql")
        self.database = rds.DatabaseInstance(
            self,
            "Database",
            instance_identifier=instance_name,
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_18_3),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            credentials=rds.Credentials.from_generated_secret("dbadmin"),
            allocated_storage=20,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
        )
        apply_name_tag(self.database, instance_name)


STACK_CLASS = RdsPostgresqlStack
