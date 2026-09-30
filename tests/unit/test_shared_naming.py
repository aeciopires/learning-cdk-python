"""Unit tests for shared/naming.py - how every physical resource name is built.

See REQUIREMENTS.md, "Naming policy".
"""

from __future__ import annotations

import pytest

from shared.naming import resource_name


def test_joins_parts_with_hyphens_in_lower_case():
    assert resource_name("Learning-CDK-Python", "dev", "sqs", "Orders") == (
        "learning-cdk-python-dev-sqs-orders"
    )


def test_underscore_separator_for_resource_types_that_forbid_hyphens():
    assert resource_name("learning-cdk-python", "prd", "db", separator="_") == (
        "learning_cdk_python_prd_db"
    )


def test_empty_and_blank_parts_are_skipped():
    # e.g. a cell_id of "" when the deployment isn't cell-based
    assert resource_name("demo", "dev", "", "  ", "s3", "data") == "demo-dev-s3-data"


def test_invalid_characters_are_replaced_and_repeats_collapsed():
    assert resource_name("demo", "dev", "my bucket!!", "--data--") == "demo-dev-my-bucket-data"


def test_any_other_separator_is_rejected():
    with pytest.raises(ValueError, match="separator must be"):
        resource_name("demo", "dev", separator=".")
