"""Module 30 - ALB: an Application Load Balancer with an empty target group.

AWS docs used while writing this module:
- ApplicationLoadBalancer construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationLoadBalancer.html
- ApplicationListener construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationListener.html
- ApplicationTargetGroup construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationTargetGroup.html
- Vpc construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html
- What is an Application Load Balancer?: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "AlbStack"


class AlbStack(Stack):
    """An internet-facing Application Load Balancer, listener, and empty target group.

    This module builds its own small VPC (public subnets only, no NAT
    Gateway - see modules/03_vpc for the pattern this follows) so it can be
    deployed on its own, independent of any other module's stack.

    The target group is created with `target_type=elbv2.TargetType.IP` and
    no registered targets - an empty target group is valid CloudFormation/
    CDK and synthesizes cleanly; it simply has nothing healthy to route
    traffic to yet. This module is deliberately just the load-balancing
    layer on its own: a real deployment would register the targets from
    module 13 (EC2) or module 15 (ECS) against this same target group (via
    `target_group.add_target(...)`), which is why those modules are not
    referenced here - every module in this learning path stays independent.
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "alb")
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

        alb_name = resource_name(config.product, config.environment, "alb", "web")
        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "Alb",
            vpc=self.vpc,
            internet_facing=True,
            load_balancer_name=alb_name,
        )
        apply_name_tag(self.load_balancer, alb_name)

        target_group_name = resource_name(config.product, config.environment, "tg", "web")
        self.target_group = elbv2.ApplicationTargetGroup(
            self,
            "TargetGroup",
            vpc=self.vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            target_group_name=target_group_name,
            # No targets registered yet - see the class docstring above.
        )
        apply_name_tag(self.target_group, target_group_name)

        self.listener = elbv2.ApplicationListener(
            self,
            "Listener",
            load_balancer=self.load_balancer,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_target_groups=[self.target_group],
        )


STACK_CLASS = AlbStack
