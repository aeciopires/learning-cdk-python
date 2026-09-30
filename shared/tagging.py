"""Mandatory tagging policy for every resource created in this repository.

See REQUIREMENTS.md ("Tagging policy") for the human-readable version of
this policy. This module is the single source of truth the code enforces.

Mandatory tags on every resource:
    - Name         : human-readable resource name (the tag key AWS itself
                      uses, by default, to display a resource's name in the
                      console - kept as "Name", capitalized, unlike every
                      other tag key in this repository).
    - environment   : e.g. "dev", "staging", "prod".
    - product       : the product/system this resource belongs to.
    - team-owner    : the team responsible for the resource.
    - pci           : "true" or "false" (string, not boolean - CloudFormation
                      tag values are always strings).
    - cell-based    : "true" or "false".
    - cell-id       : present only when cell-based is "true".

Reference: https://docs.aws.amazon.com/cdk/v2/guide/tagging.html
"""

from __future__ import annotations

from dataclasses import dataclass

from aws_cdk import Tags
from constructs import IConstruct


@dataclass(frozen=True)
class StandardTags:
    """Values for the mandatory tag set, shared by every stack in this repo."""

    product: str
    environment: str
    team_owner: str
    pci: bool = False
    cell_based: bool = False
    cell_id: str | None = None

    def __post_init__(self) -> None:
        if self.cell_based and not self.cell_id:
            raise ValueError("cell_id is required when cell_based is True")
        if not self.cell_based and self.cell_id:
            raise ValueError("cell_id must only be set when cell_based is False -> True")


def apply_standard_tags(scope: IConstruct, *, tags: StandardTags) -> None:
    """Apply the 6 stack-wide mandatory tags to every resource under `scope`.

    `Tags.of(scope).add(...)` (https://docs.aws.amazon.com/cdk/v2/guide/tagging.html)
    tags `scope` and every taggable resource nested under it in the construct
    tree, so this is called exactly once per Stack, right after the stack's
    `super().__init__()` call. It deliberately does **not** set the `Name`
    tag: unlike the other 6 tags, `Name` identifies one specific resource
    (a bucket, a queue, ...), not the whole stack - call `apply_name_tag()"
    on each significant resource instead, right after creating it.
    """
    Tags.of(scope).add("environment", tags.environment)
    Tags.of(scope).add("product", tags.product)
    Tags.of(scope).add("team-owner", tags.team_owner)
    Tags.of(scope).add("pci", "true" if tags.pci else "false")
    Tags.of(scope).add("cell-based", "true" if tags.cell_based else "false")
    # __post_init__ guarantees cell_id is set whenever cell_based is True;
    # checking both also narrows cell_id from `str | None` to `str` for mypy.
    if tags.cell_based and tags.cell_id:
        Tags.of(scope).add("cell-id", tags.cell_id)


def apply_name_tag(construct: IConstruct, name: str) -> None:
    """Apply the `Name` tag to one specific resource (see `apply_standard_tags`)."""
    Tags.of(construct).add("Name", name)
