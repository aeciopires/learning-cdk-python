<!-- TOC -->

- [Module 18 - RDS for MySQL](#module-18---rds-for-mysql)
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

# Module 18 - RDS for MySQL

## Overview

Amazon RDS (Relational Database Service) manages a relational database
engine for you - patching, backups, storage, and failover - so you write
SQL against it instead of administering a database server yourself. This
module creates one small MySQL instance (`db.t3.micro`), its own dedicated
2-Availability-Zone VPC, and a Secrets Manager secret holding its
auto-generated master password.

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module to a real AWS account.** Unlike almost every other module in this
learning path, an RDS instance bills by the hour from the moment it exists
- whether or not anything ever connects to it.

## What you will learn

- How `aws_rds.DatabaseInstance` (the CDK L2 construct) turns a handful of
  properties into a running managed database.
- Why RDS needs a DB subnet group spanning **two** Availability Zones even
  for a single-AZ instance - and how that differs from modules like
  modules/03_vpc, which only need one AZ's worth of subnets for what they
  demonstrate.
- `rds.Credentials.from_generated_secret("admin")`: instead of choosing a
  password yourself, CDK generates one and stores it in a brand-new AWS
  Secrets Manager secret, then wires the instance to read it. This is the
  same mechanism module 09 (Secrets Manager) explains on its own - here you
  see it used automatically by another service.
- Why this instance is placed in a `PRIVATE_ISOLATED` subnet (no route to
  the internet at all) rather than a public one.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Amazon RDS | `aws_cdk.aws_rds.DatabaseInstance` | L2 |
| Amazon RDS | `aws_cdk.aws_rds.DatabaseInstanceEngine`, `aws_cdk.aws_rds.MysqlEngineVersion` | L2 (helpers) |
| Amazon RDS / AWS Secrets Manager | `aws_cdk.aws_rds.Credentials` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- floci runs RDS as a real Docker container under the hood (see
  [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md), "Observations and
  limitations") - deploying this module locally takes noticeably longer
  than an S3 bucket or an SQS queue, and needs more free RAM/CPU.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_18_rds_mysql.py`](../../tests/unit/test_18_rds_mysql.py))
check that: exactly one `AWS::RDS::DBInstance` is created, it uses the
`mysql` engine at version `8.4.10`, `DeletionProtection` is `false` (so
`cdk destroy` can remove it) and `PubliclyAccessible` is `false`, and every
mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
section 7) is present on the instance. They run in well under a second,
with no Docker, no floci, and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_18_rds_mysql.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth RdsMysqlStack
uv run cdk deploy RdsMysqlStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you have read and understood
[Notes and cautions](#notes-and-cautions) - this module has a real,
ongoing hourly cost the moment it is deployed.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy RdsMysqlStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws rds describe-db-instances --query "DBInstances[].{Id:DBInstanceIdentifier,Status:DBInstanceStatus,Engine:Engine}"
aws secretsmanager list-secrets --query "SecretList[].Name"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
RDS instance and the generated secret visually.

## Clean up

```bash
uv run cdk destroy RdsMysqlStack
```

`removal_policy=RemovalPolicy.DESTROY` and `deletion_protection=False` mean
`cdk destroy` removes the instance (and, via CDK's default behavior for a
generated secret, the Secrets Manager secret) without a manual snapshot or
deletion-protection step first - deliberate for a learning module, not a
pattern to copy for a production database.

## Notes and cautions

- **This is one of the more expensive modules in this learning path on real
  AWS.** An RDS instance bills **hourly from the moment it exists**,
  regardless of whether anything ever connects to it - unlike, say, an S3
  bucket or a DynamoDB table in on-demand mode (modules/21_dynamodb), which
  cost nothing while idle. Even the smallest instance class
  (`db.t3.micro`) accrues charges continuously until you run `cdk destroy`.
  See the pricing reference below and check current rates for your region
  before deploying to a real account.
- `deletion_protection=False` and `removal_policy=RemovalPolicy.DESTROY`
  are chosen so this module is easy to tear down while learning - a real
  production database should set both the other way.
- `cdk synth` currently prints a template-validation **warning** (not an
  error) that `StorageEncrypted` is not set to `true` for this instance.
  This module leaves storage encryption off to keep the example to the
  minimal property set this learning path teaches with; a production
  database should set `storage_encrypted=True`.
- Two Availability Zones are used for the VPC (`max_azs=2`) purely because
  RDS requires a DB subnet group spanning at least two AZs - the instance
  itself is still single-AZ (`multi_az` defaults to `False`); a Multi-AZ
  deployment (a second, standby instance kept in sync) would roughly double
  the hourly cost again.

## References

- [Amazon RDS - What is Amazon RDS?](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html)
- [Amazon RDS for MySQL pricing](https://aws.amazon.com/rds/mysql/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.DatabaseInstance`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseInstance.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.MysqlEngineVersion`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/MysqlEngineVersion.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.Credentials`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/Credentials.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
