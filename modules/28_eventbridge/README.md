<!-- TOC -->

- [Module 28 - EventBridge (a rule matching a custom application event)](#module-28---eventbridge-a-rule-matching-a-custom-application-event)
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

# Module 28 - EventBridge (a rule matching a custom application event)

## Overview

Amazon EventBridge is a managed **event bus**: a channel that events (small
JSON records describing "something happened") flow through. A **rule**
watches the bus and, when an event matches the rule's **event pattern**
(a set of field-value filters), sends a copy of that event to one or more
**targets** (a Lambda function, an SQS queue, a CloudWatch Logs log group,
...). Every AWS account already has a *default* event bus - AWS services
publish their own events there, and so can your own applications, via the
`PutEvents` API. This module creates one rule on the default bus that
matches a custom application event and logs it.

## What you will learn

- What an event bus, a rule, and an event pattern are, and how they relate.
- The difference between an AWS-service event (like an EC2 state change,
  which has AWS's own fixed `source`/`detail` shape) and a **custom
  application event** - one your own code defines and publishes, with a
  `source` (e.g. `"learning-cdk-python.demo"`) and `detail-type` (e.g.
  `"OrderPlaced"`) you make up yourself.
- How `events.EventPattern(source=[...], detail_type=[...])` expresses "only
  events matching these values" as CDK code.
- How to send a test event with the AWS CLI's `aws events put-events` and see
  it land in CloudWatch Logs.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon EventBridge | `aws_cdk.aws_events.Rule` | L2 |
| Amazon EventBridge | `aws_cdk.aws_events.EventPattern` | L2 (props) |
| Amazon EventBridge | `aws_cdk.aws_events_targets.CloudWatchLogGroup` | L2 |
| Amazon CloudWatch Logs | `aws_cdk.aws_logs.LogGroup` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_28_eventbridge.py`](../../tests/unit/test_28_eventbridge.py))
check that: exactly one rule and one log group are created, the rule's event
pattern matches `source: ["learning-cdk-python.demo"]` and
`detail-type: ["OrderPlaced"]` (this module's whole point), the rule has a
target wired to the log group, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on the
rule. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_28_eventbridge.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth EventBridgeStack
uv run cdk deploy EventBridgeStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(see [Notes and cautions](#notes-and-cautions) - EventBridge custom events
and CloudWatch Logs both have no hourly charge, only usage-based pricing).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy EventBridgeStack --profile <your-aws-cli-profile>
```

## Verify

```bash
# Send a test event matching this module's rule pattern:
aws events put-events --entries '[
  {
    "Source": "learning-cdk-python.demo",
    "DetailType": "OrderPlaced",
    "Detail": "{\"orderId\": \"demo-123\"}"
  }
]'

# See it land in CloudWatch Logs (may take a few seconds):
aws logs tail learning-cdk-python-dev-logs-order-events --since 5m
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
rule and log group visually.

## Clean up

```bash
uv run cdk destroy EventBridgeStack
```

## Notes and cautions

- Matching is exact on the fields you list: an event with a different
  `source` or `detail-type` (for example, a typo) simply does not match and
  is silently not delivered - there is no error to catch, which is why
  testing with `put-events` and `logs tail` matters.
- `install_latest_aws_sdk=False` is set on the `CloudWatchLogGroup` target
  deliberately: by default, the custom resource CDK creates to grant
  EventBridge permission to write into the log group downloads the latest
  AWS SDK at deploy time, which needs outbound internet access this
  learning path should not require when deploying against floci.
- EventBridge's default event bus and custom events have no hourly charge -
  you pay per published event beyond a monthly free tier; CloudWatch Logs
  bills for ingested/stored data. See the pricing references below, and
  re-check current numbers before relying on them.

## References

- [Amazon EventBridge - event patterns](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-event-patterns.html)
- [Amazon EventBridge - sending events with PutEvents](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-putevent.html)
- [Amazon EventBridge pricing](https://aws.amazon.com/eventbridge/pricing/)
- [Amazon CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_events.Rule`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/Rule.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_events.EventPattern`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events/EventPattern.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_events_targets.CloudWatchLogGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_events_targets/CloudWatchLogGroup.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_logs.LogGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_logs/LogGroup.html)
