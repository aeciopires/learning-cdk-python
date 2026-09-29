"""Module 03 - VPC: subnets, security groups, and route tables.

AWS docs used while writing this module:
- Vpc construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html
- SecurityGroup construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SecurityGroup.html
- What Is Amazon VPC: https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html
- Route tables: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html

See README.md in this directory for the full explanation, deploy steps, and
what to look for in the floci UI after deploying.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

# Every module exposes STACK_CLASS + STACK_ID so app.py can discover and
# instantiate it without any module-specific code - see app.py.
STACK_ID = "VpcStack"


class VpcStack(Stack):
    """A 2-AZ VPC with public + private-isolated subnets and one security group.

    `ec2.Vpc` is the CDK L2 construct for Amazon VPC. By default it creates,
    for every Availability Zone selected by `max_azs`: one subnet per entry
    in `subnet_configuration`, an Internet Gateway attached to the VPC (used
    by the public subnets), and one route table per subnet with the routes
    already wired up - that automatic wiring is exactly what modules
    04 (Internet Gateway) and 05 (NAT Gateway) unpack manually, one resource
    at a time, using the same `aws_ec2` L1 (`Cfn*`) constructs `ec2.Vpc`
    itself uses under the hood.

    `nat_gateways=0` keeps this module free (a NAT Gateway bills hourly plus
    data processing - see module 05) and self-contained: the private subnets
    here are `PRIVATE_ISOLATED` (no outbound route to the internet at all),
    not `PRIVATE_WITH_EGRESS` (which needs a NAT Gateway).
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "main")

        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
        apply_name_tag(self.vpc, vpc_name)

        # One route table is created per subnet by ec2.Vpc; this shows how to
        # reach it to add a custom route (here, a placeholder VPC endpoint
        # route target is *not* added - this only proves the route table is
        # reachable and named, which is what beginners usually go looking for
        # first). Real custom routes are added in modules 05-07 (NAT Gateway,
        # Transit Gateway, VPC Peering), each against the route table of the
        # subnet that needs the new route.
        # NOTE: this VPC's second subnet group is PRIVATE_ISOLATED (see
        # subnet_configuration above), so CDK exposes it via
        # `vpc.isolated_subnets`, not `vpc.private_subnets` (that list is for
        # PRIVATE_WITH_EGRESS subnets - see module 05, NAT Gateway - and is
        # empty here).
        for index, subnet in enumerate(self.vpc.isolated_subnets):
            Stack.of(self).node.add_metadata(
                f"isolated-subnet-{index}-route-table-id",
                subnet.route_table.route_table_id,
            )

        app_security_group_name = resource_name(config.product, config.environment, "sg", "app")
        self.app_security_group = ec2.SecurityGroup(
            self,
            "AppSecurityGroup",
            vpc=self.vpc,
            security_group_name=app_security_group_name,
            description="Allows inbound HTTPS (443) from within the VPC only.",
            allow_all_outbound=True,
        )
        self.app_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="HTTPS from inside the VPC",
        )
        apply_name_tag(self.app_security_group, app_security_group_name)


STACK_CLASS = VpcStack
