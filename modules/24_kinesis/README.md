<!-- TOC -->

- [Module 24 - Kinesis](#module-24---kinesis)
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

# Module 24 - Kinesis

## Overview

Amazon Kinesis Data Streams is a managed service for ingesting and
processing real-time streaming data (think: a durable, ordered,
replayable log, rather than a simple queue - contrast with modules/26_sqs).
This module creates one stream with a single shard (a shard is a stream's
unit of read/write throughput) and a 24-hour retention period.

## What you will learn

- How `aws_kinesis.Stream` (the CDK L2 construct) turns `shard_count` and
  `retention_period` into a running stream.
- Why a shard, not a queue, is Kinesis's core unit: it determines both the
  stream's throughput and (indirectly, via provisioned mode) its cost.
- The difference between Kinesis's default provisioned capacity mode (pay
  per shard-hour, used here) and its on-demand mode - see
  [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon Kinesis Data Streams | `aws_cdk.aws_kinesis.Stream` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_24_kinesis.py`](../../tests/unit/test_24_kinesis.py))
check that: exactly one `AWS::Kinesis::Stream` is created, it has
`ShardCount: 1` and `RetentionPeriodHours: 24`, and every mandatory tag
(see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is
present on the stream. They run in well under a second, with no Docker, no
floci, and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_24_kinesis.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth KinesisStack
uv run cdk deploy KinesisStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy KinesisStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws kinesis list-streams
aws kinesis describe-stream-summary --stream-name <stream-name-from-above>
aws kinesis put-record --stream-name <stream-name-from-above> --data "hello" --partition-key "demo"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
stream visually.

## Clean up

```bash
uv run cdk destroy KinesisStack
```

## Notes and cautions

- **Kinesis Data Streams bills per shard-hour on real AWS**, in this
  module's default provisioned capacity mode - the one shard here exists
  (and is billed) continuously from creation until `cdk destroy`,
  independent of whether any record is ever put onto or read from it. This
  is much cheaper than the RDS/Aurora/ElastiCache/OpenSearch modules (a
  single shard is a small fraction of their hourly cost), but it is not
  free the way modules/21_dynamodb (in on-demand billing mode) is while
  idle. Check current per-shard-hour rates for your region before deploying
  to a real account.
- Kinesis Data Streams also offers an on-demand capacity mode (no shard
  count to plan, billed by throughput actually used) - this module uses the
  provisioned/`shard_count=` shape instead, since it maps most directly to
  the shard concept this module is teaching.

## References

- [Amazon Kinesis Data Streams - Key concepts](https://docs.aws.amazon.com/streams/latest/dev/key-concepts.html)
- [Amazon Kinesis Data Streams pricing](https://aws.amazon.com/kinesis/data-streams/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_kinesis.Stream`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_kinesis/Stream.html)
