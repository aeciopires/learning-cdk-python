"""Module 08 - KMS: a customer-managed encryption key with automatic rotation.

AWS docs used while writing this module:
- Key construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_kms/Key.html
- KMS concepts (customer-managed keys, key rotation): https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html
- Deleting KMS keys (the mandatory pending-deletion window): https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_kms as kms
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "KmsStack"


class KmsStack(Stack):
    """One customer-managed KMS key, with automatic yearly rotation enabled.

    `kms.Key`'s `alias` property takes the alias **without** the `alias/`
    prefix - the construct adds it for you (confirmed by reading the
    installed aws-cdk-lib 2.271.0 source: `Key.__init__` calls
    `self.add_alias(props.alias)`, and `Alias`'s own constructor prepends
    `alias/` to any value that does not already start with it). Passing an
    alias that already starts with `alias/` would still work (it is left
    alone), but this module follows the documented convention and passes
    the bare name.

    `removal_policy=RemovalPolicy.DESTROY` is what lets `cdk destroy` remove
    this key at all in this learning module - see "Notes and cautions" in
    README.md for what that removal_policy does and does not skip on real
    AWS (it does not skip KMS's own mandatory pending-deletion window).
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

        key_alias = resource_name(config.product, config.environment, "kms", "app")
        self.key = kms.Key(
            self,
            "AppKey",
            alias=key_alias,
            description=(
                f"Customer-managed KMS key for the {config.product} learning path "
                "- see modules/08_kms/README.md."
            ),
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        apply_name_tag(self.key, key_alias)


STACK_CLASS = KmsStack
