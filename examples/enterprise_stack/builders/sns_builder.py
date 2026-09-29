"""SNS: same `sns.Topic` + SQS subscription verified in
modules/27_sns/stack.py. Deliberately self-contained (its own
"notifications" queue, distinct from SqsResourceBuilder's "orders" queue)
rather than depending on "sqs" - two different queues for two different
purposes, exactly as the two standalone modules model them.
"""

from __future__ import annotations

from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from aws_cdk import aws_sqs as sqs
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class SnsResourceBuilder(ResourceBuilder):
    key = "sns"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        queue_name = resource_name(config.product, config.environment, cell, "sqs", "notifications")
        queue = sqs.Queue(scope, "NotificationsQueue", queue_name=queue_name, encryption=sqs.QueueEncryption.SQS_MANAGED)
        apply_name_tag(queue, queue_name)

        topic_name = resource_name(config.product, config.environment, cell, "sns", "notifications")
        topic = sns.Topic(scope, "NotificationsTopic", topic_name=topic_name)
        apply_name_tag(topic, topic_name)
        topic.add_subscription(sns_subscriptions.SqsSubscription(queue))

        context.shared["sns_topic"] = topic
