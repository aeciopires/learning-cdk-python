<!-- TOC -->

- [Module 35 - Cognito (user pool and app client)](#module-35---cognito-user-pool-and-app-client)
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

# Module 35 - Cognito (user pool and app client)

## Overview

Amazon Cognito handles sign-up and sign-in for an application's end users,
without you having to build and secure your own password database. This
module creates one **user pool** - a managed directory of users, with a
password policy and email verification - and one **app client**, the
credentials a browser or mobile app uses to talk to that user pool.

**User pools vs. identity pools.** Cognito actually has two related but
separate features, and this module only covers the first:

| | User pool | Identity pool |
|---|---|---|
| Question it answers | "Who is this person?" (authentication) | "What AWS resources can this already-identified person touch?" (authorization) |
| What you get back | A JSON Web Token (ID/access/refresh tokens) | Temporary AWS credentials (via STS, see [`../02_sts`](../02_sts/README.md)) |
| Typical use | Sign-up/sign-in forms, "log in with email" | Letting a signed-in mobile app upload directly to an S3 bucket |
| This module | Creates one | Does not create one |

A real application often uses both: a user pool to authenticate the user,
then an identity pool to exchange that user pool's token for temporary AWS
credentials. See [Reference 3](#references) for identity pools.

## What you will learn

- How `aws_cognito.UserPool` turns a handful of properties into a managed
  user directory, including a password policy and account-recovery method.
- The difference between a user pool (authentication) and an identity pool
  (temporary AWS credentials) - see the table above.
- Why an app client has no client secret when the caller is a browser or
  mobile app that cannot keep one confidential (`generate_secret=False`).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon Cognito | `aws_cdk.aws_cognito.UserPool` | L2 |
| Amazon Cognito | `aws_cdk.aws_cognito.UserPoolClient` | L2 |
| Amazon Cognito | `aws_cdk.aws_cognito.SignInAliases`, `StandardAttributes`, `StandardAttribute`, `PasswordPolicy` | L2 (props) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_35_cognito.py`](../../tests/unit/test_35_cognito.py))
check that: exactly one user pool and one app client are created, the user
pool's password policy requires a 12-character minimum and all four
character classes, the app client generates no client secret (the "public
client" point this module teaches), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the user pool - as `UserPoolTags`, a map rather than the `Tags` list most
other resources use. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_35_cognito.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth CognitoStack
uv run cdk deploy CognitoStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created. A Cognito user
pool has no hourly charge; pricing is per **monthly active user (MAU)**
once you go over a free tier - see [Reference 5](#references) before
deploying against a real account with real users.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy CognitoStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws cognito-idp list-user-pools --max-results 10
aws cognito-idp list-user-pool-clients --user-pool-id <user-pool-id-from-above>

# Create a test user directly (bypasses the self-sign-up email flow, useful
# for a quick smoke test against floci):
aws cognito-idp admin-create-user \
  --user-pool-id <user-pool-id> \
  --username test@example.com \
  --user-attributes Name=email,Value=test@example.com Name=email_verified,Value=true
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
user pool's resources visually.

## Clean up

```bash
uv run cdk destroy CognitoStack
```

## Notes and cautions

- `removal_policy=cdk.RemovalPolicy.DESTROY` is deliberate: the L2
  `UserPool` construct's own default is `RETAIN` (so a production user pool
  - and every user's account - is never deleted by an accidental
  `cdk destroy`). This module overrides that default so the stack cleans
  up completely for learning purposes; do not copy this override into a
  production stack without thinking about it first.
- The password policy here (`min_length=12`, all four character classes
  required) is stricter than Cognito's own default - see
  [Reference 4](#references) for the full range of options and defaults.
- This module does not configure a hosted UI, an identity provider (Google,
  SAML, ...), or MFA - each is a real, separate piece of configuration a
  production user pool usually adds; this module only shows the minimum
  pool + client pairing.

## References

- [Amazon Cognito - What Is Amazon Cognito?](https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html)
- [Amazon Cognito - User pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html)
- [Amazon Cognito - Identity pools](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html)
- [Amazon Cognito - Password policy](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-policies.html)
- [Amazon Cognito pricing](https://aws.amazon.com/cognito/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_cognito.UserPool`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cognito/UserPool.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_cognito.UserPoolClient`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cognito/UserPoolClient.html)
