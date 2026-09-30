<!-- TOC -->

- [Module 44 - Service Quotas (no CDK code)](#module-44---service-quotas-no-cdk-code)
  - [Overview](#overview)
  - [What you will learn](#what-you-will-learn)
  - [AWS services and CDK constructs used](#aws-services-and-cdk-constructs-used)
  - [Prerequisites](#prerequisites)
  - [Tests](#tests)
  - [Run the script](#run-the-script)
  - [Deploy to real AWS (optional)](#deploy-to-real-aws-optional)
  - [Verify](#verify)
  - [Clean up](#clean-up)
  - [Notes and cautions](#notes-and-cautions)
  - [References](#references)

<!-- TOC -->

# Module 44 - Service Quotas (no CDK code)

## Overview

AWS Service Quotas is where every service's account-level limits live (how
many VPCs you can create, how many concurrent Lambda executions you can
run, ...) and where you request an increase when a default is too low. This
module is different from every other module in this repository: **it has
no `stack.py` and deploys nothing**, because Service Quotas has no
CloudFormation/CDK resource to deploy in the first place - see
[Notes and cautions](#notes-and-cautions) for how this was confirmed rather
than assumed. Instead, this module is a runnable `boto3` script,
`script.py`, that lists, inspects, and (optionally) requests an increase
for a quota.

## What you will learn

- That not every AWS service is provisioned infrastructure - some are pure
  APIs over account-level configuration, with nothing for CloudFormation
  or CDK to create, update, or delete.
- How `app.py`'s module-discovery loop (see
  [`../../CLAUDE.md`](../../CLAUDE.md#3-the-module-contract)) skips a
  `modules/*/` directory with no `stack.py`, so this module needs no
  special-casing anywhere else in the repository.
- How to call the Service Quotas API directly with `boto3`:
  `list_service_quotas` (what you have now), `get_service_quota` (detail
  on one), and `request_service_quota_increase` (ask AWS for more).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS Service Quotas | *(none - see Overview)* | N/A |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Docker, floci). Node.js/the CDK Toolkit are **not** needed for this
  module specifically, since there is nothing to `cdk synth`/`deploy`.
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

**This module's test is different from every other module's.** Every other
module's "Tests" section points at a `aws_cdk.assertions.Template` built
from a synthesized CDK stack (see
[`../../docs/TESTING.md`](../../docs/TESTING.md)) - but this module has no
`stack.py` at all (see [Overview](#overview) and
[Notes and cautions](#notes-and-cautions)), so there is no CloudFormation
template to synthesize. Writing a fake stack just to have something to
unit-test would contradict this repository's own guardrail against
inventing constructs (see
[`../../CLAUDE.md`](../../CLAUDE.md#4-do-not-invent-things-the-core-guardrail)).

Instead, [`tests/unit/test_44_resource_quotas.py`](../../tests/unit/test_44_resource_quotas.py)
tests `script.py` itself, with botocore's
[`Stubber`](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.html):
each `boto3` call (`list_service_quotas`, including a second page,
`get_service_quota`, `request_service_quota_increase`) gets a canned
response, so nothing is sent to floci or to real AWS. It also checks that
`main()` never calls `request_service_quota_increase` - the Stubber fails
the test if an unexpected call is made. This covers 100% of `script.py`
(see [`../../docs/TESTING.md`, "Test coverage"](../../docs/TESTING.md#test-coverage)).

```bash
# From the repository root:
uv run pytest tests/unit/test_44_resource_quotas.py -v
uv run ruff check modules/44_resource_quotas/script.py
```

These tests prove the script calls the right API operations with the right
parameters - not that floci or AWS answer them as expected. See
[Run the script](#run-the-script) below for actually exercising the
`boto3` calls against floci.

## Run the script

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run python modules/44_resource_quotas/script.py
```

This lists every quota for `ec2` (the default) and prints the detail for
one example quota code. Pass a different service to explore another one:

```bash
uv run python modules/44_resource_quotas/script.py --service-code lambda --quota-code L-B99A9384
```

`request_service_quota_increase(...)` is defined in `script.py` but **not
called** by default - see [Notes and cautions](#notes-and-cautions) before
uncommenting it.

## Deploy to real AWS (optional)

There is nothing to deploy (see [Overview](#overview)); the same
`script.py` runs against a real account once you stop pointing the AWS
CLI/SDK at floci:

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
AWS_PROFILE=<your-aws-cli-profile> uv run python modules/44_resource_quotas/script.py
```

## Verify

```bash
aws service-quotas list-service-quotas --service-code ec2 --max-results 10
aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A
```

Or open the floci UI at `http://localhost:4566/_floci/ui` - Service Quotas
has no provisioned resources to browse there, but the AWS CLI calls above
work against floci's emulated API the same way they would against real AWS.

## Clean up

Nothing to clean up - this module creates no resources, on floci or on
real AWS. If you ran `request_service_quota_increase(...)` against a real
account, that request itself cannot be "cleaned up" - see
[Notes and cautions](#notes-and-cautions).

## Notes and cautions

- **Why this module has no CDK code, verified rather than assumed**: a
  search of the [AWS resource and property types reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-template-resource-type-ref.html)
  (the canonical list of every `AWS::*` CloudFormation resource type) turns
  up no `AWS::ServiceQuotas::*` entry. This is corroborated by an [AWS CDK
  GitHub discussion](https://github.com/aws/aws-cdk/discussions/22963)
  where CDK maintainers confirm the CDK cannot support Service Quotas as a
  native construct without CloudFormation support existing first, and
  suggest a custom resource (`AwsCustomResource`, which wraps a raw SDK
  call, not a real CloudFormation resource type) as the only CDK-adjacent
  workaround - which this repository's guardrail against inventing
  constructs (see [`../../CLAUDE.md`](../../CLAUDE.md#4-do-not-invent-things-the-core-guardrail))
  treats as out of scope for a "here is the CDK construct for X" teaching
  module. See [Reference 1](#references) for what Service Quotas is, from
  AWS's own docs.
- **floci's service coverage**: as of this writing, the
  [floci - AWS](https://floci.io/aws/) service-coverage page lists
  "Service Quotas" among its ~119 emulated services (`Service Quotas JSON
  1.1`), with no fidelity caveat or "exclusive" marker next to it - so the
  `boto3` calls in `script.py` are expected to work against floci as
  written. Re-check that page yourself before relying on this, since
  service coverage changes over time (see
  [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md#10-observations-and-limitations)
  for this repository's general floci-fidelity caveat).
- `request_service_quota_increase(...)` opens a **real, tracked support
  request** against a real AWS account - it is not instantaneous, not
  free-form, and calling it twice creates two requests, not one. It is
  left commented out in `script.py` on purpose.

## References

- [AWS Service Quotas - What Is Service Quotas?](https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html)
- [AWS resource and property types reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-template-resource-type-ref.html)
- [AWS CDK GitHub discussion - "Is there plan to implement constructs for Service Quota?"](https://github.com/aws/aws-cdk/discussions/22963)
- [Service Quotas - boto3 client reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html)
- [floci - AWS service coverage](https://floci.io/aws/)
