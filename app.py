#!/usr/bin/env python3
"""CDK app entry point - discovers and instantiates every module's stack.

Each `modules/NN_service/stack.py` exposes two module-level names:
    STACK_ID    : str            - the CloudFormation/CDK stack id, e.g. "VpcStack"
    STACK_CLASS : type[Stack]    - a Stack subclass with __init__(self, scope,
                                    construct_id, *, config: AppConfig, **kwargs)

That contract is what lets this file stay unchanged as modules are added:
no module needs to be imported or wired up here by name. A module that has
no deployable CDK resource at all (for example 44_resource_quotas - see its
README.md for why) simply has no `stack.py`, and is skipped.

Run `uv run cdk list` to see every stack id this discovers.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

import aws_cdk as cdk

from shared.config import get_environment, load_app_config

MODULES_DIR = Path(__file__).parent / "modules"


def main() -> None:
    app = cdk.App()
    config = load_app_config()
    env = get_environment()

    for module_info in sorted(
        pkgutil.iter_modules([str(MODULES_DIR)]), key=lambda m: m.name
    ):
        stack_module_path = MODULES_DIR / module_info.name / "stack.py"
        if not stack_module_path.exists():
            continue

        stack_module = importlib.import_module(f"modules.{module_info.name}.stack")
        stack_class = stack_module.STACK_CLASS
        stack_id = stack_module.STACK_ID

        stack_class(app, stack_id, config=config, env=env)

    app.synth()


if __name__ == "__main__":
    main()
