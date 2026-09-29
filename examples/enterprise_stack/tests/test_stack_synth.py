"""Synthesis-level tests - build EnterpriseCellStack with a fixed,
fake config (no AWS credentials, no Docker, no floci needed) and assert on
its synthesized CloudFormation template, the same `aws_cdk.assertions`
style every modules/NN_service test in this repository uses (see
docs/TESTING.md).
"""

from __future__ import annotations

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from examples.enterprise_stack.builders import build_default_registry
from examples.enterprise_stack.core.resource_registry import MissingDependencyError
from examples.enterprise_stack.stack import EnterpriseCellStack
from shared.config import AppConfig


def _config(cell_id: str) -> AppConfig:
    return AppConfig(
        product="test-product",
        environment="test",
        team_owner="platform-engineering",
        pci=False,
        cell_based=True,
        cell_id=cell_id,
    )


def test_only_enabled_resources_are_synthesized():
    app = cdk.App()
    stack = EnterpriseCellStack(
        app,
        "TestCell",
        config=_config("cell-01"),
        registry=build_default_registry(),
        enabled_keys={"s3", "sqs"},
    )
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::S3::Bucket", 1)
    template.resource_count_is("AWS::SQS::Queue", 2)  # the orders queue + its DLQ
    template.resource_count_is("AWS::EC2::VPC", 0)  # "vpc" was never enabled


def test_disabled_dependency_raises_before_synth():
    app = cdk.App()
    with pytest.raises(MissingDependencyError):
        EnterpriseCellStack(
            app,
            "TestCell",
            config=_config("cell-01"),
            registry=build_default_registry(),
            enabled_keys={"ec2"},  # "ec2" depends_on "vpc", which is missing
        )


def test_two_cells_produce_independently_named_resources():
    app = cdk.App()
    registry = build_default_registry()
    stack_a = EnterpriseCellStack(
        app, "CellA", config=_config("cell-01"), registry=registry, enabled_keys={"s3"}
    )
    stack_b = EnterpriseCellStack(
        app, "CellB", config=_config("cell-02"), registry=registry, enabled_keys={"s3"}
    )

    bucket_a = next(iter(Template.from_stack(stack_a).find_resources("AWS::S3::Bucket").values()))
    bucket_b = next(iter(Template.from_stack(stack_b).find_resources("AWS::S3::Bucket").values()))

    name_a = bucket_a["Properties"]["BucketName"]
    name_b = bucket_b["Properties"]["BucketName"]
    assert name_a != name_b
    assert "cell-01" in name_a
    assert "cell-02" in name_b


def test_lambda_reuses_the_iam_builders_role_not_its_own():
    app = cdk.App()
    stack = EnterpriseCellStack(
        app,
        "TestCell",
        config=_config("cell-01"),
        registry=build_default_registry(),
        enabled_keys={"iam", "lambda"},
    )
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::IAM::Role", 1)  # not 2 - lambda has no role of its own
    template.resource_count_is("AWS::Lambda::Function", 1)
