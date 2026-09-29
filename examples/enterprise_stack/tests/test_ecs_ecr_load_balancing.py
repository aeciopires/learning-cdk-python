"""Synthesis-level tests for the ECR -> ECS (CPU autoscaling) -> ALB/NLB
chain: `ecr` stores the application image, `ecs` (`depends_on = ("vpc",
"ecr")`) runs it and scales 1-3 tasks on CPU utilization, and `alb`/`nlb`
(`depends_on = ("vpc", "ecs")`) each register that same service in their
target group. Same `aws_cdk.assertions` style as test_stack_synth.py.
"""

from __future__ import annotations

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from examples.enterprise_stack.builders import build_default_registry
from examples.enterprise_stack.builders.ecs_builder import EcsResourceBuilder
from examples.enterprise_stack.core.resource_registry import MissingDependencyError
from examples.enterprise_stack.stack import EnterpriseCellStack
from shared.config import AppConfig


def _config(cell_id: str = "cell-01") -> AppConfig:
    return AppConfig(
        product="test-product",
        environment="test",
        team_owner="platform-engineering",
        pci=False,
        cell_based=True,
        cell_id=cell_id,
    )


def _build(enabled_keys: set[str]) -> Template:
    app = cdk.App()
    stack = EnterpriseCellStack(
        app,
        "TestCell",
        config=_config(),
        registry=build_default_registry(),
        enabled_keys=enabled_keys,
    )
    return Template.from_stack(stack)


def test_ecs_depends_on_ecr_not_just_vpc():
    with pytest.raises(MissingDependencyError):
        _build({"vpc", "ecs"})  # "ecr" is missing


def test_alb_and_nlb_depend_on_ecs_not_just_vpc():
    with pytest.raises(MissingDependencyError):
        _build({"vpc", "alb"})  # "ecs" is missing
    with pytest.raises(MissingDependencyError):
        _build({"vpc", "nlb"})  # "ecs" is missing


def test_ecr_repository_is_scanned_and_cleanly_destroyable():
    template = _build({"vpc", "ecr", "ecs"})

    template.resource_count_is("AWS::ECR::Repository", 1)
    template.has_resource_properties(
        "AWS::ECR::Repository",
        {
            "ImageScanningConfiguration": {"ScanOnPush": True},
        },
    )
    # EmptyOnDelete/RemovalPolicy are CDK-only concepts, not synthesized as
    # literal template properties - they change what CloudFormation is told
    # to do on delete/replace via UpdateReplacePolicy/DeletionPolicy.
    ecr_resource = next(iter(template.find_resources("AWS::ECR::Repository").values()))
    assert ecr_resource["DeletionPolicy"] == "Delete"


def test_ecs_task_uses_the_ecr_repository_not_a_public_image():
    template = _build({"vpc", "ecr", "ecs"})

    task_def = next(iter(template.find_resources("AWS::ECS::TaskDefinition").values()))
    image = task_def["Properties"]["ContainerDefinitions"][0]["Image"]

    # ecs.ContainerImage.from_ecr_repository() always renders as an
    # Fn::Join built from the repository's own ARN/Fn::GetAtt (see
    # ecs_builder.py's docstring) - never a plain "public.ecr.aws/..." or
    # "docker.io/..." string literal.
    assert isinstance(image, dict) and "Fn::Join" in image
    serialized = str(image)
    assert "AppRepository" in serialized
    assert "public.ecr.aws" not in serialized
    assert "docker.io" not in serialized


def test_ecs_scales_one_to_three_tasks_on_cpu_utilization():
    template = _build({"vpc", "ecr", "ecs"})

    template.resource_count_is("AWS::ApplicationAutoScaling::ScalableTarget", 1)
    template.has_resource_properties(
        "AWS::ApplicationAutoScaling::ScalableTarget",
        {
            "ServiceNamespace": "ecs",
            "MinCapacity": EcsResourceBuilder.MIN_TASK_COUNT,
            "MaxCapacity": EcsResourceBuilder.MAX_TASK_COUNT,
        },
    )
    template.has_resource_properties(
        "AWS::ApplicationAutoScaling::ScalingPolicy",
        {
            "PolicyType": "TargetTrackingScaling",
            "TargetTrackingScalingPolicyConfiguration": Match.object_like(
                {
                    "TargetValue": EcsResourceBuilder.TARGET_CPU_UTILIZATION_PERCENT,
                    "PredefinedMetricSpecification": {
                        "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
                    },
                }
            ),
        },
    )


def test_alb_and_nlb_both_register_the_same_ecs_service():
    template = _build({"vpc", "ecr", "ecs", "alb", "nlb"})

    # One target group each - the whole point of this test is *which*
    # service ends up in AWS::ECS::Service's own LoadBalancers list, not
    # anything stored on the target groups themselves.
    template.resource_count_is("AWS::ElasticLoadBalancingV2::TargetGroup", 2)
    template.resource_count_is("AWS::ECS::Service", 1)

    service = next(iter(template.find_resources("AWS::ECS::Service").values()))
    load_balancers = service["Properties"]["LoadBalancers"]

    assert len(load_balancers) == 2
    for entry in load_balancers:
        assert entry["ContainerName"] == "AppContainer"
        assert entry["ContainerPort"] == 80


def test_alb_alone_still_works_without_nlb():
    template = _build({"vpc", "ecr", "ecs", "alb"})

    template.resource_count_is("AWS::ElasticLoadBalancingV2::TargetGroup", 1)
    service = next(iter(template.find_resources("AWS::ECS::Service").values()))
    assert len(service["Properties"]["LoadBalancers"]) == 1
