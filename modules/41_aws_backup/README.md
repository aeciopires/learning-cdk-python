<!-- TOC -->

- [Module 41 - AWS Backup](#module-41---aws-backup)
  - [Overview](#overview)
  - [What you will learn](#what-you-will-learn)
  - [AWS services and CDK constructs used](#aws-services-and-cdk-constructs-used)
  - [Prerequisites](#prerequisites)
  - [Tests](#tests)
  - [Deploy with floci (local, free)](#deploy-with-floci-local-free)
  - [Deploy to real AWS (optional)](#deploy-to-real-aws-optional)
  - [Verify](#verify)
  - [Clean up](#clean-up)
  - [Notes and cautions](#notes-and-cautions)
  - [References](#references)

<!-- TOC -->

# Module 41 - AWS Backup

## Overview

AWS Backup is a centralized backup service: instead of configuring backups
separately per service (RDS snapshots, EFS backups, DynamoDB backups, ...),
you define one **plan** (a schedule and retention policy) and one
**selection** (which resources it applies to), and AWS Backup handles the
rest across every supported service. This module creates a **backup
vault** (where recovery points are stored), a **daily backup plan** with
35-day retention, and a **selection** that ties the plan to this
repository's own `environment` tag.

## What you will learn

- How `backup.BackupVault` and `backup.BackupPlan` fit together: the vault
  is storage, the plan is schedule + retention, and a selection connects a
  plan to actual resources.
- How `BackupPlan.daily35_day_retention(...)` - one of several built-in
  preset factory methods - saves you from hand-building a
  `BackupPlanRule` (cron schedule, backup window, retention/cold-storage
  transitions) for a common case.
- How `BackupResource.from_tag(...)` selects resources dynamically, by tag,
  instead of listing ARNs one by one - and how this ties directly into
  this repository's own mandatory `environment` tag (see
  [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md#7-tagging-policy)).
- Why this stack, by itself, backs up nothing - see
  [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS Backup | `aws_cdk.aws_backup.BackupVault` | L2 |
| AWS Backup | `aws_cdk.aws_backup.BackupPlan` | L2 |
| AWS Backup | `aws_cdk.aws_backup.BackupResource` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_41_aws_backup.py`](../../tests/unit/test_41_aws_backup.py))
check that: exactly one backup vault, plan, and selection are created, the
plan runs daily with 35-day retention (the `daily35_day_retention` preset),
the selection targets resources by the `environment` tag (this module's
whole point), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the vault and plan - as `BackupVaultTags`/`BackupPlanTags`, maps rather
than the `Tags` list most other resources use (`AWS::Backup::BackupSelection`
has no tagging property of its own, so it has no equivalent check). No
Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_41_aws_backup.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth AwsBackupStack
uv run cdk deploy AwsBackupStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created - see
[Notes and cautions](#notes-and-cautions) for why this stack alone has no
cost.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy AwsBackupStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws backup list-backup-vaults
aws backup list-backup-plans
aws backup list-backup-selections --backup-plan-id <plan-id-from-above>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
vault, plan, and selection visually.

## Clean up

```bash
uv run cdk destroy AwsBackupStack
```

## Notes and cautions

- **This stack defines a backup *policy*, not a backup.** It has no cost
  and performs no backups by itself. AWS Backup only starts creating
  recovery points once a real, taggable, supported resource (an RDS
  instance, a DynamoDB table, an EFS file system, an EBS volume, ...)
  exists in this account/region carrying an `environment` tag equal to
  `config.environment` - see `shared/tagging.py` and
  [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md#7-tagging-policy). Once
  such a resource exists, cost is driven by the amount of backup storage
  and the resource type - see [Reference 4](#references).
- `daily35_day_retention` is the simplest, cheapest built-in preset (one
  daily backup, no cold-storage transition). `BackupPlan` also offers
  `daily_monthly1_year_retention`, `daily_weekly_monthly5_year_retention`,
  and `daily_weekly_monthly7_year_retention` for longer-retention,
  cold-storage-aware schedules - see [Reference 2](#references).
- `add_selection(...)` also creates an IAM role for AWS Backup to assume
  when it backs up your resources (unless you pass `role=` yourself) - see
  [Reference 2](#references).

## References

- [AWS Backup - What is AWS Backup?](https://docs.aws.amazon.com/aws-backup/latest/devguide/whatisbackup.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_backup.BackupPlan`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_backup/BackupPlan.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_backup.BackupResource`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_backup/BackupResource.html)
- [AWS Backup pricing](https://aws.amazon.com/backup/pricing/)
