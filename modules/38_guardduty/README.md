<!-- TOC -->

- [Module 38 - GuardDuty](#module-38---guardduty)
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

# Module 38 - GuardDuty

## Overview

Amazon GuardDuty is a threat-detection service: it continuously analyzes
account activity (CloudTrail management/S3 data events, VPC Flow Logs, DNS
logs, and more) for signs of compromise - without you running any agents
or scanners yourself. This module creates the one resource GuardDuty needs
to start: a **detector**.

## What you will learn

- How enabling GuardDuty in an account/region is a single resource
  (`CfnDetector`), not a service you separately "turn on" in the console
  first.
- What `finding_publishing_frequency` controls (how often GuardDuty
  delivers newly-detected findings to CloudWatch Events/EventBridge - it
  does not change how often GuardDuty *looks* for threats).
- **The one-detector-per-region limit** - see
  [Notes and cautions](#notes-and-cautions), the most important thing to
  know before deploying this module anywhere but floci.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon GuardDuty | `aws_cdk.aws_guardduty.CfnDetector` | **L1** (`Cfn*`) |

There is **no L2 construct for GuardDuty** in the current stable
`aws-cdk-lib` (confirmed against the
[AWS CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_guardduty/CfnDetector.html)
while writing this module) - this module uses the L1 `CfnDetector`, a 1:1
mapping to the `AWS::GuardDuty::Detector` CloudFormation resource.

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_38_guardduty.py`](../../tests/unit/test_38_guardduty.py))
check that: exactly one detector is created, it is actually enabled
(`Enable: true` - this module's whole point), it publishes findings every
15 minutes, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present. No
Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_38_guardduty.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth GuardDutyStack
uv run cdk deploy GuardDutyStack --require-approval never
```

## Deploy to real AWS (optional)

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module against a real account** - it will fail outright if GuardDuty is
already enabled in the target account/region.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy GuardDutyStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws guardduty list-detectors
aws guardduty get-detector --detector-id <detector-id-from-above>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
detector's resources visually.

## Clean up

```bash
uv run cdk destroy GuardDutyStack
```

## Notes and cautions

- **An AWS account can have only one GuardDuty detector per region.** If
  GuardDuty is already enabled in your target account/region - including
  indirectly, via an AWS Organizations delegated administrator account
  managing GuardDuty for the whole organization - deploying this stack
  against real AWS will fail with a "the request is rejected because a
  detector already exists" error. Check first with
  `aws guardduty list-detectors` (against real AWS, not floci) before
  deploying. See [Reference 1](#references).
- **GuardDuty has a real, usage-based cost on real AWS**, driven by the
  volume of CloudTrail events, VPC Flow Logs, and DNS logs it analyzes -
  see [Reference 3](#references). It has no free tier beyond an initial
  30-day trial for new detectors. floci has no such cost.
- This module enables GuardDuty with its default data sources; it does not
  enable the optional protection plans (S3 Malware Protection, EKS
  Protection, RDS Protection, Lambda Protection, ...), each billed and
  configured separately - see [Reference 2](#references).

## References

- [Amazon GuardDuty - What is Amazon GuardDuty?](https://docs.aws.amazon.com/guardduty/latest/ug/what-is-guardduty.html)
- [Amazon GuardDuty - Protection plans](https://docs.aws.amazon.com/guardduty/latest/ug/guardduty-features-activation-model.html)
- [Amazon GuardDuty pricing](https://aws.amazon.com/guardduty/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_guardduty.CfnDetector`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_guardduty/CfnDetector.html)
