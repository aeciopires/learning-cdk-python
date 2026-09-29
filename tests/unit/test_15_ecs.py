"""Unit tests for modules/15_ecs. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

EcsStack = stack_class("15_ecs")


def _synth(config):
    app = cdk.App()
    stack = EcsStack(app, "TestEcsStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_cluster(config):
    template = _synth(config)
    template.resource_count_is("AWS::ECS::Cluster", 1)


def test_creates_exactly_one_task_definition(config):
    template = _synth(config)
    template.resource_count_is("AWS::ECS::TaskDefinition", 1)


def test_creates_exactly_one_service(config):
    template = _synth(config)
    template.resource_count_is("AWS::ECS::Service", 1)


def test_task_definition_is_fargate_with_the_nginx_image(config):
    """The whole point of this module: a Fargate task running the public nginx image."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ECS::TaskDefinition",
        {
            "RequiresCompatibilities": ["FARGATE"],
            "NetworkMode": "awsvpc",
            "Cpu": "256",
            "Memory": "512",
            "ContainerDefinitions": Match.array_with(
                [
                    Match.object_like(
                        {
                            "Image": "public.ecr.aws/nginx/nginx:latest",
                            "PortMappings": Match.array_with(
                                [Match.object_like({"ContainerPort": 80})]
                            ),
                        }
                    )
                ]
            ),
        },
    )


def test_service_runs_on_fargate_with_a_public_ip(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ECS::Service",
        {
            "LaunchType": "FARGATE",
            "DesiredCount": 1,
            "NetworkConfiguration": Match.object_like(
                {
                    "AwsvpcConfiguration": Match.object_like(
                        {"AssignPublicIp": "ENABLED"}
                    )
                }
            ),
        },
    )


def test_cluster_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::ECS::Cluster", {"Tags": Match.array_with([tag])}
        )
