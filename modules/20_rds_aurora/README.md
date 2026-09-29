<!-- TOC -->

- [Module 20 - Aurora (PostgreSQL-compatible)](#module-20---aurora-postgresql-compatible)
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

# Module 20 - Aurora (PostgreSQL-compatible)

## Overview

Amazon Aurora is AWS's own cloud-native relational database engine,
compatible with either MySQL or PostgreSQL wire protocols but built on a
different, distributed storage layer than standalone RDS. This module
creates one Aurora PostgreSQL-compatible cluster with a single
`db.t3.medium` writer instance, plus its own dedicated 2-Availability-Zone
VPC and a Secrets Manager secret for the generated master password.

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module to a real AWS account.** Aurora is typically **pricier** than an
equivalent-size standalone RDS instance (module 18/19) and, like every RDS
family engine, bills hourly the moment it exists.

## What you will learn

- The cluster/instance split: `aws_rds.DatabaseCluster` provisions Aurora's
  shared storage layer; `rds.ClusterInstance.provisioned(...)` provisions
  the compute instance(s) attached to it (here, one `writer`, no
  `readers`).
- **The current (non-deprecated) `DatabaseCluster` API.** `aws_cdk.aws_rds`
  has changed this construct's API across CDK versions: an older shape
  configured instance count via `instances=<int>` and `instance_props=`;
  the current shape - the one this module uses - is
  `writer=rds.ClusterInstance.provisioned("Writer", instance_type=...)`
  with an optional `readers=[...]` list. This was verified directly against
  the `aws_cdk.aws_rds` source shipped in this project's pinned
  `aws-cdk-lib==2.271.0` (not recalled from memory - see the module's
  `stack.py` docstring for exactly what was checked).
- Why a cluster still needs a 2-AZ VPC even though Aurora's storage is
  already replicated across AZs internally - the DB subnet group
  requirement applies the same way it does to standalone RDS (modules 18
  and 19).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Amazon Aurora | `aws_cdk.aws_rds.DatabaseCluster` | L2 |
| Amazon Aurora | `aws_cdk.aws_rds.ClusterInstance` | L2 (helper) |
| Amazon Aurora | `aws_cdk.aws_rds.DatabaseClusterEngine`, `aws_cdk.aws_rds.AuroraPostgresEngineVersion` | L2 (helpers) |
| Amazon Aurora / AWS Secrets Manager | `aws_cdk.aws_rds.Credentials` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- floci's Aurora/RDS coverage runs as a real Docker container under the hood
  (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md), "Observations and
  limitations") - this is one of the heavier modules to deploy locally, and
  Aurora-specific behavior (its distributed storage layer, cluster
  endpoints) is one of the harder things for any local emulator to fully
  replicate; treat floci here as "does the CDK code work", not as a
  faithful Aurora performance/availability simulation.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_20_rds_aurora.py`](../../tests/unit/test_20_rds_aurora.py))
check that: exactly one `AWS::RDS::DBCluster` and exactly one
`AWS::RDS::DBInstance` are created (the cluster's one writer - no
`readers=` is configured, see `stack.py`), the cluster uses the
`aurora-postgresql` engine at version `17.9`, the writer instance is a
`db.t3.medium` with `PromotionTier: 0` (CloudFormation's marker for the
writer), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the cluster. They run in well under a second, with no Docker, no floci,
and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_20_rds_aurora.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth RdsAuroraStack
uv run cdk deploy RdsAuroraStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you have read and understood
[Notes and cautions](#notes-and-cautions) - this module has a real,
ongoing hourly cost, typically higher than modules 18/19, the moment it is
deployed.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy RdsAuroraStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws rds describe-db-clusters --query "DBClusters[].{Id:DBClusterIdentifier,Status:Status,Engine:Engine}"
aws rds describe-db-instances --query "DBInstances[].{Id:DBInstanceIdentifier,Cluster:DBClusterIdentifier,Status:DBInstanceStatus}"
aws secretsmanager list-secrets --query "SecretList[].Name"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
cluster, its writer instance, and the generated secret visually.

## Clean up

```bash
uv run cdk destroy RdsAuroraStack
```

## Notes and cautions

- **Aurora is typically pricier than an equivalent-size standalone RDS
  instance**, and - like every module in the RDS/Aurora family in this
  path - bills **hourly from the moment the cluster and its writer instance
  exist**, regardless of whether anything ever connects to them. This is
  one of the more expensive modules in this learning path on real AWS; see
  the pricing reference below and check current rates for your region
  before deploying to a real account.
- **Master username:** this module uses
  `rds.Credentials.from_generated_secret("dbadmin")`, not `"admin"`.
  `cdk synth RdsAuroraStack` flags `"admin"` with a CloudFormation
  template-validation warning (not a hard error) -
  `MasterUsername: 'admin' must not be one of ['admin'] for a
  PostgreSQL-compatible engine, where it is a reserved word` - so this
  module and module 19 (RDS PostgreSQL) both use `"dbadmin"` instead.
- `removal_policy=RemovalPolicy.DESTROY` is chosen so this module is easy
  to tear down while learning; `readers=` is intentionally left unset (no
  read replica) to keep this module to the lowest cost an Aurora cluster
  can be while still demonstrating the writer/reader instance model.
- The exact minimum/currently-supported instance classes for Aurora
  PostgreSQL can change over time - re-check the
  [Aurora PostgreSQL instance class support](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Concepts.html)
  page before relying on `db.t3.medium` remaining valid.

## References

- [Amazon Aurora User Guide - Overview](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/CHAP_AuroraOverview.html)
- [Amazon Aurora pricing](https://aws.amazon.com/rds/aurora/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.DatabaseCluster`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseCluster.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.ClusterInstance`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/ClusterInstance.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.AuroraPostgresEngineVersion`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/AuroraPostgresEngineVersion.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.Credentials`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/Credentials.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
