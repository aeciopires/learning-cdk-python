"""Module 31 - NLB: a Network Load Balancer with an empty target group.

AWS docs used while writing this module:
- NetworkLoadBalancer construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/NetworkLoadBalancer.html
- NetworkListener construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/NetworkListener.html
- NetworkTargetGroup construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/NetworkTargetGroup.html
- Vpc construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html
- What is a Network Load Balancer?: https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html

See README.md in this directory for the full explanation, including how an
NLB compares to the ALB built in module 30, and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "NlbStack"


class NlbStack(Stack):
    """An internet-facing Network Load Balancer, listener, and empty target group.

    Same shape as module 30 (ALB): its own small VPC (public subnets only,
    no NAT Gateway), one listener, one target group with no targets
    registered yet - a real deployment would register the targets from
    module 13 (EC2) or module 15 (ECS), which is why they are not referenced
    here (every module in this learning path stays independent).

    The difference from module 30 is the layer the load balancer operates
    at: `elbv2.NetworkListener` here uses `protocol=elbv2.Protocol.TCP`
    (layer 4 - it forwards raw TCP connections) instead of
    `elbv2.ApplicationProtocol.HTTP` (layer 7 - it understands HTTP
    requests/headers). See README.md for a full ALB-vs-NLB comparison.
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "nlb")
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
            ],
        )
        apply_name_tag(self.vpc, vpc_name)

        nlb_name = resource_name(config.product, config.environment, "nlb", "tcp")
        self.load_balancer = elbv2.NetworkLoadBalancer(
            self,
            "Nlb",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name=nlb_name,
        )
        apply_name_tag(self.load_balancer, nlb_name)

        target_group_name = resource_name(config.product, config.environment, "tg", "tcp")
        self.target_group = elbv2.NetworkTargetGroup(
            self,
            "TargetGroup",
            vpc=self.vpc,
            port=80,
            protocol=elbv2.Protocol.TCP,
            target_type=elbv2.TargetType.IP,
            target_group_name=target_group_name,
            # No targets registered yet - see the class docstring above.
        )
        apply_name_tag(self.target_group, target_group_name)

        self.listener = elbv2.NetworkListener(
            self,
            "Listener",
            load_balancer=self.load_balancer,
            port=80,
            protocol=elbv2.Protocol.TCP,
            default_target_groups=[self.target_group],
        )


STACK_CLASS = NlbStack
