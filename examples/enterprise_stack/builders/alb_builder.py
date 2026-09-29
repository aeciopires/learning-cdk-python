"""ALB: same `elbv2.ApplicationLoadBalancer` calls verified in
modules/30_alb/stack.py - except:

- the VPC, shared via `depends_on = ("vpc", ...)`;
- the target group, which registers this cell's actual ECS service
  (`depends_on = (..., "ecs")`) via `target_group.add_target(service)`
  instead of staying empty - `ecs.FargateService` implements
  `elbv2.IApplicationLoadBalancerTarget` directly (verified against the
  `aws-cdk-lib` source, `aws_cdk.aws_ecs.BaseService`), so no extra
  wiring is needed beyond this one call.
"""

from __future__ import annotations

from aws_cdk import aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class AlbResourceBuilder(ResourceBuilder):
    key = "alb"
    depends_on = ("vpc", "ecs")

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""
        vpc = context.shared["vpc"]

        # ELBv2 load balancer/target group *physical* names are capped at 32
        # characters by AWS - `cdk synth` rejects the full
        # product-environment-cell-purpose convention the moment a cell_id
        # is involved. The `Name` *tag* has no such limit, so it still gets
        # the full standard name via apply_name_tag(); only the short-lived
        # physical name is abbreviated (environment + cell + purpose).
        alb_tag_name = resource_name(config.product, config.environment, cell, "alb", "web")
        alb_physical_name = resource_name(config.environment, cell, "alb", "web")
        load_balancer = elbv2.ApplicationLoadBalancer(
            scope, "Alb", vpc=vpc, internet_facing=True, load_balancer_name=alb_physical_name
        )
        apply_name_tag(load_balancer, alb_tag_name)

        tg_tag_name = resource_name(config.product, config.environment, cell, "tg", "web")
        tg_physical_name = resource_name(config.environment, cell, "tg", "web")
        target_group = elbv2.ApplicationTargetGroup(
            scope,
            "AlbTargetGroup",
            vpc=vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.IP,
            target_group_name=tg_physical_name,
        )
        apply_name_tag(target_group, tg_tag_name)
        target_group.add_target(context.shared["ecs_service"])

        elbv2.ApplicationListener(
            scope,
            "AlbListener",
            load_balancer=load_balancer,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            default_target_groups=[target_group],
        )

        context.shared["alb"] = load_balancer
