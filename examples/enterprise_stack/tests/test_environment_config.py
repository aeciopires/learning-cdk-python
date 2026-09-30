"""Unit tests for core/environment_config.py - reading environments/<name>.json.

Plain Python, no CDK synth: these check that each shipped JSON file loads
into the cells the README describes, and the account/region fallback.
"""

from __future__ import annotations

import pytest

from examples.enterprise_stack.core.environment_config import CellConfig, load_environment


@pytest.fixture(autouse=True)
def no_cdk_defaults(monkeypatch):
    monkeypatch.delenv("CDK_DEFAULT_ACCOUNT", raising=False)
    monkeypatch.delenv("CDK_DEFAULT_REGION", raising=False)


@pytest.mark.parametrize(("name", "cells", "resources"), [("dev", 1, 6), ("stg", 1, 13), ("prd", 2, 14)])
def test_each_environment_file_has_the_documented_shape(name, cells, resources):
    loaded = load_environment(name)

    assert len(loaded) == cells
    assert all(len(cell.enabled_resources) == resources for cell in loaded)


def test_prd_cells_use_the_explicit_account_and_region_from_the_file():
    cell_01, cell_02 = load_environment("prd")

    assert (cell_01.cell_id, cell_01.region) == ("cell-01", "us-east-1")
    assert (cell_02.cell_id, cell_02.region) == ("cell-02", "us-west-2")
    assert cell_01.env is not None and cell_01.env.account == "111111111111"


def test_missing_account_and_region_fall_back_to_cdk_defaults(monkeypatch):
    monkeypatch.setenv("CDK_DEFAULT_ACCOUNT", "000000000000")
    monkeypatch.setenv("CDK_DEFAULT_REGION", "eu-west-1")

    (cell,) = load_environment("dev")

    assert (cell.account, cell.region) == ("000000000000", "eu-west-1")


def test_no_account_or_region_anywhere_means_environment_agnostic():
    (cell,) = load_environment("dev")

    assert cell.env is None


def test_an_unknown_environment_lists_the_available_ones():
    with pytest.raises(FileNotFoundError, match=r"Available: \['dev', 'prd', 'stg'\]"):
        load_environment("staging")


def test_cell_config_env_with_only_a_region():
    cell = CellConfig(cell_id="c", account=None, region="us-east-1", enabled_resources=())

    assert cell.env is not None and cell.env.region == "us-east-1"
