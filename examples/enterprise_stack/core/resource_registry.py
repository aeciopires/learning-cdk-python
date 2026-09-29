"""The catalog of known resource builders, and the precedence engine.

See ../README.md ("Conditional resources and precedence, explained") for
the beginner-level explanation of what a topological sort is and why one
is used here instead of a plain, hand-maintained number.
"""

from __future__ import annotations

from .resource_builder import ResourceBuilder


class MissingDependencyError(RuntimeError):
    """Raised when a builder is enabled but something it `depends_on` is not.

    This example never silently auto-enables a dependency for you - see
    ../README.md, "Why a missing dependency is an error, not a fix-it".
    """


class CircularDependencyError(RuntimeError):
    """Raised when `depends_on` values form a cycle (A needs B, B needs A).

    That can only happen if two builders' `depends_on` are wrong - fix the
    builders, not the registry.
    """


class ResourceRegistry:
    """Open/Closed in action: `register()` is the *only* thing joining the
    stack requires of a new resource - nothing here grows in size or
    complexity as the catalog grows.

    Precedence: `ordered()` returns the enabled builders sorted so every
    builder appears after everything it `depends_on` - a topological sort
    (Kahn's algorithm), the same technique used to order tasks with
    prerequisites (you can't do task C before its prerequisites A and B are
    both done). Builders with no dependency relationship to each other keep
    a deterministic (alphabetical) order, so the same `enabled_resources`
    list always produces the same build order.
    """

    def __init__(self) -> None:
        self._builders: dict[str, ResourceBuilder] = {}

    def register(self, builder: ResourceBuilder) -> None:
        if not builder.key:
            raise ValueError(f"{type(builder).__name__}.key must be a non-empty string")
        if builder.key in self._builders:
            raise ValueError(f"a builder with key '{builder.key}' is already registered")
        self._builders[builder.key] = builder

    def ordered(self, enabled_keys: set[str]) -> list[ResourceBuilder]:
        unknown = enabled_keys - self._builders.keys()
        if unknown:
            raise KeyError(f"enabled_resources refers to unknown builder key(s): {sorted(unknown)}")

        for key in enabled_keys:
            for dependency in self._builders[key].depends_on:
                if dependency not in enabled_keys:
                    raise MissingDependencyError(
                        f"'{key}' is enabled but its dependency '{dependency}' is not - "
                        f"add '{dependency}' to enabled_resources too, or disable '{key}'."
                    )

        remaining = {key: self._builders[key] for key in enabled_keys}
        placed: list[ResourceBuilder] = []
        placed_keys: set[str] = set()

        while remaining:
            ready = sorted(
                (b for b in remaining.values() if all(dep in placed_keys for dep in b.depends_on)),
                key=lambda b: b.key,
            )
            if not ready:
                raise CircularDependencyError(f"circular depends_on among: {sorted(remaining)}")
            for builder in ready:
                placed.append(builder)
                placed_keys.add(builder.key)
                del remaining[builder.key]

        return placed
