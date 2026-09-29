"""The one interface every resource builder in this example implements.

See ../README.md ("SOLID, explained for beginners") for the full story -
in short: this is the *abstraction* that lets `stack.py` orchestrate 14
different AWS services without importing a single one of them by name.

This same abstraction is also what makes ../README.md section 13's
alternative possible - "one git repository (and one release cadence) per
builder": since nothing in this file, `resource_registry.py`, or
`stack.py` cares whether a concrete `ResourceBuilder` subclass came from a
local file or an installed, Semantic-Versioned package, a builder can be
extracted into its own repository without any of *this* code changing -
only the one `import` line in `builders/__init__.py` that names it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from constructs import Construct

from shared.config import AppConfig


@dataclass
class ResourceContext:
    """Everything a builder needs, and nothing it doesn't (Interface
    Segregation): the shared `AppConfig` (product/environment/team-owner/
    cell - see shared/config.py), plus a small grab-bag, `shared`, that
    builders use to publish a construct other builders may depend on (for
    example, `VpcResourceBuilder` publishes the one VPC that
    `Ec2ResourceBuilder`, `EcsResourceBuilder`, `AlbResourceBuilder`, and
    `NlbResourceBuilder` all reuse instead of each creating their own).
    """

    config: AppConfig
    shared: dict[str, Any] = field(default_factory=dict)


class ResourceBuilder(ABC):
    """Single Responsibility: a `ResourceBuilder` knows how to create
    exactly one kind of AWS resource - nothing about *which* resources are
    enabled, in what order, or what any other builder does.

    Open/Closed: `ResourceRegistry` and `EnterpriseCellStack` (see
    ``stack.py``) never change when a new resource is added - a new class
    implementing this interface, registered in `builders/__init__.py`, is
    the entire change.

    Liskov Substitution: `EnterpriseCellStack` only ever calls `.build()`.
    Any subclass can stand in for any other without the stack needing to
    know, or care, which concrete resource it is building.
    """

    #: Unique key. Other builders reference it in `depends_on`, and
    #: environment config files (see ../environments/*.json) reference it
    #: in `enabled_resources` to turn this resource on or off.
    key: str = ""

    #: Keys of other builders that must also be enabled, and built first,
    #: whenever this one is enabled. See core/resource_registry.py for how
    #: this becomes an actual build order (a topological sort).
    depends_on: tuple[str, ...] = ()

    @abstractmethod
    def build(self, scope: Construct, context: ResourceContext) -> None:
        """Create this resource under `scope`.

        If another builder may need what you just created, store it on
        `context.shared` under a clear key (e.g. `context.shared["vpc"] =
        vpc`) - that dict, not a direct import of your class, is how other
        builders reach it (Dependency Inversion: they depend on "a VPC
        being present in context.shared", not on `VpcResourceBuilder`
        itself).
        """
        raise NotImplementedError
