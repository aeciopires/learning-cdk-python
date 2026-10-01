#!/usr/bin/env python3
"""Entry point for the enterprise_stack example - see README.md.

Deploys one EnterpriseCellStack per cell listed in
environments/<ENTERPRISE_ENVIRONMENT>.json. Run from the repository root:

    export ENTERPRISE_ENVIRONMENT=dev   # or stg, or prd
    uv run cdk synth --app "uv run python examples/enterprise_stack/app.py"
    uv run cdk list  --app "uv run python examples/enterprise_stack/app.py"

Switching `dev` to `stg` to `prd` (or adding a cell to prd.json)
changes which resources get built and how many cells get deployed without
touching a single line of Python. The chosen name is also every cell's
`environment` tag and resource-name segment (overriding `CDK_ENVIRONMENT`),
so stg cells are always named `...-stg-...` - see README.md, "Cells:
replicating the same stack across environments, accounts, and regions".

This file is deliberately not registered in the repository's own
app.py/cdk.json - see README.md, "Why this lives outside modules/" for why
it is a separate CDK app rather than a 45th learning module.
"""

from __future__ import annotations

import os
from dataclasses import replace

import aws_cdk as cdk

from examples.enterprise_stack.builders import build_default_registry
from examples.enterprise_stack.core.environment_config import load_environment
from examples.enterprise_stack.stack import EnterpriseCellStack
from shared.config import load_app_config, validate_environment


def _stack_id(environment: str, cell_id: str) -> str:
    """e.g. ("stg", "cell-01") -> "EnterpriseStgCell01Stack".

    The environment is part of the id so dev, stg, and prd cells are
    different CloudFormation stacks: with the cell id alone, every
    environment's cell-01 would be the same stack, and deploying stg would
    replace dev's cell-01 instead of adding a second one.
    """
    words = [environment, *cell_id.split("-")]
    return "Enterprise" + "".join(word.capitalize() for word in words) + "Stack"


def main() -> None:
    app = cdk.App()
    base_config = load_app_config()
    environment_name = validate_environment(os.getenv("ENTERPRISE_ENVIRONMENT", "dev"))
    registry = build_default_registry()

    for cell in load_environment(environment_name):
        cell_config = replace(
            base_config, environment=environment_name, cell_based=True, cell_id=cell.cell_id
        )
        EnterpriseCellStack(
            app,
            _stack_id(environment_name, cell.cell_id),
            config=cell_config,
            registry=registry,
            enabled_keys=set(cell.enabled_resources),
            env=cell.env,
        )

    app.synth()


if __name__ == "__main__":
    main()
