"""Unit tests for modules/20_rds_aurora. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

RdsAuroraStack = stack_class("20_rds_aurora")


def _synth(config):
    app = cdk.App()
    stack = RdsAuroraStack(app, "TestRdsAuroraStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_cluster(config):
    template = _synth(config)
    template.resource_count_is("AWS::RDS::DBCluster", 1)


def test_creates_exactly_one_writer_instance(config):
    """No `readers=` is configured - see stack.py's docstring - so the cluster
    has exactly one instance, the writer."""
    template = _synth(config)
    template.resource_count_is("AWS::RDS::DBInstance", 1)


def test_cluster_uses_the_aurora_postgres_engine_and_expected_version(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::RDS::DBCluster",
        {"Engine": "aurora-postgresql", "EngineVersion": "17.9"},
    )


def test_writer_instance_is_a_promotion_tier_zero_aurora_postgres_instance(config):
    """`PromotionTier: 0` is how CloudFormation marks the writer instance."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::RDS::DBInstance",
        {
            "Engine": "aurora-postgresql",
            "DBInstanceClass": "db.t3.medium",
            "PromotionTier": 0,
        },
    )


def test_cluster_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::RDS::DBCluster", {"Tags": Match.array_with([tag])}
        )


def test_master_password_is_a_literal_reference_to_a_named_secret(config):
    """floci only resolves a {{resolve:secretsmanager:...}} reference written as
    a plain string - not the Fn::Join + Ref form CDK builds from a Secret
    object - so the password must reference the secret by its fixed name."""
    template = _synth(config)
    secret_name = f"{config.product}-{config.environment}-secret-rds-aurora"
    template.has_resource_properties(
        "AWS::SecretsManager::Secret",
        {
            "Name": secret_name,
            "GenerateSecretString": Match.object_like(
                {"GenerateStringKey": "password", "SecretStringTemplate": Match.string_like_regexp("dbadmin")}
            ),
        },
    )
    template.has_resource_properties(
        "AWS::RDS::DBCluster",
        {
            "MasterUsername": "dbadmin",
            "MasterUserPassword": f"{{{{resolve:secretsmanager:{secret_name}:SecretString:password::}}}}",
        },
    )


def test_database_waits_for_its_secret(config):
    """A by-name reference has no implicit dependency on the secret."""
    template = _synth(config)
    secret_id = next(iter(template.find_resources("AWS::SecretsManager::Secret")))
    database = next(iter(template.find_resources("AWS::RDS::DBCluster").values()))
    assert secret_id in database["DependsOn"]
