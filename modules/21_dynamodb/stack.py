"""Module 21 - DynamoDB: a pay-per-request table with a simple partition key.

AWS docs used while writing this module:
- Table construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html
- Attribute construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Attribute.html
- BillingMode enum: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/BillingMode.html
- Amazon DynamoDB - Core components: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html
- Amazon DynamoDB pricing (on-demand vs. provisioned): https://aws.amazon.com/dynamodb/pricing/

**Table vs. TableV2 note:** `aws_cdk.aws_dynamodb` also ships a newer
`TableV2` construct (built around a `billing=` prop and a `Billing` class,
primarily aimed at multi-Region global tables). This module deliberately
uses the classic `Table` construct instead: it is the long-stable,
single-purpose L2 for a single-Region table, its `billing_mode=`/
`BillingMode.PAY_PER_REQUEST` shape matches what most of the CDK's own
examples still use, and this module does not need `TableV2`'s multi-Region
replica features. See README.md for more.

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "DynamoDbStack"


class DynamoDbStack(Stack):
    """One DynamoDB table, billed per request, with a single string partition key.

    `billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST` (DynamoDB's
    "on-demand" capacity mode) means there is no hourly or per-capacity-unit
    charge while the table is idle - unlike every RDS/Aurora/ElastiCache/
    OpenSearch module in this learning path, this one has no baseline cost
    on a real AWS account as long as nothing reads or writes to it.
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

        table_name = resource_name(config.product, config.environment, "ddb", "items")
        self.table = dynamodb.Table(
            self,
            "Table",
            table_name=table_name,
            partition_key=dynamodb.Attribute(name="pk", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        apply_name_tag(self.table, table_name)


STACK_CLASS = DynamoDbStack
