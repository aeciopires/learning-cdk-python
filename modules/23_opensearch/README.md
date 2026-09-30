<!-- TOC -->

- [Module 23 - Amazon OpenSearch Service](#module-23---amazon-opensearch-service)
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

# Module 23 - Amazon OpenSearch Service

## Overview

Amazon OpenSearch Service is a managed search and analytics engine (a fork
of Elasticsearch). This module creates one small, single-node,
single-Availability-Zone domain (`t3.small.search`) - a public domain (not
placed inside a VPC), with access restricted to callers authenticated as
this AWS account.

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module to a real AWS account.** An OpenSearch data node bills hourly the
moment it exists, even at the smallest instance size - this is one of the
more expensive modules in this learning path.

## What you will learn

- How `aws_opensearchservice.Domain` (the CDK L2 construct) turns
  `capacity`, `ebs`, and `zone_awareness` properties into a running
  OpenSearch cluster.
- Why this module uses `aws_cdk.aws_opensearchservice`, not the older
  `aws_cdk.aws_elasticsearch` module - see
  [Notes and cautions](#notes-and-cautions).
- The public-domain + `access_policies` pattern: instead of placing the
  domain in a VPC (with its own subnet/security-group plumbing, as in
  modules/18_rds_mysql or modules/22_elasticache), this module scopes
  access with an IAM policy statement naming this AWS account as the only
  allowed principal - simpler to reason about for a first look at this
  service.
- The 28-character hard limit on OpenSearch domain names, and how this
  module's `stack.py` handles it - see
  [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon OpenSearch Service | `aws_cdk.aws_opensearchservice.Domain` | L2 |
| Amazon OpenSearch Service | `aws_cdk.aws_opensearchservice.EngineVersion`, `CapacityConfig`, `EbsOptions`, `ZoneAwarenessConfig` | L2 (helpers) |
| AWS IAM | `aws_cdk.aws_iam.PolicyStatement`, `aws_cdk.aws_iam.AccountPrincipal` | L2 (helpers) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- **floci's OpenSearch coverage is not verified as complete for this
  module** - the authors of this learning path could not confirm, at the
  time of writing, that floci's OpenSearch emulation is fully faithful (for
  example, for access-policy enforcement or the exact API surface this
  domain exposes). Treat `cdk deploy`/`cdk synth` against floci here as "the
  CDK code is valid and floci accepts the CloudFormation template", not as
  a guarantee that every OpenSearch API call will behave identically to a
  real account. If you want to be certain this module behaves like real
  OpenSearch, prefer verifying against a real (disposable) AWS account -
  see [Deploy to real AWS](#deploy-to-real-aws-optional) and its cost
  warning first.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_23_opensearch.py`](../../tests/unit/test_23_opensearch.py))
check that: exactly one `AWS::OpenSearchService::Domain` is created, it is
a single-node, single-AZ deployment (`EngineVersion: OpenSearch_3.7`,
`InstanceCount: 1`, `InstanceType: t3.small.search`,
`ZoneAwarenessEnabled: false`), the synthesized `DomainName` respects
Amazon OpenSearch Service's hard 28-character limit (see "Notes and
cautions" below), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the domain. They run in well under a second, with no Docker, no floci, and
no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_23_opensearch.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth OpenSearchStack
uv run cdk deploy OpenSearchStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you have read and understood
[Notes and cautions](#notes-and-cautions) - this module has a real,
ongoing hourly cost the moment it is deployed.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy OpenSearchStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws opensearch list-domain-names
aws opensearch describe-domain --domain-name <domain-name-from-above>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
domain visually.

## Clean up

```bash
uv run cdk destroy OpenSearchStack
```

## Notes and cautions

- **This is one of the more expensive modules in this learning path on real
  AWS.** An OpenSearch data node bills **hourly from the moment it exists**
  - even the smallest instance size (`t3.small.search`) used here - and
  this module recommends verifying it primarily against **floci**, not a
  real account left running, precisely because of this cost. See the
  pricing reference below and check current rates for your region if you
  do deploy it for real.
- **Domain name length limit.** Amazon OpenSearch Service enforces a hard
  28-character limit on domain names. This repository's usual
  `product-environment-service-purpose` name (see
  [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md), "Naming policy") is
  longer than that for most `product`/`environment` values, so `stack.py`
  builds the full, policy-compliant name with `resource_name()` first and
  only then truncates it to 28 characters as the very last step, purely to
  satisfy this one service's limit - not a general exception to the naming
  policy. See `stack.py`'s comment at the `domain_name` assignment for the
  exact reasoning, and
  [`REQUIREMENTS.md`, section 8](../../REQUIREMENTS.md#8-naming-policy) for
  the general policy this is a documented, service-specific exception to.
- **floci coverage is not confirmed for OpenSearch** - see
  [Prerequisites](#prerequisites). Say so honestly rather than assuming: if
  something behaves unexpectedly against floci for this module, that may be
  a floci coverage gap rather than a mistake in this module's code.
- This domain is public (no VPC) with access scoped to the deploying AWS
  account via `access_policies` - not placed behind a VPC security group,
  unlike modules/18_rds_mysql or modules/22_elasticache. A production
  OpenSearch domain handling sensitive data would typically use VPC access
  instead.
- `zone_awareness` is disabled and there is only one data node - the
  cheapest possible configuration, with no high availability. Don't copy
  this configuration for anything that needs to survive a single node
  failure.

## References

- [Amazon OpenSearch Service - Identity and access management](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/ac.html)
- [Amazon OpenSearch Service pricing](https://aws.amazon.com/opensearch-service/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_opensearchservice.Domain`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_opensearchservice/Domain.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_opensearchservice.EngineVersion`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_opensearchservice/EngineVersion.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_iam.AccountPrincipal`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/AccountPrincipal.html)
- [floci - AWS service coverage](https://floci.io/aws/)
