<!-- TOC -->

- [Module 40 - CloudTrail](#module-40---cloudtrail)
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

# Module 40 - CloudTrail

## Overview

AWS CloudTrail records every API call made in an account - who called
what, when, and from where - as an audit log. This module creates one
**trail**: a durable, multi-region record of that activity, delivered to
an S3 bucket the trail itself creates.

## What you will learn

- How `cloudtrail.Trail` creates its own S3 bucket (with the right
  CloudTrail bucket policy already attached) when you do not supply one.
- What `is_multi_region_trail=True` buys you: API activity from *every*
  AWS region delivered to this one trail/bucket, not just the region this
  stack happens to be deployed to.
- What `enable_file_validation=True` buys you: a per-file digital
  digest/signature, so tampering with a delivered log file after the fact
  can be detected.
- What CloudTrail actually costs on real AWS, and what is free -
  see [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS CloudTrail | `aws_cdk.aws_cloudtrail.Trail` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_40_cloudtrail.py`](../../tests/unit/test_40_cloudtrail.py))
check that: exactly one trail (and its own destination S3 bucket) are
created, the trail is multi-region with log file validation enabled (this
module's whole point), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the trail. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_40_cloudtrail.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth CloudTrailStack
uv run cdk deploy CloudTrailStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and read
[Notes and cautions](#notes-and-cautions) first - the trail itself has a
free component, but is not entirely free.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy CloudTrailStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws cloudtrail describe-trails
aws cloudtrail get-trail-status --name <trail-name-or-arn-from-above>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
trail and its destination S3 bucket visually.

## Clean up

```bash
uv run cdk destroy CloudTrailStack
```

## Notes and cautions

- **The first copy of management-event logging is free on real AWS.**
  Every AWS account already gets one free trail's worth of *management*
  event history in the CloudTrail Event history console (no trail
  required), and the first trail's management events delivered to S3 are
  also free. What is **not** free: additional trails' management events,
  and **data events** (S3 object-level activity, Lambda invocations, ...),
  which this module does not enable - see
  [Reference 3](#references) for exact pricing.
- `trail_name=` is set here for consistency with this repository's naming
  policy (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md#8-naming-policy)),
  but the CDK construct's own documentation recommends leaving it unset
  for a non-organization trail and letting CloudFormation generate a name -
  worth knowing if you copy this pattern outside this learning path.
- This module logs to a bucket the trail itself creates and does not
  enable log file encryption with a customer-managed KMS key (SSE-S3 is
  used instead) - see [`../08_kms`](../08_kms/README.md) for a module that
  creates a customer-managed key you could wire in.

## References

- [AWS CloudTrail - CloudTrail concepts](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-concepts.html)
- [AWS CloudTrail - Logging management events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-management-events-with-cloudtrail.html)
- [AWS CloudTrail pricing](https://aws.amazon.com/cloudtrail/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_cloudtrail.Trail`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudtrail/Trail.html)
