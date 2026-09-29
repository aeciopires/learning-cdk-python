"""Module 04 - Internet Gateway: wiring one up by hand with L1 constructs.

AWS docs used while writing this module:
- Internet gateways: https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html
- CfnInternetGateway construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnInternetGateway.html
- CfnVPCGatewayAttachment construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnVPCGatewayAttachment.html
- CfnRoute construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html
- CfnResource.add_resource_dependency: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/CfnResource.html
- Vpc construct (for isolated_subnets / private_subnets, confirmed by introspecting the
  installed aws-cdk-lib 2.271.0 package - PRIVATE_ISOLATED subnets populate
  vpc.isolated_subnets, not vpc.private_subnets): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html

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

STACK_ID = "InternetGatewayStack"


class InternetGatewayStack(Stack):
    """A VPC with only an isolated subnet, given internet access by hand.

    Module 03 (`ec2.Vpc` with a `PUBLIC` subnet) gets an Internet Gateway,
    the attachment that connects it to the VPC, and the default route for
    free - `ec2.Vpc` creates and wires all three of those for you the moment
    any subnet in `subnet_configuration` is `PUBLIC`. This module builds a
    VPC with **no** `PUBLIC` subnet (only `PRIVATE_ISOLATED`, so `ec2.Vpc`
    has no reason to create an Internet Gateway at all), then adds the same
    three resources one at a time with L1 (`Cfn*`) constructs - a 1:1
    mapping to the underlying CloudFormation resource types - to show
    exactly what module 03 was hiding:

    1. `ec2.CfnInternetGateway` - the gateway itself, not yet attached to
       anything.
    2. `ec2.CfnVPCGatewayAttachment` - attaches the gateway to the VPC. A
       gateway is a standalone resource until this attachment exists.
    3. `ec2.CfnRoute` - a `0.0.0.0/0` route in one subnet's route table,
       pointing at the gateway.

    The subtle part: `CfnRoute`'s properties reference the route table and
    the gateway (via `route_table_id` and `gateway_id`), but **not** the
    attachment - so CloudFormation's automatic "infer dependencies from
    Ref/GetAtt" mechanism never sees that the route needs the attachment to
    exist first. Route creation fails if CloudFormation happens to create it
    before the gateway is attached. `route.add_resource_dependency(attachment)`
    is how you tell CloudFormation about a dependency it cannot infer on its
    own - see the API reference link above (`add_dependency` also exists but
    is documented as deprecated in favor of `add_resource_dependency` as of
    aws-cdk-lib 2.271.0; this module uses the current one).
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "igw-demo")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.1.0.0/16"),
            max_azs=1,
            nat_gateways=0,
            # No PUBLIC subnet here on purpose - see the class docstring.
            # PRIVATE_ISOLATED subnets are exposed as vpc.isolated_subnets,
            # not vpc.private_subnets (confirmed against the installed
            # aws-cdk-lib package - see the module docstring).
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
        apply_name_tag(self.vpc, vpc_name)

        igw_name = resource_name(config.product, config.environment, "igw", "main")
        self.internet_gateway = ec2.CfnInternetGateway(self, "InternetGateway")
        apply_name_tag(self.internet_gateway, igw_name)

        # Standalone until this attachment exists - see the class docstring.
        self.attachment = ec2.CfnVPCGatewayAttachment(
            self,
            "InternetGatewayAttachment",
            vpc_id=self.vpc.vpc_id,
            internet_gateway_id=self.internet_gateway.ref,
        )

        # The one subnet this VPC has, made reachable from the internet by a
        # single 0.0.0.0/0 route toward the Internet Gateway.
        self.default_route = ec2.CfnRoute(
            self,
            "IsolatedSubnetDefaultRoute",
            route_table_id=self.vpc.isolated_subnets[0].route_table.route_table_id,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=self.internet_gateway.ref,
        )
        # Explicit dependency CloudFormation cannot infer on its own - see
        # the class docstring for why this line is required.
        self.default_route.add_resource_dependency(self.attachment)


STACK_CLASS = InternetGatewayStack
