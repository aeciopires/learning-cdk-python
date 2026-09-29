"""ECS: same `ecs.Cluster`/`ecs.FargateService` calls verified in
modules/15_ecs/stack.py - except:

- the VPC, shared via `depends_on = ("vpc", ...)` the same way
  ec2_builder.py reuses it;
- the container image, which comes from this cell's own ECR repository
  (`ecr_builder.py`, `depends_on = (..., "ecr")`) via
  `ecs.ContainerImage.from_ecr_repository()` instead of the public
  `nginx:alpine` image the standalone module uses - see
  `ecr_builder.py`'s docstring for how the image actually gets into that
  repository (a manual `docker push`, the same as modules/14_ecr's own
  README documents - CDK cannot do this step for you);
- CPU-based Application Auto Scaling, scaling the service between 1 and 3
  tasks - see MAX_TASK_COUNT/TARGET_CPU_UTILIZATION_PERCENT below and
  ../README.md, "Scaling: 1 to 3 tasks, driven by CPU" for what each
  method call does, verified against the `aws-cdk-lib` source
  (`BaseService.auto_scale_task_count()` /
  `ScalableTaskCount.scale_on_cpu_utilization()`, both in
  `aws_cdk.aws_ecs`).
"""

from __future__ import annotations

from aws_cdk import Duration
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class EcsResourceBuilder(ResourceBuilder):
    key = "ecs"
    depends_on = ("vpc", "ecr")

    #: Application Auto Scaling never runs fewer than this many tasks...
    MIN_TASK_COUNT = 1
    #: ...nor more than this many, no matter how high CPU utilization gets.
    MAX_TASK_COUNT = 3
    #: Target for the target-tracking scaling policy below - Application
    #: Auto Scaling adds tasks when the fleet's average CPU utilization
    #: rises above this and removes tasks when it's comfortably under it.
    TARGET_CPU_UTILIZATION_PERCENT = 70

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""
        vpc = context.shared["vpc"]
        repository = context.shared["ecr_repository"]

        cluster_name = resource_name(config.product, config.environment, cell, "ecs", "cluster")
        cluster = ecs.Cluster(scope, "Cluster", cluster_name=cluster_name, vpc=vpc)
        apply_name_tag(cluster, cluster_name)

        family = resource_name(config.product, config.environment, cell, "ecs", "app-task")
        task_definition = ecs.FargateTaskDefinition(
            scope, "AppTaskDefinition", family=family, cpu=256, memory_limit_mib=512
        )
        task_definition.add_container(
            "AppContainer",
            image=ecs.ContainerImage.from_ecr_repository(repository, "latest"),
            port_mappings=[ecs.PortMapping(container_port=80)],
        )
        apply_name_tag(task_definition, family)

        service_name = resource_name(config.product, config.environment, cell, "ecs", "app-service")
        service = ecs.FargateService(
            scope,
            "AppService",
            service_name=service_name,
            cluster=cluster,
            task_definition=task_definition,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            assign_public_ip=True,
            desired_count=self.MIN_TASK_COUNT,
        )
        apply_name_tag(service, service_name)

        scaling = service.auto_scale_task_count(
            min_capacity=self.MIN_TASK_COUNT, max_capacity=self.MAX_TASK_COUNT
        )
        scaling.scale_on_cpu_utilization(
            "CpuScaling",
            target_utilization_percent=self.TARGET_CPU_UTILIZATION_PERCENT,
            scale_in_cooldown=Duration.seconds(60),
            scale_out_cooldown=Duration.seconds(60),
        )

        context.shared["ecs_service"] = service
