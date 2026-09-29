"""Unit tests for modules/21_dynamodb. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

DynamoDbStack = stack_class("21_dynamodb")


def _synth(config):
    app = cdk.App()
    stack = DynamoDbStack(app, "TestDynamoDbStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_table(config):
    template = _synth(config)
    template.resource_count_is("AWS::DynamoDB::Table", 1)


def test_table_is_pay_per_request(config):
    """The whole point of this module - no idle baseline cost. See stack.py."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::DynamoDB::Table", {"BillingMode": "PAY_PER_REQUEST"}
    )


def test_table_has_a_single_string_partition_key(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "KeySchema": Match.array_with(
                [{"AttributeName": "pk", "KeyType": "HASH"}]
            ),
            "AttributeDefinitions": Match.array_with(
                [{"AttributeName": "pk", "AttributeType": "S"}]
            ),
        },
    )


def test_table_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::DynamoDB::Table", {"Tags": Match.array_with([tag])}
        )
