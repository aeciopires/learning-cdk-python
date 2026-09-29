"""Module 15 - ECS (Fargate): a cluster, task definition, and service.

AWS docs used while writing this module:
- Cluster construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/Cluster.html
- FargateTaskDefinition: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/FargateTaskDefinition.html
- FargateService: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/FargateService.html
- ContainerImage: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/ContainerImage.html
- Amazon ECS - What is Amazon ECS: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html
- Amazon ECR Public Gallery - nginx (the image this module runs): https://gallery.ecr.aws/nginx/nginx

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "EcsStack"


class EcsStack(Stack):
    """A Fargate cluster running one public, unauthenticated nginx container.

    This module builds its own minimal, `PUBLIC`-subnet-only VPC (`max_azs=1`,
    `nat_gateways=0`) so the Fargate task can run without a NAT Gateway -
    `assign_public_ip=True` on the service gives each task's elastic network
    interface a public IP, so it can reach the internet (to pull
    `public.ecr.aws/nginx/nginx:latest`, a real, unauthenticated image on the
    Amazon ECR Public Gallery - see the link above) directly through the
    VPC's Internet Gateway, with no Application Load Balancer in front of it.

    This deliberately does **not** use
    `aws_cdk.aws_ecs_patterns.ApplicationLoadBalancedFargateService` - that
    higher-level pattern (cluster + service + Application Load Balancer, all
    in one construct) belongs conceptually to module 30 (ALB); this module
    stays focused on ECS/Fargate itself. See References for the pattern as a
    "production shortcut".
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "ecs")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            max_azs=1,
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

        cluster_name = resource_name(config.product, config.environment, "ecs", "cluster")
        self.cluster = ecs.Cluster(
            self,
            "Cluster",
            cluster_name=cluster_name,
            vpc=self.vpc,
        )
        apply_name_tag(self.cluster, cluster_name)

        task_definition_family = resource_name(config.product, config.environment, "ecs", "app-task")
        self.task_definition = ecs.FargateTaskDefinition(
            self,
            "AppTaskDefinition",
            family=task_definition_family,
            cpu=256,
            memory_limit_mib=512,
        )
        self.task_definition.add_container(
            "AppContainer",
            image=ecs.ContainerImage.from_registry("public.ecr.aws/nginx/nginx:latest"),
            port_mappings=[ecs.PortMapping(container_port=80)],
        )
        apply_name_tag(self.task_definition, task_definition_family)

        service_name = resource_name(config.product, config.environment, "ecs", "app-service")
        self.service = ecs.FargateService(
            self,
            "AppService",
            service_name=service_name,
            cluster=self.cluster,
            task_definition=self.task_definition,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            assign_public_ip=True,
            desired_count=1,
        )
        apply_name_tag(self.service, service_name)


STACK_CLASS = EcsStack
