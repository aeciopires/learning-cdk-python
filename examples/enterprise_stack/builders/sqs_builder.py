"""SQS: same `sqs.Queue`/dead-letter-queue calls verified in
modules/26_sqs/stack.py.
"""

from __future__ import annotations

from aws_cdk import aws_sqs as sqs
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class SqsResourceBuilder(ResourceBuilder):
    key = "sqs"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        dlq_name = resource_name(config.product, config.environment, cell, "sqs", "orders-dlq")
        dead_letter_queue = sqs.Queue(
            scope, "OrdersDeadLetterQueue", queue_name=dlq_name, encryption=sqs.QueueEncryption.SQS_MANAGED
        )
        apply_name_tag(dead_letter_queue, dlq_name)

        queue_name = resource_name(config.product, config.environment, cell, "sqs", "orders")
        queue = sqs.Queue(
            scope,
            "OrdersQueue",
            queue_name=queue_name,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=3, queue=dead_letter_queue),
        )
        apply_name_tag(queue, queue_name)

        context.shared["sqs_queue"] = queue
