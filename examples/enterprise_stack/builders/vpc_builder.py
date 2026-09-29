"""VPC: the one network every network-attached builder in this cell shares
(Ec2, Ecs, Alb, Nlb - each `depends_on = ("vpc",)`).

Same `ec2.Vpc`/`ec2.SecurityGroup` calls verified in modules/03_vpc/stack.py.
Building it once and publishing it via `context.shared["vpc"]` is the
payoff this example has over the 4 independent copies those standalone
modules each keep for their own, separate lesson - see ../README.md,
"Without SOLID: what modules/13, 15, 30, 31 do on their own".
"""

from __future__ import annotations

from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class VpcResourceBuilder(ResourceBuilder):
    key = "vpc"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        vpc_name = resource_name(config.product, config.environment, cell, "vpc", "main")
        vpc = ec2.Vpc(
            scope,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                ec2.SubnetConfiguration(
                    name="private", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=24
                ),
            ],
        )
        apply_name_tag(vpc, vpc_name)

        app_sg_name = resource_name(config.product, config.environment, cell, "sg", "app")
        security_group = ec2.SecurityGroup(
            scope,
            "AppSecurityGroup",
            vpc=vpc,
            security_group_name=app_sg_name,
            description="Allows inbound HTTPS (443) from within the VPC only.",
            allow_all_outbound=True,
        )
        security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(443),
            description="HTTPS from inside the VPC",
        )
        apply_name_tag(security_group, app_sg_name)

        context.shared["vpc"] = vpc
        context.shared["app_security_group"] = security_group
