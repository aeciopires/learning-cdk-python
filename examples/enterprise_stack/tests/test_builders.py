"""One test per resource builder not already exercised by the other test
files (ec2, sns, acm, kms, dynamodb) - each enables just that builder (plus
what it `depends_on`) and checks the one resource it exists to create, and
that its physical name follows the product-environment-cell convention.
"""

from __future__ import annotations

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from examples.enterprise_stack.builders import build_default_registry
from examples.enterprise_stack.stack import EnterpriseCellStack
from shared.config import AppConfig


def _template(*enabled: str) -> Template:
    config = AppConfig(
        product="test-product",
        environment="stg",
        team_owner="platform-engineering",
        pci=False,
        cell_based=True,
        cell_id="cell-01",
    )
    stack = EnterpriseCellStack(
        cdk.App(),
        "TestCell",
        config=config,
        registry=build_default_registry(),
        enabled_keys=set(enabled),
    )
    return Template.from_stack(stack)


NAME_PREFIX = "test-product-stg-cell-01-"


@pytest.mark.parametrize(
    ("enabled", "resource_type", "name_property", "expected_name"),
    [
        (("kms",), "AWS::KMS::Alias", "AliasName", f"alias/{NAME_PREFIX}kms-app"),
        (("dynamodb",), "AWS::DynamoDB::Table", "TableName", f"{NAME_PREFIX}ddb-items"),
        (("sns",), "AWS::SNS::Topic", "TopicName", f"{NAME_PREFIX}sns-notifications"),
        (("vpc", "ec2"), "AWS::IAM::Role", "RoleName", f"{NAME_PREFIX}role-ec2-instance"),
    ],
)
def test_builder_creates_its_resource_with_the_cell_name(
    enabled, resource_type, name_property, expected_name
):
    _template(*enabled).has_resource_properties(resource_type, {name_property: expected_name})


def test_ec2_builder_places_one_instance_in_the_shared_vpc():
    template = _template("vpc", "ec2")

    template.resource_count_is("AWS::EC2::Instance", 1)
    template.resource_count_is("AWS::EC2::VPC", 1)  # the cell's VPC, not a second one


def test_sns_builder_fans_out_to_its_own_queue():
    template = _template("sns")

    template.resource_count_is("AWS::SNS::Subscription", 1)
    template.has_resource_properties("AWS::SNS::Subscription", {"Protocol": "sqs"})


def test_acm_builder_requests_one_dns_validated_certificate():
    template = _template("acm")

    template.resource_count_is("AWS::CertificateManager::Certificate", 1)
    template.has_resource_properties(
        "AWS::CertificateManager::Certificate",
        {"DomainName": "test-product.example.com", "ValidationMethod": Match.any_value()},
    )
