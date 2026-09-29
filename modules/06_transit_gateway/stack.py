"""Module 06 - Transit Gateway: connecting two VPCs through a shared hub.

AWS docs used while writing this module:
- Transit gateways: https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html
- AWS::EC2::TransitGateway: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgateway.html
- AWS::EC2::TransitGatewayVpcAttachment: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgatewayvpcattachment.html
- AWS::EC2::TransitGatewayRouteTable: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgatewayroutetable.html
- AWS::EC2::TransitGatewayRouteTableAssociation: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgatewayroutetableassociation.html
- AWS::EC2::TransitGatewayRoute: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgatewayroute.html
- CfnTransitGateway* construct family (Python): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnTransitGateway.html

Every property name below was verified against the CloudFormation reference
pages above (and cross-checked against the installed aws-cdk-lib 2.271.0
package's own constructor signatures) before being used - none of the
Transit Gateway constructs have an L2 in aws-cdk-lib, only these L1 (`Cfn*`)
ones, so that is what this module uses throughout.

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "TransitGatewayStack"


class TransitGatewayStack(Stack):
    """A Transit Gateway hub connecting two small VPCs, with an explicit route table.

    None of `AWS::EC2::TransitGateway*` has an L2 construct in aws-cdk-lib -
    this whole module is L1 (`Cfn*`), a 1:1 mapping to the CloudFormation
    resource types (see the module docstring for the exact reference pages
    checked).

    When you create a Transit Gateway, AWS creates a *default* transit
    gateway route table for it automatically - but the CDK's `CfnTransitGateway`
    construct has no attribute exposing that default table's id (it is only
    ever visible in the CloudFormation-generated template, and even the
    CloudFormation resource itself has no documented `Fn::GetAtt` for it, see
    the `AWS::EC2::TransitGateway` reference above under "Return values").
    Rather than guess at an undocumented way to reach it, this module creates
    its own **explicit** `ec2.CfnTransitGatewayRouteTable`, associates both
    VPC attachments with it, and adds routes to it by hand - the honest,
    documented way to control transit gateway routing from CDK.

    Both VPCs are `PRIVATE_ISOLATED`-only (no NAT Gateway, no Internet
    Gateway) - this module is about the Transit Gateway's own routing, not
    about internet access, and staying isolated keeps it free to run.
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

        tgw_name = resource_name(config.product, config.environment, "tgw", "hub")
        self.transit_gateway = ec2.CfnTransitGateway(
            self,
            "TransitGateway",
            description=f"Transit gateway hub for the {config.product} learning module - see modules/06_transit_gateway/README.md.",
        )
        apply_name_tag(self.transit_gateway, tgw_name)

        self.vpc_a = self._build_vpc(config, suffix="a", cidr="10.10.0.0/16")
        self.vpc_b = self._build_vpc(config, suffix="b", cidr="10.20.0.0/16")

        attachment_a_name = resource_name(config.product, config.environment, "tgw-attachment", "a")
        self.attachment_a = ec2.CfnTransitGatewayVpcAttachment(
            self,
            "VpcAAttachment",
            transit_gateway_id=self.transit_gateway.ref,
            vpc_id=self.vpc_a.vpc_id,
            subnet_ids=[subnet.subnet_id for subnet in self.vpc_a.isolated_subnets],
        )
        apply_name_tag(self.attachment_a, attachment_a_name)

        attachment_b_name = resource_name(config.product, config.environment, "tgw-attachment", "b")
        self.attachment_b = ec2.CfnTransitGatewayVpcAttachment(
            self,
            "VpcBAttachment",
            transit_gateway_id=self.transit_gateway.ref,
            vpc_id=self.vpc_b.vpc_id,
            subnet_ids=[subnet.subnet_id for subnet in self.vpc_b.isolated_subnets],
        )
        apply_name_tag(self.attachment_b, attachment_b_name)

        route_table_name = resource_name(config.product, config.environment, "tgw-route-table", "main")
        self.route_table = ec2.CfnTransitGatewayRouteTable(
            self,
            "TransitGatewayRouteTable",
            transit_gateway_id=self.transit_gateway.ref,
        )
        apply_name_tag(self.route_table, route_table_name)

        self.association_a = ec2.CfnTransitGatewayRouteTableAssociation(
            self,
            "VpcAAssociation",
            transit_gateway_attachment_id=self.attachment_a.ref,
            transit_gateway_route_table_id=self.route_table.ref,
        )
        self.association_b = ec2.CfnTransitGatewayRouteTableAssociation(
            self,
            "VpcBAssociation",
            transit_gateway_attachment_id=self.attachment_b.ref,
            transit_gateway_route_table_id=self.route_table.ref,
        )

        # Each VPC's CIDR is reachable through the *other* VPC's attachment -
        # that is what makes this a hub: traffic from A to B's CIDR exits
        # through B's attachment, and vice versa.
        self.route_to_vpc_b = ec2.CfnTransitGatewayRoute(
            self,
            "RouteToVpcB",
            transit_gateway_route_table_id=self.route_table.ref,
            destination_cidr_block="10.20.0.0/16",
            transit_gateway_attachment_id=self.attachment_b.ref,
        )
        self.route_to_vpc_a = ec2.CfnTransitGatewayRoute(
            self,
            "RouteToVpcA",
            transit_gateway_route_table_id=self.route_table.ref,
            destination_cidr_block="10.10.0.0/16",
            transit_gateway_attachment_id=self.attachment_a.ref,
        )

    def _build_vpc(self, config: AppConfig, *, suffix: str, cidr: str) -> ec2.Vpc:
        vpc_name = resource_name(config.product, config.environment, "vpc", f"tgw-{suffix}")
        vpc = ec2.Vpc(
            self,
            f"Vpc{suffix.upper()}",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr(cidr),
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
        apply_name_tag(vpc, vpc_name)
        return vpc


STACK_CLASS = TransitGatewayStack
