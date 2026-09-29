"""The one Stack class in this whole example - see README.md."""

from __future__ import annotations

from aws_cdk import Stack
from constructs import Construct

from shared.config import AppConfig
from shared.tagging import apply_standard_tags

from .core.resource_builder import ResourceContext
from .core.resource_registry import ResourceRegistry


class EnterpriseCellStack(Stack):
    """One "cell": every resource it creates belongs to exactly one
    (product, environment, cell_id, account, region) combination.
    Instantiate it again with a different `config`/`enabled_keys`/`env`
    and you get an independent, identically-shaped cell - see
    environments/prod.json for two cells built from the very same classes.

    This class knows nothing about IAM, VPCs, S3, or any other AWS
    service - only how to ask a `ResourceRegistry` for the enabled
    builders, in dependency order, and call `.build()` on each. That is
    the whole Dependency Inversion / Open-Closed point of this example:
    adding resource #14 never touches this file.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: AppConfig,
        registry: ResourceRegistry,
        enabled_keys: set[str],
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        apply_standard_tags(self, tags=config.to_standard_tags())

        context = ResourceContext(config=config)
        for builder in registry.ordered(enabled_keys):
            builder.build(self, context)
