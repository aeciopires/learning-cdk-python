<!-- TOC -->

- [Module 26 - SQS (a queue with a dead-letter queue)](#module-26---sqs-a-queue-with-a-dead-letter-queue)
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

# Module 26 - SQS (a queue with a dead-letter queue)

## Overview

Amazon SQS (Simple Queue Service) is a fully managed message queue: one part
of your system (a "producer") sends small messages onto a queue, and another
part (a "consumer") reads and deletes them, usually at its own pace. This
decouples the two - the producer does not need the consumer to be online or
fast. This module creates one standard queue plus a second, smaller queue
used as its dead-letter queue (DLQ).

## What you will learn

- How `aws_sqs.Queue` (the CDK L2 construct) turns a handful of properties
  into a fully managed queue.
- What server-side encryption with SQS-managed keys
  (`sqs.QueueEncryption.SQS_MANAGED`) is, and why it is a good default (no
  KMS key to create, manage, or pay for).
- What a dead-letter queue (DLQ) is: a second queue that receives messages a
  consumer failed to process successfully after a set number of attempts,
  instead of those messages being retried forever or silently lost.
- How `sqs.DeadLetterQueue(max_receive_count=3, queue=dlq)`, passed as the
  main queue's `dead_letter_queue=` prop, is all the code needed to wire a
  redrive policy - no manual IAM or resource policy required.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon SQS | `aws_cdk.aws_sqs.Queue` | L2 |
| Amazon SQS | `aws_cdk.aws_sqs.DeadLetterQueue` | L2 (props) |
| Amazon SQS | `aws_cdk.aws_sqs.QueueEncryption` | L2 (enum) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_26_sqs.py`](../../tests/unit/test_26_sqs.py))
check that: exactly two queues are created (the main queue and its DLQ), the
main queue's redrive policy has `maxReceiveCount: 3` (this module's whole
point - a message is moved to the DLQ after 3 failed receive attempts), both
queues use SQS-managed encryption, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present. No
Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_26_sqs.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth SqsStack
uv run cdk deploy SqsStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(see [Notes and cautions](#notes-and-cautions) - SQS has no hourly charge).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy SqsStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws sqs get-queue-url --queue-name learning-cdk-python-dev-sqs-orders
aws sqs get-queue-url --queue-name learning-cdk-python-dev-sqs-orders-dlq

# Inspect the redrive policy CDK wired up on the main queue:
aws sqs get-queue-attributes \
  --queue-url <queue-url-from-above> \
  --attribute-names RedrivePolicy
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse both
queues visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) for how
the UI is enabled in this repository's `docker-compose.yml`).

## Clean up

```bash
uv run cdk destroy SqsStack
```

## Notes and cautions

- `max_receive_count=3` means a message is only moved to the DLQ after it
  has been received (and not deleted) 3 times - tune this per queue based on
  how transient you expect failures to be.
- SQS itself has no hourly or monthly charge in a real AWS account - you pay
  per request beyond a monthly free tier - see the pricing reference below.
  Re-check current pricing before relying on this number changing over time.
- A message stuck in the DLQ needs a human (or a separate redrive process)
  to inspect and decide what to do with it - CDK/CloudFormation does not
  retry DLQ messages automatically.

## References

- [Amazon SQS - dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)
- [Amazon SQS pricing](https://aws.amazon.com/sqs/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_sqs.Queue`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/Queue.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_sqs.DeadLetterQueue`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/DeadLetterQueue.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_sqs.QueueEncryption`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_sqs/QueueEncryption.html)
