"""Shared pytest fixtures for every module's unit tests.

See docs/TESTING.md for the full beginner explanation of how these tests
work, how to run them, and how to write a new one.
"""

from __future__ import annotations

import os

# Silences a harmless JSII/Node.js compatibility warning that would
# otherwise print to stderr on every test run - see the AWS CDK's jsii
# runtime docs. Set before aws_cdk is imported anywhere.
os.environ.setdefault("JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION", "1")

import pytest

from shared.config import AppConfig


@pytest.fixture
def config() -> AppConfig:
    """A fixed, deterministic AppConfig, shared by every module's tests.

    Unlike `shared.config.load_app_config()` (what `app.py` uses, which
    reads real `CDK_*` environment variables - see REQUIREMENTS.md section
    9), this fixture never reads the environment: every test in this
    repository builds its stack against the exact same tag values, so a
    test's result never depends on what happens to be exported in your
    shell.
    """
    return AppConfig(
        product="learning-cdk-python",
        environment="test",
        team_owner="platform-engineering",
        pci=False,
        cell_based=False,
        cell_id=None,
    )
