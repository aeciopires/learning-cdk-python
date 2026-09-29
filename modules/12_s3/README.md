<!-- TOC -->

- [Module 12 - S3 (a versioned, encrypted, private bucket)](#module-12---s3-a-versioned-encrypted-private-bucket)
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

# Module 12 - S3 (a versioned, encrypted, private bucket)

## Overview

Amazon S3 (Simple Storage Service) is AWS's object storage service - files
("objects") stored inside "buckets", accessed over HTTPS rather than a
filesystem path. This module creates one bucket with versioning turned on,
server-side encryption, and every public-access door closed, using the CDK
L2 (curated) `Bucket` construct.

## What you will learn

- How `aws_s3.Bucket` turns a handful of properties into a bucket with
  sensible security defaults, instead of the AWS Console's many separate
  checkboxes.
- What "versioning" (keeping every previous version of an object instead of
  overwriting it) and "block public access" (a bucket-level setting that
  overrides any individual object/bucket policy trying to make something
  public) actually do.
- Why `enforce_ssl=True` matters: it adds a bucket policy statement that
  denies any request made over plain HTTP, not just HTTPS.
- The tradeoff behind `removal_policy=DESTROY` + `auto_delete_objects=True`
  in a learning path versus `RemovalPolicy.RETAIN` in production - see
  [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon S3 | `aws_cdk.aws_s3.Bucket` | L2 |
| Amazon S3 | `aws_cdk.aws_s3.BlockPublicAccess` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_12_s3.py`](../../tests/unit/test_12_s3.py))
check that: exactly one bucket is created, versioning is enabled (this
module's whole point), every public-access door is blocked
(`BlockPublicAcls`/`BlockPublicPolicy`/`IgnorePublicAcls`/`RestrictPublicBuckets`
all `true`), the bucket has S3-managed (`AES256`) default encryption, and
every mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
section 7) is present. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_12_s3.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth S3Stack
uv run cdk deploy S3Stack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(an S3 bucket has no hourly cost by itself - see
[Notes and cautions](#notes-and-cautions) for the small cost that *does*
apply once you store objects in it).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy S3Stack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws s3api get-bucket-versioning --bucket learning-cdk-python-dev-s3-app-data
aws s3api get-bucket-encryption --bucket learning-cdk-python-dev-s3-app-data
aws s3api get-public-access-block --bucket learning-cdk-python-dev-s3-app-data
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
bucket visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) for
how the UI is enabled in this repository's `docker-compose.yml`).

## Clean up

```bash
uv run cdk destroy S3Stack
```

## Notes and cautions

- **`auto_delete_objects=True` provisions a small custom-resource Lambda
  function under the hood** - CDK adds a Lambda-backed CloudFormation custom
  resource that empties the bucket right before CloudFormation deletes it.
  This is normal and expected; you will see an extra Lambda function and IAM
  role appear alongside the bucket when you deploy this stack.
- **`removal_policy=DESTROY` + `auto_delete_objects=True` is a
  learning-path choice, not a production default.** It exists so
  `cdk destroy` fully cleans up this module in floci (and in a real sandbox
  account) with no manual "empty the bucket first" step. Production buckets
  almost always keep `RemovalPolicy.RETAIN` (the CDK default when
  `removal_policy` is not set at all) precisely so a mistaken stack deletion
  can never take real data with it.
- Storing objects in S3 on real AWS has a small, usage-based cost
  (per-GB-month storage, plus request and data-transfer charges) - see the
  [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/) page. An empty
  bucket, on its own, costs nothing.
- Bucket names are globally unique across all of AWS, not just your account -
  see the naming-rules link below if `cdk deploy` reports a name collision
  on real AWS (unlikely with this module's `product-environment-...` naming
  scheme, but possible).

## References

- [Amazon S3 - What is Amazon S3?](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
- [Amazon S3 - Bucket naming rules](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucketnamingrules.html)
- [Amazon S3 - Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html)
- [Amazon S3 - Blocking public access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [Amazon S3 pricing](https://aws.amazon.com/s3/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_s3.Bucket`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3/Bucket.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_s3.BlockPublicAccess`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3/BlockPublicAccess.html)
