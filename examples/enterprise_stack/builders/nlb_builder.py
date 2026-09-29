"""NLB: same `elbv2.NetworkLoadBalancer` calls verified in
modules/31_nlb/stack.py - except:

- the VPC, shared via `depends_on = ("vpc", ...)`;
- the target group, which registers this cell's actual ECS service
  (`depends_on = (..., "ecs")`) via `target_group.add_target(service)` -
  see the matching comment in alb_builder.py, same pattern, the
  `INetworkLoadBalancerTarget` interface instead of
  `IApplicationLoadBalancerTarget`.
"""

from __future__ import annotations

from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class NlbResourceBuilder(ResourceBuilder):
    key = "nlb"
    depends_on = ("vpc", "ecs")

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""
        vpc = context.shared["vpc"]

        # Same 32-character ELBv2 physical-name limit as alb_builder.py -
        # see the comment there for why the tag and the physical name use
        # two different, differently-sized values.
        nlb_tag_name = resource_name(config.product, config.environment, cell, "nlb", "tcp")
        nlb_physical_name = resource_name(config.environment, cell, "nlb", "tcp")
        load_balancer = elbv2.NetworkLoadBalancer(
            scope, "Nlb", vpc=vpc, internet_facing=True, load_balancer_name=nlb_physical_name
        )
        apply_name_tag(load_balancer, nlb_tag_name)

        tg_tag_name = resource_name(config.product, config.environment, cell, "tg", "tcp")
        tg_physical_name = resource_name(config.environment, cell, "tg", "tcp")
        target_group = elbv2.NetworkTargetGroup(
            scope,
            "NlbTargetGroup",
            vpc=vpc,
            port=80,
            protocol=elbv2.Protocol.TCP,
            target_type=elbv2.TargetType.IP,
            target_group_name=tg_physical_name,
        )
        apply_name_tag(target_group, tg_tag_name)
        target_group.add_target(context.shared["ecs_service"])

        elbv2.NetworkListener(
            scope,
            "NlbListener",
            load_balancer=load_balancer,
            port=80,
            protocol=elbv2.Protocol.TCP,
            default_target_groups=[target_group],
        )

        context.shared["nlb"] = load_balancer
