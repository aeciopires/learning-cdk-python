<!-- TOC -->

- [Module 22 - ElastiCache (Valkey or Redis OSS)](#module-22---elasticache-valkey-or-redis-oss)
  - [Overview](#overview)
  - [What you will learn](#what-you-will-learn)
  - [AWS services and CDK constructs used](#aws-services-and-cdk-constructs-used)
  - [Prerequisites](#prerequisites)
  - [Choosing the engine: Valkey or Redis OSS](#choosing-the-engine-valkey-or-redis-oss)
  - [Tests](#tests)
  - [Deploy with floci (local, free)](#deploy-with-floci-local-free)
  - [Deploy to real AWS (optional)](#deploy-to-real-aws-optional)
  - [Verify](#verify)
  - [Clean up](#clean-up)
  - [Notes and cautions](#notes-and-cautions)
  - [References](#references)

<!-- TOC -->

# Module 22 - ElastiCache (Valkey or Redis OSS)

## Overview

Amazon ElastiCache is a managed in-memory data store, typically used as a
cache or a fast key-value store in front of a slower primary database. This
module creates one single-node cache (`cache.t3.micro`) running **Valkey**
(the default) or **Redis OSS** - you choose with one environment variable -
in its own dedicated single-AZ VPC, reachable only from inside that VPC,
with encryption in transit and at rest.

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module to a real AWS account.** Like the RDS/Aurora modules, an ElastiCache
node bills hourly the moment it exists.

## What you will learn

- **Valkey vs. Redis OSS.** [Valkey](https://valkey.io) describes itself as
  "an open source (BSD) high-performance key/value datastore" backed by the
  Linux Foundation, which includes BSD-licensed Redis code and is
  compatible with Redis OSS clients. ElastiCache offers both engines, and
  this module serves both on the same port (6379).
- **Why this module uses a *replication group*, not a *cache cluster*.**
  CloudFormation's `AWS::ElastiCache::CacheCluster` accepts only the
  `memcached` and `redis` engines - its documentation says "To create a
  Valkey cluster, use `AWS::ElastiCache::ReplicationGroup`", which accepts
  both `valkey` and `redis`. With one node (`NumCacheClusters: 1`) it is
  still a single-node cache.
- **Why this module uses L1 (`Cfn*`) constructs, not L2.** Unlike
  `aws_ec2.Vpc` or `aws_rds.DatabaseInstance`, `aws_cdk.aws_elasticache`
  ships **no curated L2 construct at all** - see
  [Notes and cautions](#notes-and-cautions).
- How to make a stack configurable with an environment variable that is
  validated at `cdk synth` time (`CDK_ELASTICACHE_ENGINE`), so a typo
  fails before anything is deployed.
- Why a single Availability Zone is enough for this module's VPC
  (`max_azs=1`), unlike RDS/Aurora's mandatory 2-AZ DB subnet group (see
  modules/18_rds_mysql).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc`, `aws_cdk.aws_ec2.SecurityGroup` | L2 |
| Amazon ElastiCache | `aws_cdk.aws_elasticache.CfnSubnetGroup` | L1 (`Cfn*` - no L2 exists) |
| Amazon ElastiCache | `aws_cdk.aws_elasticache.CfnReplicationGroup` | L1 (`Cfn*` - no L2 exists) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- See [Deploy with floci](#deploy-with-floci-local-free) for what floci
  does and doesn't create for this module.

## Choosing the engine: Valkey or Redis OSS

| `CDK_ELASTICACHE_ENGINE` | Engine | Replication group id |
|---|---|---|
| unset, or `valkey` | Valkey | `learning-cdk-python-<environment>-valkey` |
| `redis` | Redis OSS | `learning-cdk-python-<environment>-redis` |
| anything else | - | `cdk synth` fails with `Invalid CDK_ELASTICACHE_ENGINE=...` |

```bash
# From the repository root - pick one:
export CDK_ELASTICACHE_ENGINE=valkey   # the default
export CDK_ELASTICACHE_ENGINE=redis
```

Or set it in your `.env` (see [`../../.env.example`](../../.env.example)).
Only the `Engine` property and the resource name change - the node type,
port, encryption, and security group are identical for both engines.

Switching engine on an already-deployed stack **replaces** the cache (a new
replication group id means a new resource; its data is not copied). The
security group's description is deliberately engine-neutral: changing it
would force CloudFormation to replace the security group, and a security
group with a fixed name can't be replaced ("already exists").

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_22_elasticache.py`](../../tests/unit/test_22_elasticache.py))
check that: exactly one `AWS::ElastiCache::ReplicationGroup`, no
`AWS::ElastiCache::CacheCluster`, and one `AWS::ElastiCache::SubnetGroup`
are created; Valkey is the default engine; `CDK_ELASTICACHE_ENGINE` selects
`valkey` or `redis` (case-insensitive) and rejects anything else; both
engines get a single encrypted `cache.t3.micro` node; the security group
opens only port 6379 and doesn't change between engines; and every
mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section
7) is on the replication group. They use pytest's `monkeypatch` to set
`CDK_ELASTICACHE_ENGINE` per test, and run in under a second, with no
Docker, no floci, and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_22_elasticache.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth ElastiCacheStack
uv run cdk deploy ElastiCacheStack --require-approval never

# the same stack with Redis OSS instead of Valkey:
CDK_ELASTICACHE_ENGINE=redis uv run cdk deploy ElastiCacheStack --require-approval never
```

**What floci creates here (checked while writing this module - re-check
with newer floci versions):** the deploy succeeds and the VPC, subnet,
security group, and cache subnet group are created, but floci's
CloudFormation implementation records the `AWS::ElastiCache::ReplicationGroup`
without starting a cache - `aws elasticache describe-replication-groups`
returns an empty list afterwards. floci's ElastiCache *API* does run real
Valkey/Redis containers, though, so you can try the engine itself by
calling the API directly (see [Verify](#verify)).

## Deploy to real AWS (optional)

Only do this if you have read and understood
[Notes and cautions](#notes-and-cautions) - this module has a real,
ongoing hourly cost the moment it is deployed.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy ElastiCacheStack --profile <your-aws-cli-profile>
```

## Verify

On real AWS:

```bash
aws elasticache describe-replication-groups --query "ReplicationGroups[].{Id:ReplicationGroupId,Status:Status,Engine:Engine,TLS:TransitEncryptionEnabled}"
aws elasticache describe-cache-subnet-groups --query "CacheSubnetGroups[].CacheSubnetGroupName"
```

On floci, check what CloudFormation recorded, then (optionally) create a
real Valkey replication group through floci's ElastiCache API to try the
engine itself - and delete it afterwards:

```bash
aws cloudformation describe-stack-resources --stack-name ElastiCacheStack \
  --query "StackResources[].[ResourceType,ResourceStatus]" --output table

aws elasticache create-replication-group --replication-group-id try-valkey \
  --replication-group-description "try valkey on floci" --engine valkey \
  --cache-node-type cache.t3.micro --num-cache-clusters 1
aws elasticache describe-replication-groups --query "ReplicationGroups[].[ReplicationGroupId,Engine,Status]"
aws elasticache delete-replication-group --replication-group-id try-valkey
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
resources visually.

## Clean up

```bash
uv run cdk destroy ElastiCacheStack
```

## Notes and cautions

- **No CDK L2 construct exists for ElastiCache.** `aws_cdk.aws_elasticache`
  provides only L1 (`Cfn*`) constructs, a 1:1 mapping onto the
  CloudFormation resource types - there is no curated `ReplicationGroup`
  class the way there is `aws_rds.DatabaseInstance` for RDS. This module
  therefore builds the subnet group and replication group directly from
  `elasticache.CfnSubnetGroup` and `elasticache.CfnReplicationGroup` - see
  [`aws_cdk.aws_elasticache.CfnReplicationGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnReplicationGroup.html)
  in the API reference.
- **Bills hourly on real AWS**, like RDS/Aurora - a `cache.t3.micro` node
  exists (and is billed) continuously from creation until `cdk destroy`,
  independent of whether it is ever read from or written to. Check the
  current rates for your engine (Valkey or Redis OSS) and region before
  deploying to a real account.
- **Encryption:** `TransitEncryptionEnabled` is required by CloudFormation
  when creating a Valkey replication group, and this module enables it
  (and encryption at rest) for Redis OSS too, so both engines behave the
  same. Clients must therefore connect with TLS. There is no
  authentication (`AuthToken` or user groups) - a production deployment
  should add one.
- **No automatic failover:** `AutomaticFailoverEnabled` is `false` because
  it needs at least 2 nodes (`NumCacheClusters >= 2`) - a production cache
  usually runs a primary plus replicas across AZs.
- **No `EngineVersion` is pinned**, so ElastiCache uses its current default
  for the chosen engine - run `aws elasticache describe-cache-engine-versions
  --engine valkey` (or `redis`) to see the versions available today.

## References

- [Amazon ElastiCache - What is Amazon ElastiCache?](https://docs.aws.amazon.com/AmazonElastiCache/latest/dg/WhatIs.html)
- [Amazon ElastiCache pricing](https://aws.amazon.com/elasticache/pricing/)
- [AWS CloudFormation - `AWS::ElastiCache::ReplicationGroup`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-elasticache-replicationgroup.html)
- [AWS CloudFormation - `AWS::ElastiCache::CacheCluster`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-elasticache-cachecluster.html) (the `Engine` property: `memcached` or `redis` only)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticache.CfnReplicationGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnReplicationGroup.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticache.CfnSubnetGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticache/CfnSubnetGroup.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
- [Valkey](https://valkey.io)
- [floci - AWS services](https://floci.io/aws/)
