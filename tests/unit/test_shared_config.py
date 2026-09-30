"""Unit tests for shared/config.py: the environment short-name policy,
get_environment(), and load_app_config().

Unlike the test_NN_service.py files, this one tests shared code rather than
a module's stack - see REQUIREMENTS.md, "Tagging policy", for the policy
itself (`environment` is one of "dev", "stg", "prd").
"""

from __future__ import annotations

import pytest

from shared.config import ENVIRONMENTS, get_environment, load_app_config, validate_environment


def test_the_three_short_environment_names_are_the_only_ones_allowed():
    assert ENVIRONMENTS == ("dev", "stg", "prd")


@pytest.mark.parametrize("name", ["dev", "stg", "prd", " PRD "])
def test_short_names_are_accepted_and_normalized(name):
    assert validate_environment(name) == name.strip().lower()


@pytest.mark.parametrize(
    ("long_name", "short_name"),
    [("staging", "stg"), ("prod", "prd"), ("production", "prd"), ("development", "dev")],
)
def test_long_names_are_rejected_with_the_short_name_suggested(long_name, short_name):
    with pytest.raises(ValueError, match=f'did you mean "{short_name}"'):
        validate_environment(long_name)


def test_unknown_names_are_rejected():
    with pytest.raises(ValueError, match="must be one of dev, stg, prd"):
        validate_environment("qa")


def test_load_app_config_reads_and_validates_cdk_environment(monkeypatch):
    monkeypatch.setenv("CDK_ENVIRONMENT", "stg")
    assert load_app_config().environment == "stg"

    monkeypatch.setenv("CDK_ENVIRONMENT", "staging")
    with pytest.raises(ValueError, match='did you mean "stg"'):
        load_app_config()


def test_load_app_config_defaults_to_dev(monkeypatch):
    monkeypatch.delenv("CDK_ENVIRONMENT", raising=False)
    assert load_app_config().environment == "dev"


# --- get_environment(): the account/region every stack deploys to -----------

_ENV_VARS = ("CDK_DEFAULT_ACCOUNT", "CDK_DEFAULT_REGION", "AWS_ACCOUNT_ID", "AWS_REGION")


@pytest.fixture
def clean_env(monkeypatch):
    """Start every get_environment() test with none of its 4 variables set."""
    for var in _ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


def test_get_environment_is_agnostic_when_nothing_is_set(clean_env):
    assert get_environment() is None


def test_get_environment_uses_the_cdk_default_variables(clean_env):
    clean_env.setenv("CDK_DEFAULT_ACCOUNT", "123456789012")
    clean_env.setenv("CDK_DEFAULT_REGION", "us-east-1")

    env = get_environment()

    assert env is not None
    assert (env.account, env.region) == ("123456789012", "us-east-1")


def test_get_environment_falls_back_to_the_aws_variables(clean_env):
    clean_env.setenv("AWS_ACCOUNT_ID", "000000000000")
    clean_env.setenv("AWS_REGION", "eu-west-1")

    env = get_environment()

    assert env is not None
    assert (env.account, env.region) == ("000000000000", "eu-west-1")


def test_get_environment_prefers_cdk_default_over_aws_variables(clean_env):
    clean_env.setenv("CDK_DEFAULT_REGION", "us-east-1")
    clean_env.setenv("AWS_REGION", "eu-west-1")

    env = get_environment()

    assert env is not None
    assert env.region == "us-east-1"
    assert env.account is None  # only a region was set - still a real env


def test_load_app_config_reads_every_tag_variable(monkeypatch):
    monkeypatch.setenv("CDK_PRODUCT", "demo")
    monkeypatch.setenv("CDK_ENVIRONMENT", "prd")
    monkeypatch.setenv("CDK_TEAM_OWNER", "team-a")
    monkeypatch.setenv("CDK_PCI", "TRUE")
    monkeypatch.setenv("CDK_CELL_BASED", "true")
    monkeypatch.setenv("CDK_CELL_ID", "cell-07")

    config = load_app_config()

    assert (config.product, config.environment, config.team_owner) == ("demo", "prd", "team-a")
    assert config.pci is True
    assert (config.cell_based, config.cell_id) == (True, "cell-07")
    assert config.to_standard_tags().cell_id == "cell-07"


def test_load_app_config_ignores_cell_id_when_not_cell_based(monkeypatch):
    monkeypatch.setenv("CDK_CELL_BASED", "false")
    monkeypatch.setenv("CDK_CELL_ID", "cell-07")

    assert load_app_config().cell_id is None
