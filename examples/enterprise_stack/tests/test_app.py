"""Unit tests for examples/enterprise_stack/app.py - one stack per cell, and
the selected environment driving every cell's tags and resource names.
"""

from __future__ import annotations

import functools
from pathlib import Path

import aws_cdk as cdk
import pytest
from aws_cdk import cx_api

from examples.enterprise_stack import app


@pytest.fixture
def synth_dir(tmp_path, monkeypatch):
    """Point app.synth() at a temporary folder (see tests/unit/test_app.py
    in the repository root for why `CDK_OUTDIR` can't be used instead)."""
    monkeypatch.setattr(app.cdk, "App", functools.partial(cdk.App, outdir=str(tmp_path)))
    monkeypatch.setenv("CDK_ENVIRONMENT", "dev")  # must be overridden by ENTERPRISE_ENVIRONMENT
    for var in ("CDK_DEFAULT_ACCOUNT", "CDK_DEFAULT_REGION", "CDK_PRODUCT"):
        monkeypatch.delenv(var, raising=False)
    return tmp_path


def _assembly(outdir: Path) -> cx_api.CloudAssembly:
    return cx_api.CloudAssembly(str(outdir))


def test_stack_id_is_built_from_the_environment_and_cell_id():
    assert app._stack_id("stg", "cell-01") == "EnterpriseStgCell01Stack"


def test_each_environment_gets_its_own_stack_ids():
    """Same cell id, different environments -> different stacks, so
    deploying one environment never replaces another's stack."""
    ids = {app._stack_id(environment, "cell-01") for environment in ("dev", "stg", "prd")}
    assert ids == {"EnterpriseDevCell01Stack", "EnterpriseStgCell01Stack", "EnterprisePrdCell01Stack"}


def test_dev_is_the_default_environment(synth_dir, monkeypatch):
    monkeypatch.delenv("ENTERPRISE_ENVIRONMENT", raising=False)

    app.main()

    assert [s.stack_name for s in _assembly(synth_dir).stacks] == ["EnterpriseDevCell01Stack"]


def test_selected_environment_sets_names_and_tags_not_cdk_environment(synth_dir, monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENVIRONMENT", "stg")

    app.main()

    template = _assembly(synth_dir).get_stack_by_name("EnterpriseStgCell01Stack").template
    repository = next(
        r for r in template["Resources"].values() if r["Type"] == "AWS::ECR::Repository"
    )
    assert repository["Properties"]["RepositoryName"] == (
        "learning-cdk-python-stg-cell-01-ecr-mytoolkit"
    )
    assert {"Key": "environment", "Value": "stg"} in repository["Properties"]["Tags"]


def test_a_long_environment_name_is_rejected(synth_dir, monkeypatch):
    monkeypatch.setenv("ENTERPRISE_ENVIRONMENT", "staging")

    with pytest.raises(ValueError, match='did you mean "stg"'):
        app.main()
