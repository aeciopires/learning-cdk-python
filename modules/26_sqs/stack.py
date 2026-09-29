"""Module 26 - SQS: a queue with a dead-letter queue.

AWS docs used while writing this module:
- Queue construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/Queue.html
- DeadLetterQueue: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/DeadLetterQueue.html
- QueueEncryption: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/QueueEncryption.html
- Amazon SQS dead-letter queues: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_sqs as sqs
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "SqsStack"


class SqsStack(Stack):
    """A standard SQS queue with a dead-letter queue (DLQ) wired up.

    `sqs.Queue` is the CDK L2 construct for Amazon SQS. `encryption=
    sqs.QueueEncryption.SQS_MANAGED` turns on server-side encryption using
    keys SQS manages for you (SSE-SQS) - no KMS key to create or pay for,
    which is why it is the default choice for a beginner module.

    A dead-letter queue (DLQ) is just a second, ordinary queue. What makes it
    a "dead-letter" queue is the *redrive policy* on the main queue:
    `sqs.DeadLetterQueue(max_receive_count=3, queue=dlq)` tells SQS to move a
    message to `dlq` after 3 failed receive attempts (a consumer received the
    message and did not delete it - `visibility_timeout` expired 3 times)
    instead of leaving it stuck, or retried forever, on the main queue.
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

        dlq_name = resource_name(config.product, config.environment, "sqs", "orders-dlq")
        self.dead_letter_queue = sqs.Queue(
            self,
            "OrdersDeadLetterQueue",
            queue_name=dlq_name,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
        )
        apply_name_tag(self.dead_letter_queue, dlq_name)

        queue_name = resource_name(config.product, config.environment, "sqs", "orders")
        self.queue = sqs.Queue(
            self,
            "OrdersQueue",
            queue_name=queue_name,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=self.dead_letter_queue,
            ),
        )
        apply_name_tag(self.queue, queue_name)


STACK_CLASS = SqsStack
