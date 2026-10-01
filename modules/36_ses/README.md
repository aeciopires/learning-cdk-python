<!-- TOC -->

- [Module 36 - SES (email identity)](#module-36---ses-email-identity)
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

# Module 36 - SES (email identity)

## Overview

Amazon SES (Simple Email Service) sends and receives email at scale. Before
SES will send mail *from* (or, for a domain, receive mail *for*) an address,
that address or domain must be **verified** - proven to AWS that you
control it. This module creates one email identity: a single address,
verified by clicking a confirmation link SES emails to it.

## What you will learn

- How `aws_ses.EmailIdentity` turns a single property (the identity) into a
  verification request.
- The difference between verifying a single **email address**
  (`ses.Identity.email(...)`, what this module uses) and verifying a whole
  **domain** (`ses.Identity.domain(...)`, or `ses.Identity.public_hosted_zone(...)`
  when the domain's DNS is already a Route 53 hosted zone in this account -
  see [`../33_route53`](../33_route53/README.md)) - a domain identity lets
  you send from any address `@that-domain` without verifying each one.
- Why a brand-new AWS account cannot actually send production email the
  moment this stack deploys (the SES sandbox - see
  [Notes and cautions](#notes-and-cautions)).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon SES | `aws_cdk.aws_ses.EmailIdentity` | L2 |
| Amazon SES | `aws_cdk.aws_ses.Identity` | L2 (helper) |

`ses.EmailIdentity` is a stable L2 construct in the current `aws-cdk-lib`
(confirmed against the [AWS CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ses/EmailIdentity.html)
and the `aws-cdk-lib` v2.271.0 source while writing this module) - the L1
`ses.CfnEmailIdentity` exists too, but is not needed here.

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_36_ses.py`](../../tests/unit/test_36_ses.py))
check that: exactly one email identity is created, it verifies the expected
`noreply@example.com` sender address, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present. No
Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_36_ses.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth SesStack
uv run cdk deploy SesStack --require-approval never --method=direct
```

floci accepts the verification request immediately (there is no real inbox
to click a confirmation link in) - see [Notes and cautions](#notes-and-cautions).

## Deploy to real AWS (optional)

Only do this if you understand the resources being created. An SES email
identity has no hourly cost; SES itself charges per email sent past a small
free tier - see [Reference 6](#references). **Before deploying**, edit
`sender_address` in `stack.py` to an address you actually control - AWS
will email a confirmation link to it, and the identity stays unverified
until you click it.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy SesStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ses get-identity-verification-attributes --identities noreply@example.com
aws ses list-identities
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
identity's status visually.

## Clean up

```bash
uv run cdk destroy SesStack
```

## Notes and cautions

- **Every new AWS account starts in the SES sandbox.** In the sandbox you
  can only send email *to* verified addresses (and, for some regions, the
  [Amazon SES mailbox simulator](https://docs.aws.amazon.com/ses/latest/dg/send-an-email-from-console.html#send-email-simulator)),
  and your daily sending quota and rate are both very low. This module's
  stack only *verifies an identity* - it does not, and cannot, request
  production access for you; that is a manual step. See
  [Reference 3](#references) for exactly what the sandbox restricts and
  [Reference 4](#references) for how to request production access when
  you are ready to send to arbitrary recipients.
- This module verifies an **address**, the simplest possible identity. A
  real production setup almost always verifies a **domain** instead (see
  [What you will learn](#what-you-will-learn)), because it covers every
  address at that domain and supports DKIM signing without re-verifying
  each sender.
- floci does not enforce the real sandbox restrictions or actually deliver
  mail - it emulates the SES API surface (identity state, verification
  attributes) so this module's CDK code and AWS CLI calls behave the same
  as against a real account, without sending anything.

## References

- [Amazon SES - What Is Amazon SES?](https://docs.aws.amazon.com/ses/latest/dg/Welcome.html)
- [Amazon SES - Verifying an identity](https://docs.aws.amazon.com/ses/latest/dg/verify-addresses-and-domains.html)
- [Amazon SES - The SES sandbox](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html#dg-production-access-sandbox)
- [Amazon SES - Request production access](https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html)
- [Amazon SES - DKIM authentication](https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim.html)
- [Amazon SES pricing](https://aws.amazon.com/ses/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ses.EmailIdentity`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ses/EmailIdentity.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ses.Identity`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ses/Identity.html)
