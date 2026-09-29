"""Module 24 - Kinesis: a Kinesis Data Streams stream with one shard.

AWS docs used while writing this module:
- Stream construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_kinesis/Stream.html
- Amazon Kinesis Data Streams - Key concepts (shards): https://docs.aws.amazon.com/streams/latest/dev/key-concepts.html
- Amazon Kinesis Data Streams pricing (per shard-hour + per-payload-unit): https://aws.amazon.com/kinesis/data-streams/pricing/

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_kinesis as kinesis
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "KinesisStack"


class KinesisStack(Stack):
    """One Kinesis Data Streams stream, provisioned mode, one shard, 24h retention.

    Kinesis Data Streams' default (provisioned) capacity mode bills per
    shard-hour whether or not any record is put or read - this module keeps
    that to the minimum, one shard, but see README.md's "Notes and cautions"
    for the real-AWS cost this still implies (unlike DynamoDB's
    pay-per-request mode in modules/21_dynamodb, there is no free-when-idle
    option for a provisioned-mode Kinesis stream).
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

        stream_name = resource_name(config.product, config.environment, "kinesis", "events")
        self.stream = kinesis.Stream(
            self,
            "Stream",
            stream_name=stream_name,
            shard_count=1,
            retention_period=Duration.hours(24),
            removal_policy=RemovalPolicy.DESTROY,
        )
        apply_name_tag(self.stream, stream_name)


STACK_CLASS = KinesisStack
