"""Module 41 - AWS Backup: a backup vault, a daily plan, and a tag-based selection.

AWS docs used while writing this module:
- BackupVault construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_backup/BackupVault.html
- BackupPlan construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_backup/BackupPlan.html
- BackupResource construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_backup/BackupResource.html
- What is AWS Backup: https://docs.aws.amazon.com/aws-backup/latest/devguide/whatisbackup.html

`BackupPlan.daily35_day_retention(scope, id, backup_vault)` is one of a
handful of built-in preset factory methods on the L2 `BackupPlan` class
(confirmed against the `aws-cdk-lib` v2.271.0 source for this construct);
it is the cheapest/simplest of the presets (a single daily backup, kept 35
days, no cold-storage transition), which is why this module uses it instead
of hand-building a `BackupPlanRule`.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_backup as backup
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "AwsBackupStack"


class AwsBackupStack(Stack):
    """A backup vault, a daily/35-day plan, and a selection tied to this repo's own tags.

    This stack defines the backup *policy* only - see README.md: it has no
    cost and backs up nothing by itself until a real, taggable resource
    (an RDS instance, a DynamoDB table, an EFS file system, ...) exists in
    this account/region with `environment=<config.environment>` as one of
    its tags (the same mandatory tag every module in this repo already
    applies via `apply_standard_tags` - see shared/tagging.py).
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: AppConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        apply_standard_tags(self, tags=config.to_standard_tags())

        vault_name = resource_name(config.product, config.environment, "backup", "vault")
        self.vault = backup.BackupVault(self, "BackupVault", backup_vault_name=vault_name)
        apply_name_tag(self.vault, vault_name)

        plan_name = resource_name(config.product, config.environment, "backup", "daily-plan")
        self.plan = backup.BackupPlan.daily35_day_retention(self, plan_name, self.vault)
        apply_name_tag(self.plan, plan_name)

        # Ties the backup selection to this repo's own mandatory `environment`
        # tag (see shared/tagging.py) instead of inventing a backup-specific
        # tag - any resource this app deploys already carries it.
        self.plan.add_selection(
            "Selection",
            resources=[backup.BackupResource.from_tag("environment", config.environment)],
        )


STACK_CLASS = AwsBackupStack
