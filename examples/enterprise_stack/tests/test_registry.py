"""Unit tests for the precedence engine - pure Python, no CDK/AWS/Docker
needed, same "fast and dependency-free" philosophy as docs/TESTING.md.
"""

from __future__ import annotations

import pytest

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from examples.enterprise_stack.core.resource_registry import (
    CircularDependencyError,
    MissingDependencyError,
    ResourceRegistry,
)


class _FakeBuilder(ResourceBuilder):
    def __init__(self, key: str, depends_on: tuple[str, ...] = ()) -> None:
        self.key = key
        self.depends_on = depends_on

    def build(self, scope, context: ResourceContext) -> None:  # pragma: no cover - not exercised here
        raise NotImplementedError


def _registry(*builders: _FakeBuilder) -> ResourceRegistry:
    registry = ResourceRegistry()
    for builder in builders:
        registry.register(builder)
    return registry


def test_orders_dependencies_before_dependents():
    vpc = _FakeBuilder("vpc")
    ec2 = _FakeBuilder("ec2", depends_on=("vpc",))
    registry = _registry(ec2, vpc)  # registered out of order, on purpose

    ordered = registry.ordered({"vpc", "ec2"})

    assert [b.key for b in ordered] == ["vpc", "ec2"]


def test_independent_resources_use_a_deterministic_tie_break():
    vpc = _FakeBuilder("vpc")
    s3 = _FakeBuilder("s3")
    registry = _registry(vpc, s3)

    ordered = registry.ordered({"vpc", "s3"})

    assert [b.key for b in ordered] == ["s3", "vpc"]  # alphabetical, no shared dependency


def test_disabled_resources_are_excluded():
    vpc = _FakeBuilder("vpc")
    ec2 = _FakeBuilder("ec2", depends_on=("vpc",))
    registry = _registry(vpc, ec2)

    ordered = registry.ordered({"vpc"})

    assert [b.key for b in ordered] == ["vpc"]


def test_missing_dependency_raises_instead_of_auto_enabling():
    ec2 = _FakeBuilder("ec2", depends_on=("vpc",))
    registry = _registry(ec2)

    with pytest.raises(MissingDependencyError):
        registry.ordered({"ec2"})


def test_circular_dependency_raises():
    a = _FakeBuilder("a", depends_on=("b",))
    b = _FakeBuilder("b", depends_on=("a",))
    registry = _registry(a, b)

    with pytest.raises(CircularDependencyError):
        registry.ordered({"a", "b"})


def test_unknown_key_raises():
    registry = _registry(_FakeBuilder("vpc"))

    with pytest.raises(KeyError):
        registry.ordered({"does-not-exist"})
