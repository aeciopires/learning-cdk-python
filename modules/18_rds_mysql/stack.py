"""Module 18 - RDS for MySQL: a single-AZ managed MySQL database instance.

AWS docs used while writing this module:
- DatabaseInstance construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstance.html
- DatabaseInstanceEngine construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstanceEngine.html
- MysqlEngineVersion construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/MysqlEngineVersion.html
  (checked directly against the installed aws-cdk-lib==2.271.0 source: the
  highest non-deprecated constant is VER_8_4_10 - see README.md for how this
  was verified and why VER_8_0_x constants still exist but are older minor
  versions, not deprecated).
- Credentials construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/Credentials.html
- Amazon RDS - Overview of Amazon RDS: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html
- Amazon RDS pricing (hourly billing while the instance exists): https://aws.amazon.com/rds/mysql/pricing/

See README.md in this directory for the full explanation, deploy steps, and
- most importantly for this module - the cost warning before deploying to a
real AWS account.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "RdsMysqlStack"


class RdsMysqlStack(Stack):
    """A small, dedicated VPC plus one db.t3.micro RDS for MySQL instance.

    This module builds its own 2-AZ VPC rather than referencing another
    module's stack (see modules/03_vpc for the full VPC walkthrough). Two
    Availability Zones are used - not one - because Amazon RDS requires a DB
    subnet group to span at least two AZs, even for a single-AZ instance
    deployment (`multi_az` is left at its default of `False` here, so only
    one AZ actually hosts the running instance - the second AZ's subnet only
    satisfies the subnet group requirement).

    The instance is placed in `PRIVATE_ISOLATED` subnets (no route to the
    internet at all, and no NAT Gateway - see modules/03_vpc and
    modules/05_nat_gateway), which is the right default for a database that
    only ever needs to be reached from inside the VPC.

    `rds.Credentials.from_generated_secret("admin")` does not set a password
    in this code at all: it tells CDK to generate a random password and
    store it as a new AWS Secrets Manager secret, then wires the DB
    instance's master password to that secret automatically. This is the
    same service module 09 (Secrets Manager) teaches on its own - this is
    what it looks like used automatically by another service, instead of
    created and read back by hand.
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "rds-mysql")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.20.0.0/16"),
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

        instance_name = resource_name(config.product, config.environment, "rds", "mysql")
        self.database = rds.DatabaseInstance(
            self,
            "Database",
            instance_identifier=instance_name,
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_4_10),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            credentials=rds.Credentials.from_generated_secret("admin"),
            allocated_storage=20,
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False,
        )
        apply_name_tag(self.database, instance_name)


STACK_CLASS = RdsMysqlStack
