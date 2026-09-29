<!-- TOC -->

- [Module 22 - ElastiCache (Redis OSS)](#module-22---elasticache-redis-oss)
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

# Module 22 - ElastiCache (Redis OSS)

## Overview

Amazon ElastiCache is a managed in-memory data store, typically used as a
cache or a fast key-value store in front of a slower primary database. This
module creates one single-node Redis OSS cache cluster (`cache.t3.micro`),
in its own dedicated single-AZ VPC, reachable only from inside that VPC.

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module to a real AWS account.** Like the RDS/Aurora modules, an ElastiCache
node bills hourly the moment it exists.

## What you will learn

- **Why this module uses L1 (`Cfn*`) constructs, not L2.** Unlike
  `aws_ec2.Vpc` or `aws_rds.DatabaseInstance`, `aws_cdk.aws_elasticache`
  ships **no curated L2 construct at all** - see
  [Notes and cautions](#notes-and-cautions).
- How `elasticache.CfnSubnetGroup` and `elasticache.CfnCacheCluster` map
  1:1 onto the `AWS::ElastiCache::SubnetGroup` and
  `AWS::ElastiCache::CacheCluster` CloudFormation resource types.
- Why a single Availability Zone is enough for this module's VPC
  (`max_azs=1`), unlike RDS/Aurora's mandatory 2-AZ DB subnet group (see
  modules/18_rds_mysql).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc`, `aws_cdk.aws_ec2.SecurityGroup` | L2 |
| Amazon ElastiCache | `aws_cdk.aws_elasticache.CfnSubnetGroup` | L1 (`Cfn*` - no L2 exists) |
| Amazon ElastiCache | `aws_cdk.aws_elasticache.CfnCacheCluster` | L1 (`Cfn*` - no L2 exists) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- floci runs ElastiCache as a real Docker container under the hood (see
  [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md), "Observations and
  limitations") - deploying this module locally takes longer than an S3
  bucket or an SQS queue, and needs more free RAM/CPU.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_22_elasticache.py`](../../tests/unit/test_22_elasticache.py))
check that: exactly one `AWS::ElastiCache::CacheCluster` and exactly one
`AWS::ElastiCache::SubnetGroup` are created, the cache cluster uses the
`redis` engine on a single `cache.t3.micro` node (`NumCacheNodes: 1`), and
every mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
section 7) is present on the cache cluster - note that both of these are
L1 (`Cfn*`) constructs, but the stack-wide `Tags.of()` aspect still applies
the standard `[{"Key": ..., "Value": ...}]` tags list to them exactly like
an L2 construct. They run in well under a second, with no Docker, no
floci, and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_22_elasticache.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth ElastiCacheStack
uv run cdk deploy ElastiCacheStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you have read and understood
[Notes and cautions](#notes-and-cautions) - this module has a real,
ongoing hourly cost the moment it is deployed.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy ElastiCacheStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws elasticache describe-cache-clusters --query "CacheClusters[].{Id:CacheClusterId,Status:CacheClusterStatus,Engine:Engine}"
aws elasticache describe-cache-subnet-groups --query "CacheSubnetGroups[].CacheSubnetGroupName"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
cache cluster visually.

## Clean up

```bash
uv run cdk destroy ElastiCacheStack
```

## Notes and cautions

- **No CDK L2 construct exists for ElastiCache.** `aws_cdk.aws_elasticache`
  provides only L1 (`Cfn*`) constructs, a 1:1 mapping onto the
  CloudFormation resource types - there is no `elasticache.CacheCluster`
  curated class the way there is `aws_rds.DatabaseInstance` for RDS. This
  module therefore builds the subnet group and cache cluster directly from
  `elasticache.CfnSubnetGroup` and `elasticache.CfnCacheCluster` - see
  [`aws_cdk.aws_elasticache.CfnCacheCluster`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnCacheCluster.html)
  in the API reference.
- **Bills hourly on real AWS**, like RDS/Aurora - a `cache.t3.micro` node
  exists (and is billed) continuously from creation until `cdk destroy`,
  independent of whether it is ever read from or written to. Check current
  rates for your region before deploying to a real account.
- This cluster has no authentication (`AUTH` token) or in-transit
  encryption enabled, to keep the example minimal - a production Redis
  deployment should enable both.

## References

- [Amazon ElastiCache - What is Amazon ElastiCache?](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/WhatIs.html)
- [Amazon ElastiCache pricing](https://aws.amazon.com/elasticache/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticache.CfnCacheCluster`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnCacheCluster.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticache.CfnSubnetGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnSubnetGroup.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
