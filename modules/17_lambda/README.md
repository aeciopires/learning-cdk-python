<!-- TOC -->

- [Module 17 - Lambda (one inline-code function)](#module-17---lambda-one-inline-code-function)
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

# Module 17 - Lambda (one inline-code function)

## Overview

AWS Lambda runs your code without you managing a server: you give it a
function, Lambda runs it on demand and bills only for the time it actually
executes. This module creates one Lambda function whose entire source code
is a short Python string, passed straight to CDK with
`lambda_.Code.from_inline(...)` - no packaging, no Docker, nothing to build.

## What you will learn

- How `aws_lambda.Function` turns code, a handler name, a runtime, and an
  execution role into a deployable function.
- `Code.from_inline(...)` - the simplest possible way to hand Lambda some
  Python, useful for tiny, dependency-free functions like this one's
  (see [Notes and cautions](#notes-and-cautions) for its limits).
- Why `aws_lambda` is imported as `lambda_` in this module (and every other
  module that touches Lambda in this path) - `lambda` is a Python keyword,
  so it cannot be used as an import name; see
  [`../../CLAUDE.md`, section 9](../../CLAUDE.md#9-pythoncdk-conventions).
- The execution role pattern every Lambda function in AWS needs: an
  `iam.Role` only the Lambda service can assume, plus (at minimum) the
  AWS-managed `AWSLambdaBasicExecutionRole` policy for CloudWatch Logs -
  the same pattern `modules/01_iam` introduces.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS Lambda | `aws_cdk.aws_lambda.Function` | L2 |
| AWS Lambda | `aws_cdk.aws_lambda.Code.from_inline` | L2 (helper) |
| AWS Lambda | `aws_cdk.aws_lambda.Runtime` | L2 (helper) |
| AWS IAM | `aws_cdk.aws_iam.Role` | L2 |
| AWS IAM | `aws_cdk.aws_iam.ManagedPolicy.from_aws_managed_policy_name` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_17_lambda.py`](../../tests/unit/test_17_lambda.py))
check that: exactly one function and one execution role are created, the
function uses the `python3.13` runtime with handler `index.handler` (this
module's whole point), its code is inline (`ZipFile`, not an S3 asset -
matching `Code.from_inline`), the execution role's trust policy only
allows `lambda.amazonaws.com` to assume it, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the function. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_17_lambda.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth LambdaStack
uv run cdk deploy LambdaStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(Lambda's free tier is generous, and this function only runs when invoked -
see [Notes and cautions](#notes-and-cautions)).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy LambdaStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws lambda invoke --function-name learning-cdk-python-dev-lambda-hello /tmp/lambda-out.json
cat /tmp/lambda-out.json
# expected: {"statusCode": 200, "body": "hello from learning-cdk-python"}
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
function visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) for
how the UI is enabled in this repository's `docker-compose.yml`).

## Clean up

```bash
uv run cdk destroy LambdaStack
```

## Notes and cautions

- **`Code.from_inline` has real limits**, which is exactly why this module
  suits it: it only accepts a plain-text source string (no binary files, no
  third-party dependencies, a total code size limit far below Lambda's
  normal deployment package limits). It is a good fit for a beginner's
  first function, and a poor fit for anything that needs a package from
  PyPI. See the maxfriedrich.de article in References for how to package a
  real function's dependencies with `uv` and deploy it with CDK once you
  outgrow `from_inline` - out of scope for this minimal example.
- AWS Lambda has a perpetual free tier (a monthly number of free requests
  and free compute-milliseconds) even outside the 12-month
  [AWS Free Tier](https://aws.amazon.com/free/) window - see
  [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/) for current
  numbers. This module's function, invoked only a handful of times while
  you learn, will not meaningfully cost anything on a real account.
- `handler="index.handler"` follows Lambda's convention for inline code:
  the inline string is treated as a file named `index.py`, and
  `index.handler` means "call the function named `handler` inside it".

## References

- [AWS Lambda - What is AWS Lambda?](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html)
- [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_lambda.Function`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_lambda.Code`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Code.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_lambda.Runtime`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Runtime.html)
- [AWS CDK v2 Developer Guide - Working with the AWS CDK in Python (Python-keyword import aliasing)](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html#python-cdk-idioms)
- [uv + AWS CDK + Lambda packaging, for when a real function needs third-party dependencies](https://maxfriedrich.de/2025/01/02/uv-lambda-cdk/)
