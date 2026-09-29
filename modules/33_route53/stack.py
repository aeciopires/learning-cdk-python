"""Module 33 - Route 53: a private hosted zone with one A record.

AWS docs used while writing this module:
- PrivateHostedZone construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_route53/PrivateHostedZone.html
- ARecord construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_route53/ARecord.html
- RecordTarget construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_route53/RecordTarget.html
- Vpc construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html
- Working with private hosted zones: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zone-private.html
- Amazon Route 53 pricing: https://aws.amazon.com/route53/pricing/

See README.md in this directory for the full explanation - including why
this module defaults to a *private* hosted zone rather than a public one -
and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_route53 as route53
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "Route53Stack"


class Route53Stack(Stack):
    """A private hosted zone (DNS scoped to one VPC) with one A record.

    `route53.PrivateHostedZone` is the primary example in this module,
    instead of `route53.PublicHostedZone`, because a private hosted zone has
    **no hourly or monthly charge** - it only resolves names inside the VPC
    it is associated with, never on the public internet. A
    `PublicHostedZone` bills a small monthly fee for as long as it exists,
    regardless of query volume - see README.md's "Notes and cautions" for
    the current rate and why that is exactly why this module defaults to
    Private.

    This module builds its own small VPC (see modules/03_vpc for the
    pattern) because `PrivateHostedZone` requires a `vpc=` at creation time.
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "dns")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
        apply_name_tag(self.vpc, vpc_name)

        # Zone names are DNS labels, not free-form resource names, so this
        # is built directly from config.product/environment rather than via
        # resource_name() (which is meant for physical resource *names*, not
        # DNS domain names).
        zone_name = f"{config.product}.internal"
        self.hosted_zone = route53.PrivateHostedZone(
            self,
            "PrivateZone",
            zone_name=zone_name,
            vpc=self.vpc,
            comment=f"Private DNS for {config.product} ({config.environment}) - see modules/33_route53/README.md.",
        )
        apply_name_tag(
            self.hosted_zone,
            resource_name(config.product, config.environment, "route53", "private-zone"),
        )

        self.a_record = route53.ARecord(
            self,
            "AppRecord",
            zone=self.hosted_zone,
            record_name="app",
            target=route53.RecordTarget.from_ip_addresses("10.0.0.10"),
            comment="Example record: app.<zone_name> -> 10.0.0.10.",
        )


STACK_CLASS = Route53Stack
