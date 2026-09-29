"""Shared helper for importing a module's stack class in tests.

Every `modules/NN_service/` directory name starts with a zero-padded
number (`03_vpc`, `12_s3`, ...), which is not a legal Python identifier -
`from modules.03_vpc.stack import VpcStack` is a `SyntaxError`, since a
dotted import path's segments must each be valid identifiers. `app.py`
solves this the same way: `importlib.import_module()` takes the dotted
path as a plain string at runtime, so it never gets parsed as Python
syntax. This helper does the same thing for test files, so every
`tests/unit/test_NN_service.py` can stay a one-liner instead of repeating
the `importlib` call.

See docs/TESTING.md for the full explanation of how these tests work.
"""

from __future__ import annotations

import importlib
from typing import Any


def stack_class(module_dir: str) -> Any:
    """Import `modules/<module_dir>/stack.py` and return its STACK_CLASS.

    Example: `stack_class("03_vpc")` returns the `VpcStack` class.
    """
    return importlib.import_module(f"modules.{module_dir}.stack").STACK_CLASS


def mandatory_tag_pairs(config: Any) -> list[dict[str, str]]:
    """The 6 stack-wide mandatory tags (everything except `Name`, which is
    applied per-resource, not per-stack - see shared/tagging.py) as
    CloudFormation `{"Key": ..., "Value": ...}` pairs, ready to assert
    against a synthesized template's `Tags` property.

    Check each pair with its own `Match.array_with([pair])` call (one call
    per tag) rather than passing the whole list to a single `array_with()`
    call - `array_with()` matches an ordered subsequence, and CDK/
    CloudFormation always sorts a resource's tags alphabetically by key, so
    a single call listing tags in a different order than that will fail
    even though every tag is really there. See docs/TESTING.md.
    """
    tags = [
        {"Key": "environment", "Value": config.environment},
        {"Key": "product", "Value": config.product},
        {"Key": "team-owner", "Value": config.team_owner},
        {"Key": "pci", "Value": "true" if config.pci else "false"},
        {"Key": "cell-based", "Value": "true" if config.cell_based else "false"},
    ]
    if config.cell_based:
        tags.append({"Key": "cell-id", "Value": config.cell_id})
    return tags
