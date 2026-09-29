"""Module 05 - NAT Gateway: outbound-only internet access for private subnets.

AWS docs used while writing this module:
- NAT gateways: https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html
- NAT Gateway pricing (hourly + per-GB data processing): https://aws.amazon.com/vpc/pricing/
- CfnEIP construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnEIP.html
- CfnNatGateway construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnNatGateway.html
- CfnRoute construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html
- Vpc construct (for isolated_subnets / private_subnets, confirmed by introspecting the
  installed aws-cdk-lib 2.271.0 package - PRIVATE_ISOLATED subnets populate
  vpc.isolated_subnets, not vpc.private_subnets): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html

See README.md in this directory for the full explanation, deploy steps, and
- most importantly - the cost warning before deploying this to real AWS.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "NatGatewayStack"


class NatGatewayStack(Stack):
    """A VPC (public + isolated subnets) with a NAT Gateway wired up by hand.

    `ec2.Vpc(..., nat_gateways=N)` is the idiomatic, one-line way to get N
    NAT Gateways (one per AZ, by default) wired up automatically in
    production code - see the "Notes and cautions" section of README.md.
    This module sets `nat_gateways=0` and builds the same three resources
    that shortcut creates, one at a time with L1 (`Cfn*`) constructs, to
    show what it does under the hood:

    1. `ec2.CfnEIP` (`domain="vpc"`) - an Elastic IP address, the public
       address the NAT Gateway will use.
    2. `ec2.CfnNatGateway` - the NAT Gateway itself, placed in a *public*
       subnet (it needs a route to the internet itself) and bound to the
       Elastic IP via `allocation_id`.
    3. `ec2.CfnRoute` - a `0.0.0.0/0` route in a *private* subnet's route
       table, pointing at the NAT Gateway, so instances in that subnet can
       reach the internet outbound without a public IP of their own.

    Unlike module 04 (Internet Gateway), no manual `add_resource_dependency`
    call is needed here: `CfnNatGateway.allocation_id` references the EIP
    directly, and `CfnRoute.nat_gateway_id` references the NAT Gateway
    directly - CloudFormation infers both orderings automatically from those
    `Ref`/`Fn::GetAtt` references, because (unlike module 04's Internet
    Gateway attachment) there is no separate "attachment" resource sitting
    outside that reference chain.
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "nat-demo")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.2.0.0/16"),
            max_azs=1,
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

        eip_name = resource_name(config.product, config.environment, "eip", "nat")
        self.nat_eip = ec2.CfnEIP(self, "NatElasticIp", domain="vpc")
        apply_name_tag(self.nat_eip, eip_name)

        nat_name = resource_name(config.product, config.environment, "nat", "main")
        self.nat_gateway = ec2.CfnNatGateway(
            self,
            "NatGateway",
            subnet_id=self.vpc.public_subnets[0].subnet_id,
            allocation_id=self.nat_eip.attr_allocation_id,
        )
        apply_name_tag(self.nat_gateway, nat_name)

        # PRIVATE_ISOLATED subnets are exposed as vpc.isolated_subnets, not
        # vpc.private_subnets (confirmed against the installed aws-cdk-lib
        # package - see the module docstring).
        self.private_default_route = ec2.CfnRoute(
            self,
            "PrivateSubnetDefaultRoute",
            route_table_id=self.vpc.isolated_subnets[0].route_table.route_table_id,
            destination_cidr_block="0.0.0.0/0",
            nat_gateway_id=self.nat_gateway.ref,
        )


STACK_CLASS = NatGatewayStack
