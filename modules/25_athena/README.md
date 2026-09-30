<!-- TOC -->

- [Module 25 - Athena](#module-25---athena)
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

# Module 25 - Athena

## Overview

Amazon Athena is a serverless, interactive query service that runs SQL
directly against data in Amazon S3 - there is no database server to
provision; you only pay for the queries you run. This module creates the
two pieces of infrastructure Athena itself needs before you can run a
query: an S3 bucket to hold query results, and an Athena workgroup
(a named, isolated query-execution context) pointed at that bucket.

## What you will learn

- **Why this module uses an L1 (`Cfn*`) construct for the workgroup.**
  Unlike `aws_s3.Bucket` or `aws_dynamodb.Table`, `aws_cdk.aws_athena` ships
  **no curated L2 construct at all** - see
  [Notes and cautions](#notes-and-cautions).
- The nested CloudFormation property shape a `CfnWorkGroup` needs:
  `WorkGroupConfigurationProperty` wrapping a `ResultConfigurationProperty`
  that points at the S3 bucket's `output_location`.
- Why Athena itself has no "database" resource to create: the actual
  tables/schemas it queries live in a separate catalog (typically AWS Glue
  Data Catalog, out of scope for this module) - a workgroup only controls
  *where query results land* and *how queries in it are executed*.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon S3 | `aws_cdk.aws_s3.Bucket` | L2 |
| Amazon Athena | `aws_cdk.aws_athena.CfnWorkGroup` | L1 (`Cfn*` - no L2 exists) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_25_athena.py`](../../tests/unit/test_25_athena.py))
check that: exactly one `AWS::Athena::WorkGroup` and exactly one
`AWS::S3::Bucket` are created, the workgroup's result configuration points
at an output location (the results bucket), the bucket blocks all public
access, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
both resources - note that the workgroup has no `Name` tag (`stack.py`
only calls `apply_name_tag()` on the bucket), so only the 6 stack-wide tags
are asserted on it. They run in well under a second, with no Docker, no
floci, and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_25_athena.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth AthenaStack
uv run cdk deploy AthenaStack --require-approval never
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy AthenaStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws athena list-work-groups
aws athena get-work-group --work-group <workgroup-name-from-above>
aws s3 ls s3://<results-bucket-name-from-above>/
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
workgroup and the results bucket visually.

## Clean up

```bash
uv run cdk destroy AthenaStack
```

`auto_delete_objects=True` on the results bucket lets `cdk destroy` remove
it directly, even if Athena has already written query results into it -
without this, CloudFormation would refuse to delete a non-empty bucket.

## Notes and cautions

- **No CDK L2 construct exists for Athena.** `aws_cdk.aws_athena` provides
  only L1 (`Cfn*`) constructs - there is no `athena.WorkGroup` curated
  class. This module therefore builds the workgroup directly from
  `athena.CfnWorkGroup`, a 1:1 mapping onto the `AWS::Athena::WorkGroup`
  CloudFormation resource type, with its nested
  `WorkGroupConfigurationProperty`/`ResultConfigurationProperty` shapes -
  see
  [`aws_cdk.aws_athena.CfnWorkGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_athena/CfnWorkGroup.html)
  in the API reference.
- **Athena itself has no hourly cost.** Unlike every RDS/Aurora/
  ElastiCache/OpenSearch module in this path, Athena bills **per TB of data
  scanned by each query**, not by the hour - an idle workgroup with no
  queries run against it costs nothing. The only ongoing cost this module
  could create is standard S3 storage for whatever query results
  accumulate in the results bucket.
- This module does not create any table or database for Athena to query
  against (that lives in a data catalog, not covered here) - running an
  actual `SELECT` against this workgroup needs a table defined elsewhere
  first.

## References

- [Amazon Athena - Query results and recent queries](https://docs.aws.amazon.com/athena/latest/ug/querying.html)
- [Amazon Athena pricing](https://aws.amazon.com/athena/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_athena.CfnWorkGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_athena/CfnWorkGroup.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_s3.Bucket`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3/Bucket.html)
