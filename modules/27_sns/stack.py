"""Module 27 - SNS: a topic fanning out to an SQS queue.

AWS docs used while writing this module:
- Topic construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html
- SqsSubscription construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/SqsSubscription.html
- Queue construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/Queue.html
- Fanout to Amazon SQS queues: https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from aws_cdk import aws_sqs as sqs
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "SnsStack"


class SnsStack(Stack):
    """An SNS topic that fans out to one SQS queue (the "SNS fan-out" pattern).

    `sns.Topic` is the CDK L2 construct for Amazon SNS. `topic.add_subscription
    (sns_subscriptions.SqsSubscription(queue))` does two things: it creates
    the SNS subscription *and* attaches the resource-based queue policy that
    lets SNS deliver messages into `queue` - a beginner does not have to
    write that policy by hand.

    This is a self-contained example: everything a message needs to travel
    from the topic to the queue is created in this one stack, so it can be
    deployed and verified on its own.
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

        queue_name = resource_name(config.product, config.environment, "sqs", "notifications")
        self.queue = sqs.Queue(
            self,
            "NotificationsQueue",
            queue_name=queue_name,
            encryption=sqs.QueueEncryption.SQS_MANAGED,
        )
        apply_name_tag(self.queue, queue_name)

        topic_name = resource_name(config.product, config.environment, "sns", "notifications")
        self.topic = sns.Topic(
            self,
            "NotificationsTopic",
            topic_name=topic_name,
        )
        apply_name_tag(self.topic, topic_name)

        # Fan-out: every message published to the topic is delivered to this
        # queue too. A real system typically fans out to several
        # subscribers (queues, Lambda functions, HTTPS endpoints, email) -
        # see README.md for why email is not included here.
        self.topic.add_subscription(sns_subscriptions.SqsSubscription(self.queue))


STACK_CLASS = SnsStack
