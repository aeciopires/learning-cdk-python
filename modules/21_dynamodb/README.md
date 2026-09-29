<!-- TOC -->

- [Module 21 - DynamoDB](#module-21---dynamodb)
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

# Module 21 - DynamoDB

## Overview

Amazon DynamoDB is a fully managed NoSQL key-value/document database. This
module creates one table with a single string partition key (`pk`), billed
in "pay-per-request" (on-demand) mode - no capacity to plan or provision
ahead of time.

## What you will learn

- How `aws_dynamodb.Table` (the CDK L2 construct) turns a partition key and
  a billing mode into a running table.
- The difference between DynamoDB's two capacity modes:
  `BillingMode.PAY_PER_REQUEST` (pay only for the reads/writes you actually
  make, used here) versus `BillingMode.PROVISIONED` (reserve read/write
  capacity units ahead of time, and pay for them whether used or not).
- Why this module uses the classic `Table` construct rather than the newer
  `TableV2` construct - see [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon DynamoDB | `aws_cdk.aws_dynamodb.Table` | L2 |
| Amazon DynamoDB | `aws_cdk.aws_dynamodb.Attribute`, `aws_cdk.aws_dynamodb.BillingMode` | L2 (helpers) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_21_dynamodb.py`](../../tests/unit/test_21_dynamodb.py))
check that: exactly one `AWS::DynamoDB::Table` is created, `BillingMode` is
`PAY_PER_REQUEST` (this module's whole point - no idle baseline cost), the
table has a single `pk` string partition key, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present.
They run in well under a second, with no Docker, no floci, and no AWS
credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_21_dynamodb.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth DynamoDbStack
uv run cdk deploy DynamoDbStack --require-approval never
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy DynamoDbStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws dynamodb list-tables
aws dynamodb describe-table --table-name <table-name-from-above>
aws dynamodb put-item --table-name <table-name-from-above> --item '{"pk": {"S": "example"}}'
aws dynamodb get-item --table-name <table-name-from-above> --key '{"pk": {"S": "example"}}'
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
table and its items visually.

## Clean up

```bash
uv run cdk destroy DynamoDbStack
```

`removal_policy=RemovalPolicy.DESTROY` lets `cdk destroy` remove the table
(and any items in it) directly - a production table would typically use
`RemovalPolicy.RETAIN` instead, to avoid an accidental `cdk destroy`
deleting real data.

## Notes and cautions

- **No hourly or baseline cost while idle.** `BillingMode.PAY_PER_REQUEST`
  means you are billed only for the read/write requests and storage you
  actually use - an idle table with no traffic costs nothing beyond
  whatever data it already stores. This is unlike every RDS/Aurora/
  ElastiCache/OpenSearch module in this learning path (18, 19, 20, 22, 23),
  which bill hourly regardless of traffic.
- **`Table` vs. `TableV2`:** `aws_cdk.aws_dynamodb` also ships a newer
  `TableV2` construct, built around a `billing=`/`Billing` class shape and
  aimed primarily at multi-Region global tables. This module deliberately
  uses the long-stable classic `Table` construct instead - it is
  unambiguously the right fit for a single-Region table like this one, and
  its `billing_mode=BillingMode.PAY_PER_REQUEST` shape is the one most of
  the CDK's own documentation and examples still show first. If a later
  module in this learning path needs DynamoDB global tables, that would be
  the place to introduce `TableV2` (with its own exact API verified against
  current docs at that time, per CLAUDE.md section 4).

## References

- [Amazon DynamoDB - Core components](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html)
- [Amazon DynamoDB pricing](https://aws.amazon.com/dynamodb/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_dynamodb.Table`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Table.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_dynamodb.Attribute`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/Attribute.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_dynamodb.BillingMode`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_dynamodb/BillingMode.html)
