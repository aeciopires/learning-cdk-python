"""KMS: same `kms.Key` call verified in modules/08_kms/stack.py."""

from __future__ import annotations

from aws_cdk import RemovalPolicy
from aws_cdk import aws_kms as kms
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class KmsResourceBuilder(ResourceBuilder):
    key = "kms"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        key_alias = resource_name(config.product, config.environment, cell, "kms", "app")
        key = kms.Key(
            scope,
            "AppKey",
            alias=key_alias,
            description=f"Customer-managed KMS key for {config.product} ({config.environment}, cell={cell or 'none'}).",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        apply_name_tag(key, key_alias)

        context.shared["kms_key"] = key
