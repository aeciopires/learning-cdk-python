"""DynamoDB: same `dynamodb.Table` call verified in
modules/21_dynamodb/stack.py.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class DynamoDbResourceBuilder(ResourceBuilder):
    key = "dynamodb"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        table_name = resource_name(config.product, config.environment, cell, "ddb", "items")
        table = dynamodb.Table(
            scope,
            "Table",
            table_name=table_name,
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        apply_name_tag(table, table_name)

        context.shared["dynamodb_table"] = table
