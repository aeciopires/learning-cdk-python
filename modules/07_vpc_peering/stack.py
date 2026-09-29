"""Module 07 - VPC Peering: a direct, non-transitive connection between two VPCs.

AWS docs used while writing this module:
- VPC peering: https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html
- CfnVPCPeeringConnection construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnVPCPeeringConnection.html
- CfnRoute construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html
- CfnResource.add_resource_dependency: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/CfnResource.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "VpcPeeringStack"


class VpcPeeringStack(Stack):
    """Two non-overlapping VPCs connected by a VPC peering connection.

    `aws_ec2` has no L2 construct for VPC peering - `ec2.CfnVPCPeeringConnection`
    (L1, a 1:1 mapping to `AWS::EC2::VPCPeeringConnection`) is what this
    module uses; see the module docstring for the API reference page.

    Unlike a Transit Gateway (module 06), a peering connection is **not** a
    hub: it connects exactly two VPCs directly, and it is **not transitive**
    - if a third VPC were peered to `vpc_b`, it still could not reach
    `vpc_a` through `vpc_b` without its own, separate peering connection to
    `vpc_a`. This is the main operational difference to remember when
    choosing between the two.

    `CfnRoute.vpc_peering_connection_id` references the peering connection
    directly, so CloudFormation already infers the route-depends-on-peering
    ordering from that `Ref` alone - unlike module 04 (Internet Gateway),
    where the route's properties never reference the attachment at all. This
    module still adds the dependency explicitly with
    `add_resource_dependency()`, both to make the requirement visible in the
    code (a peering connection can take a moment to leave `pending-acceptance`
    for `active` even for same-account/same-region peering, which is what
    this module creates) and as the pattern to copy for a cross-account or
    cross-region peering connection, where acceptance is not automatic.
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

        vpc_a_name = resource_name(config.product, config.environment, "vpc", "peer-a")
        self.vpc_a = ec2.Vpc(
            self,
            "VpcA",
            vpc_name=vpc_a_name,
            ip_addresses=ec2.IpAddresses.cidr("10.30.0.0/16"),
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
        apply_name_tag(self.vpc_a, vpc_a_name)

        vpc_b_name = resource_name(config.product, config.environment, "vpc", "peer-b")
        self.vpc_b = ec2.Vpc(
            self,
            "VpcB",
            vpc_name=vpc_b_name,
            ip_addresses=ec2.IpAddresses.cidr("10.40.0.0/16"),
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
        apply_name_tag(self.vpc_b, vpc_b_name)

        peering_name = resource_name(config.product, config.environment, "vpc-peering", "a-to-b")
        self.peering_connection = ec2.CfnVPCPeeringConnection(
            self,
            "PeeringConnection",
            vpc_id=self.vpc_a.vpc_id,
            peer_vpc_id=self.vpc_b.vpc_id,
        )
        apply_name_tag(self.peering_connection, peering_name)

        # vpc_a's route table gets a route to vpc_b's CIDR, and vice versa -
        # peering is symmetric, so both sides need their own route.
        self.route_a_to_b = ec2.CfnRoute(
            self,
            "VpcARouteToVpcB",
            route_table_id=self.vpc_a.isolated_subnets[0].route_table.route_table_id,
            destination_cidr_block="10.40.0.0/16",
            vpc_peering_connection_id=self.peering_connection.ref,
        )
        self.route_a_to_b.add_resource_dependency(self.peering_connection)

        self.route_b_to_a = ec2.CfnRoute(
            self,
            "VpcBRouteToVpcA",
            route_table_id=self.vpc_b.isolated_subnets[0].route_table.route_table_id,
            destination_cidr_block="10.30.0.0/16",
            vpc_peering_connection_id=self.peering_connection.ref,
        )
        self.route_b_to_a.add_resource_dependency(self.peering_connection)


STACK_CLASS = VpcPeeringStack
