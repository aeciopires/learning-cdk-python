<!-- TOC -->

- [Module 42 - Cost Explorer (cost anomaly detection)](#module-42---cost-explorer-cost-anomaly-detection)
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

# Module 42 - Cost Explorer (cost anomaly detection)

## Overview

**Read this section before the rest of this README - it corrects a common
misconception this module's name invites.** "Cost Explorer" refers to two
different things:

1. **Cost Explorer the reporting UI/API** - the console pages and API calls
   (`ce:GetCostAndUsage`, etc.) you use to browse and chart historical
   spend. **This has no CloudFormation/CDK resource at all** and must be
   enabled once, manually, by the account's management/payer account - see
   [Notes and cautions](#notes-and-cautions).
2. **Cost Anomaly Detection** - a related Cost Explorer *feature* that
   watches spend for unusual patterns and alerts you, and **is**
   CloudFormation/CDK-automatable via `AWS::CE::AnomalyMonitor` and
   `AWS::CE::AnomalySubscription`.

This module automates **only #2**. It creates one anomaly **monitor**
(watches per-AWS-service spend) and one **subscription** (emails a
recipient daily when an anomaly exceeds a threshold).

## What you will learn

- The distinction above - the single most important thing this module
  teaches, since it is very easy to conflate the two.
- How `ce.CfnAnomalyMonitor` with `monitor_type="DIMENSIONAL"` and
  `monitor_dimension="SERVICE"` gets you a working, zero-configuration
  anomaly model with no manual cost-category setup.
- Why `threshold_expression` is built with `json.dumps(...)` instead of a
  nested CDK property class: the CloudFormation property is typed as a
  plain JSON string (an `Expression` object serialized to text), not a
  structured object - see [Reference 3](#references).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS Cost Explorer (Cost Anomaly Detection) | `aws_cdk.aws_ce.CfnAnomalyMonitor` | **L1** (`Cfn*`) |
| AWS Cost Explorer (Cost Anomaly Detection) | `aws_cdk.aws_ce.CfnAnomalySubscription` | **L1** (`Cfn*`) |

There is **no L2 construct for either resource** in the current stable
`aws-cdk-lib` (confirmed against the AWS CDK API Reference while writing
this module - see [Reference 4](#references) and
[Reference 5](#references)) - both are L1, 1:1 mappings to their
CloudFormation resources.

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_42_cost_explorer.py`](../../tests/unit/test_42_cost_explorer.py))
check that: exactly one anomaly monitor and one subscription are created,
the monitor builds the zero-configuration per-service (`DIMENSIONAL`/
`SERVICE`) cost model, the subscription's `ThresholdExpression` (parsed
from its JSON string) only alerts above $100 of impact, and every
mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
section 7) is present - as `ResourceTags` on both `AWS::CE::AnomalyMonitor`
and `AWS::CE::AnomalySubscription`. No Docker, floci, or AWS credentials
needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_42_cost_explorer.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth CostExplorerStack
uv run cdk deploy CostExplorerStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created, and read
[Notes and cautions](#notes-and-cautions) first - Cost Explorer's reporting
UI itself is **not** enabled by this stack. Also edit `alert_address` in
`stack.py` to an address you control before deploying for real.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy CostExplorerStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ce get-anomaly-monitors
aws ce get-anomaly-subscriptions
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
monitor and subscription visually.

## Clean up

```bash
uv run cdk destroy CostExplorerStack
```

## Notes and cautions

- **Cost Explorer's reporting UI/API has no CloudFormation/CDK resource
  and must be enabled manually, once, by the account's management (payer)
  account** - see [Reference 1](#references). This stack does not, and
  cannot, do that step for you; it only automates Cost Anomaly Detection
  (a separate, CloudFormation-capable feature of Cost Explorer). Do not
  assume deploying this stack means historical cost reports are now
  available in the console.
- Cost Anomaly Detection itself has **no additional charge** on real AWS
  (confirmed via AWS's own "what's new" announcements for this feature,
  which repeatedly describe new capabilities as shipping "at no additional
  charge" - see [Reference 6](#references)) - but it depends on Cost
  Explorer being enabled (step above) and on enough billing history
  existing to build an anomaly model, which floci does not simulate.
- The `Threshold` property (a flat dollar amount) is deprecated in favor of
  `ThresholdExpression` (used by this module) - see
  [Reference 3](#references) for the full expression grammar
  (`Dimensions`, `And`, `Or`, `Not`).

## References

- [AWS Cost Management - Enable Cost Explorer](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-enable.html)
- [AWS Cost Management - Getting started with Cost Anomaly Detection](https://docs.aws.amazon.com/cost-management/latest/userguide/getting-started-ad.html)
- [AWS::CE::AnomalySubscription - AWS CloudFormation (ThresholdExpression)](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ce-anomalysubscription.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ce.CfnAnomalyMonitor`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ce/CfnAnomalyMonitor.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ce.CfnAnomalySubscription`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ce/CfnAnomalySubscription.html)
- [AWS Cost Anomaly Detection reduces anomaly detection latency (example "what's new" post confirming no additional charge)](https://aws.amazon.com/about-aws/whats-new/2024/05/aws-cost-anomaly-detection-reduces-latency/)
