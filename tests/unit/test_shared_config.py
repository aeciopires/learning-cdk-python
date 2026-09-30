"""Unit tests for shared/config.py's environment short-name policy.

Unlike the test_NN_service.py files, this one tests shared code rather than
a module's stack - see REQUIREMENTS.md, "Tagging policy", for the policy
itself (`environment` is one of "dev", "stg", "prd").
"""

from __future__ import annotations

import pytest

from shared.config import ENVIRONMENTS, load_app_config, validate_environment


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
