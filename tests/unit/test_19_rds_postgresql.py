"""Unit tests for modules/19_rds_postgresql. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

RdsPostgresqlStack = stack_class("19_rds_postgresql")


def _synth(config):
    app = cdk.App()
    stack = RdsPostgresqlStack(app, "TestRdsPostgresqlStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_db_instance(config):
    template = _synth(config)
    template.resource_count_is("AWS::RDS::DBInstance", 1)


def test_instance_uses_the_postgres_engine_and_expected_version(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::RDS::DBInstance",
        {"Engine": "postgres", "EngineVersion": "18.3"},
    )


def test_instance_has_deletion_protection_disabled(config):
    """A learning-path stack must be destroyable with `cdk destroy` - see README.md."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::RDS::DBInstance", {"DeletionProtection": False}
    )


def test_instance_is_not_publicly_accessible(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::RDS::DBInstance", {"PubliclyAccessible": False}
    )


def test_database_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::RDS::DBInstance", {"Tags": Match.array_with([tag])}
        )
