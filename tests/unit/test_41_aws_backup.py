"""Unit tests for modules/41_aws_backup. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

AwsBackupStack = stack_class("41_aws_backup")


def _synth(config):
    app = cdk.App()
    stack = AwsBackupStack(app, "TestAwsBackupStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_backup_vault(config):
    template = _synth(config)
    template.resource_count_is("AWS::Backup::BackupVault", 1)


def test_creates_exactly_one_backup_plan(config):
    template = _synth(config)
    template.resource_count_is("AWS::Backup::BackupPlan", 1)


def test_creates_exactly_one_backup_selection(config):
    template = _synth(config)
    template.resource_count_is("AWS::Backup::BackupSelection", 1)


def test_backup_plan_runs_daily_with_35_day_retention(config):
    """The `daily35_day_retention(...)` preset this module deliberately uses."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Backup::BackupPlan",
        {
            "BackupPlan": Match.object_like(
                {
                    "BackupPlanRule": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "RuleName": "Daily",
                                    "Lifecycle": {"DeleteAfterDays": 35},
                                }
                            )
                        ]
                    )
                }
            )
        },
    )


def test_backup_selection_selects_resources_tagged_with_the_environment(config):
    """This module's whole point: a tag-based selection, not a fixed resource
    list - see README.md and stack.py's `BackupResource.from_tag(...)`.
    """
    template = _synth(config)
    template.has_resource_properties(
        "AWS::Backup::BackupSelection",
        {
            "BackupSelection": Match.object_like(
                {
                    "ListOfTags": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "ConditionKey": "environment",
                                    "ConditionType": "STRINGEQUALS",
                                    "ConditionValue": config.environment,
                                }
                            )
                        ]
                    )
                }
            )
        },
    )


def test_backup_vault_has_the_mandatory_tags(config):
    """`AWS::Backup::BackupVault` tags as `BackupVaultTags`, an object/map
    (key -> value), not a `Tags` list - confirmed in the real synthesized
    `cdk.out/AwsBackupStack.template.json`. A map has no ordering concern
    the way a `Tags` array does, so one `Match.object_like(...)` call
    covering every tag is enough here.
    """
    template = _synth(config)
    expected = {pair["Key"]: pair["Value"] for pair in mandatory_tag_pairs(config)}
    template.has_resource_properties(
        "AWS::Backup::BackupVault", {"BackupVaultTags": Match.object_like(expected)}
    )


def test_backup_plan_has_the_mandatory_tags(config):
    """Same `*Tags`-as-a-map shape as the vault above, but as `BackupPlanTags`."""
    template = _synth(config)
    expected = {pair["Key"]: pair["Value"] for pair in mandatory_tag_pairs(config)}
    template.has_resource_properties(
        "AWS::Backup::BackupPlan", {"BackupPlanTags": Match.object_like(expected)}
    )


# AWS::Backup::BackupSelection has no tagging property of its own (absent
# from the real synthesized template - it is a policy mapping a plan to a
# selection of resources, not something separately taggable), so there is
# no mandatory-tags test for it.
