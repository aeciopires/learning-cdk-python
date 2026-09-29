<!-- TOC -->

- [Module 08 - KMS (a customer-managed encryption key)](#module-08---kms-a-customer-managed-encryption-key)
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

# Module 08 - KMS (a customer-managed encryption key)

## Overview

AWS KMS (Key Management Service) lets you create and control cryptographic
keys used to encrypt data across almost every other AWS service (S3
buckets, Secrets Manager secrets, EBS volumes, ...). This module creates one
**customer-managed key** (a key you own and control, as opposed to an
AWS-managed key like the default `alias/aws/s3`), with automatic key
rotation enabled and a friendly alias.

## What you will learn

- **Customer-managed vs. AWS-managed keys.** A customer-managed key (what
  this module creates) gives you control over its policy, rotation, and
  deletion - an AWS-managed key (like the one S3 uses by default when you
  just tick "enable encryption") does not.
- **Key aliases.** `kms.Key`'s `alias` property takes the alias name
  *without* the `alias/` prefix (e.g. `"learning-cdk-python-dev-kms-app"`) -
  the construct adds the prefix for you. Aliases exist because a key's own
  identifier (its key ID or ARN) is not human-friendly; you refer to a key
  by its alias in most day-to-day use.
- **Automatic key rotation.** `enable_key_rotation=True` asks AWS to
  generate new cryptographic material for this key automatically (AWS's
  default rotation period, unless you also set `rotation_period` - see the
  [Key construct reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_kms/Key.html)
  in [References](#references) for the current default), without you having
  to re-encrypt existing data or change which key ID your application uses.
- **`removal_policy=RemovalPolicy.DESTROY`** - and why, on real AWS, this
  does *not* mean the key disappears the instant you run `cdk destroy`. See
  [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| KMS | `aws_cdk.aws_kms.Key` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_08_kms.py`](../../tests/unit/test_08_kms.py))
check that: exactly one KMS key and one alias are created, the key has
`EnableKeyRotation: true` (this module's whole point - automatic yearly
rotation), the alias name has the `alias/` prefix CDK adds automatically,
and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the key. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_08_kms.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth KmsStack
uv run cdk deploy KmsStack --require-approval never
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy KmsStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws kms list-aliases --query "Aliases[?AliasName=='alias/learning-cdk-python-dev-kms-app']"
aws kms describe-key --key-id "alias/learning-cdk-python-dev-kms-app"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
key visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)).

## Clean up

```bash
uv run cdk destroy KmsStack
```

## Notes and cautions

- **On real AWS, deleting a KMS key is never instant, `RemovalPolicy.DESTROY`
  or not.** Scheduling a key for deletion starts a mandatory waiting period
  (7-30 days, 30 by default) during which the key still exists and can be
  cancelled - `RemovalPolicy.DESTROY` only controls whether CloudFormation
  *attempts* deletion at all when the stack is destroyed (the alternative,
  `RemovalPolicy.RETAIN`, would leave the key behind even after
  `cdk destroy`); it does not skip the waiting period itself. See
  [Deleting AWS KMS keys](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html)
  in [References](#references) for the full mechanics and how to cancel a
  pending deletion if you change your mind.
- floci emulates this differently (keys are typically removed immediately
  on `cdk destroy`, with no pending-deletion window), which is part of why
  `cdk destroy` in the instructions above looks instantaneous locally but
  will not be on a real account.
- A customer-managed KMS key has a small monthly cost on real AWS (plus a
  per-API-call cost for use) - check current pricing before leaving one
  running in a real account for long.

## References

- [AWS KMS - Key Management Service concepts](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html)
- [AWS KMS - Deleting AWS KMS keys](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_kms.Key`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_kms/Key.html)
