<!-- TOC -->

- [Module 27 - SNS (a topic fanning out to SQS)](#module-27---sns-a-topic-fanning-out-to-sqs)
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

# Module 27 - SNS (a topic fanning out to SQS)

## Overview

Amazon SNS (Simple Notification Service) is a fully managed pub/sub topic:
one producer publishes a message once, and SNS delivers a copy to every
subscriber - this "one message in, many copies out" pattern is called
**fan-out**. This module creates one SNS topic and subscribes one SQS queue
(built in module 26) to it, so publishing a single message results in a
message landing in the queue.

## What you will learn

- How `aws_sns.Topic` (the CDK L2 construct) creates a publish/subscribe
  topic.
- The SNS-to-SQS fan-out pattern: `topic.add_subscription(sns_subscriptions
  .SqsSubscription(queue))` both creates the subscription *and* attaches the
  SQS resource policy that lets SNS deliver into the queue - no manual IAM
  policy required.
- Why this module does not include an email subscription (see
  [Notes and cautions](#notes-and-cautions)).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon SNS | `aws_cdk.aws_sns.Topic` | L2 |
| Amazon SNS | `aws_cdk.aws_sns_subscriptions.SqsSubscription` | L2 |
| Amazon SQS | `aws_cdk.aws_sqs.Queue` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_27_sns.py`](../../tests/unit/test_27_sns.py))
check that: exactly one topic and exactly one queue are created, exactly one
SNS subscription exists and its protocol is `sqs` (the fan-out this module
exists to teach), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on the
topic. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_27_sns.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth SnsStack
uv run cdk deploy SnsStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(see [Notes and cautions](#notes-and-cautions) - SNS has no hourly charge).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy SnsStack --profile <your-aws-cli-profile>
```

## Verify

```bash
# Find the topic and confirm the queue is subscribed:
aws sns list-topics
aws sns list-subscriptions-by-topic --topic-arn <topic-arn-from-above>

# Publish a message and see it land in the queue:
aws sns publish --topic-arn <topic-arn-from-above> --message "hello from module 27"
aws sqs get-queue-url --queue-name learning-cdk-python-dev-sqs-notifications
aws sqs receive-message --queue-url <queue-url-from-above>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
topic and queue visually.

## Clean up

```bash
uv run cdk destroy SnsStack
```

## Notes and cautions

- **Email subscriptions need manual confirmation and are not included here.**
  A real-world SNS topic very often has an `sns_subscriptions
  .EmailSubscription("someone@example.com")` subscriber, but SNS emails that
  address a confirmation link it must click before any notification is
  delivered - a step CDK cannot automate (there is no API to click a link in
  someone's inbox), so it does not belong in a stack meant to `cdk deploy`
  cleanly and repeatably. Add it yourself, against your own address, if you
  want to see the confirmation flow.
- SNS itself has no hourly or monthly charge in a real AWS account - you pay
  per request/notification beyond a monthly free tier - see the pricing
  reference below. Re-check current pricing, as it can change over time.
- A topic can fan out to many subscriber types at once (SQS, Lambda, HTTPS,
  email, mobile push, ...) - this module shows exactly one (SQS) to keep the
  example self-contained.

## References

- [Amazon SNS - fanout to Amazon SQS queues](https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html)
- [Amazon SNS pricing](https://aws.amazon.com/sns/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_sns.Topic`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns/Topic.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_sns_subscriptions.SqsSubscription`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sns_subscriptions/SqsSubscription.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_sqs.Queue`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/Queue.html)
