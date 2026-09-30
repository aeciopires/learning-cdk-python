"""Unit tests for modules/45_documentdb. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

DocumentDbStack = stack_class("45_documentdb")


def _synth(config):
    app = cdk.App()
    stack = DocumentDbStack(app, "TestDocumentDbStack", config=config)
    return Template.from_stack(stack)


def test_creates_one_cluster_with_one_instance(config):
    template = _synth(config)
    template.resource_count_is("AWS::DocDB::DBCluster", 1)
    template.resource_count_is("AWS::DocDB::DBInstance", 1)


def test_cluster_is_encrypted_named_and_on_a_supported_version(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::DocDB::DBCluster",
        {
            "DBClusterIdentifier": f"{config.product}-{config.environment}-docdb-main",
            "EngineVersion": "8.0.0",
            "StorageEncrypted": True,
            "Port": 27017,
        },
    )


def test_instance_uses_the_smallest_supported_class(config):
    template = _synth(config)
    template.has_resource_properties("AWS::DocDB::DBInstance", {"DBInstanceClass": "db.t3.medium"})


def test_subnet_group_spans_two_availability_zones(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::DocDB::DBSubnetGroup", {"SubnetIds": Match.array_equals([Match.any_value()] * 2)}
    )


def test_master_password_is_generated_in_secrets_manager(config):
    template = _synth(config)
    template.resource_count_is("AWS::SecretsManager::Secret", 1)
    template.has_resource_properties(
        "AWS::SecretsManager::Secret",
        {
            "Name": f"{config.product}-{config.environment}-secret-docdb",
            "GenerateSecretString": Match.object_like(
                {"GenerateStringKey": "password", "SecretStringTemplate": Match.string_like_regexp("docdbadmin")}
            ),
        },
    )


def test_password_reaches_the_cluster_only_as_a_dynamic_reference(config):
    template = _synth(config)
    cluster = next(iter(template.find_resources("AWS::DocDB::DBCluster").values()))
    password = cluster["Properties"]["MasterUserPassword"]

    assert "{{resolve:secretsmanager:" in str(password)
    assert cluster["Properties"]["MasterUsername"] == "docdbadmin"
    # No SecretTargetAttachment: floci can't deploy one for DocumentDB.
    template.resource_count_is("AWS::SecretsManager::SecretTargetAttachment", 0)


def test_cluster_is_destroyed_with_the_stack(config):
    template = _synth(config)
    template.has_resource("AWS::DocDB::DBCluster", {"DeletionPolicy": "Delete"})


def test_cluster_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties("AWS::DocDB::DBCluster", {"Tags": Match.array_with([tag])})
