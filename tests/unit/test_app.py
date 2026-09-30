"""Unit tests for the root app.py - module discovery.

Every test_NN_service.py builds one stack directly; this file checks the
piece that ties them together: that app.py finds every modules/*/stack.py,
builds each one under its own STACK_ID, and skips a module directory that
has no stack.py (like 44_resource_quotas). See CLAUDE.md, section 3.
"""

from __future__ import annotations

import functools
from pathlib import Path

import aws_cdk as cdk
import pytest
from aws_cdk import cx_api

import app

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def synth_dir(tmp_path, monkeypatch):
    """Point app.synth() at a temporary folder instead of cdk.out/.

    `CDK_OUTDIR` can't be used for this: the CDK's Node.js process is
    already running (started by the first test) and never sees variables
    set afterwards - so `cdk.App` itself is given an explicit `outdir`.
    """
    monkeypatch.setattr(app.cdk, "App", functools.partial(cdk.App, outdir=str(tmp_path)))
    for var in ("CDK_DEFAULT_ACCOUNT", "CDK_DEFAULT_REGION", "AWS_ACCOUNT_ID", "AWS_REGION"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("CDK_ENVIRONMENT", raising=False)
    return tmp_path


def _stack_ids(outdir: Path) -> list[str]:
    return sorted(stack.stack_name for stack in cx_api.CloudAssembly(str(outdir)).stacks)


def test_every_module_with_a_stack_py_becomes_one_stack(synth_dir):
    expected = len(list((REPO_ROOT / "modules").glob("*/stack.py")))

    app.main()

    stack_ids = _stack_ids(synth_dir)
    assert len(stack_ids) == expected
    assert "VpcStack" in stack_ids


def test_a_module_directory_without_stack_py_is_skipped(synth_dir, monkeypatch, tmp_path_factory):
    fake_modules = tmp_path_factory.mktemp("modules")
    (fake_modules / "99_docs_only").mkdir()
    (fake_modules / "99_docs_only" / "__init__.py").write_text("")
    monkeypatch.setattr(app, "MODULES_DIR", fake_modules)

    app.main()

    assert _stack_ids(synth_dir) == []
