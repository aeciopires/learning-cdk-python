<!-- TOC -->

- [Module 01 - IAM (roles and policies)](#module-01---iam-roles-and-policies)
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

# Module 01 - IAM (roles and policies)

**This is the first module in the learning path.** If you haven't set up
this project yet, stop and follow
[`../../REQUIREMENTS.md`, section 0](../../REQUIREMENTS.md#0-zero-to-your-first-deploy-in-order)
first - it explains, in order, what CDK/floci/uv are and gets you to the
point where the commands below will actually work.

## Overview

IAM (Identity and Access Management) controls *who* (a person, an AWS
service, another AWS account) can do *what* (an action, like `s3:GetObject`)
on *which* resource. This module creates one **IAM role** - a set of
temporary permissions something can *assume*, rather than a permanent
identity with its own password/access keys - and one **policy** attached to
it, written to grant only the specific permissions needed (this is called
"least privilege").

Concretely: a role that the AWS Lambda *service* is allowed to assume (its
"trust policy"), with two things attached to it: an AWS-managed policy that
grants the minimum CloudWatch Logs permissions any Lambda function needs to
run, and a small custom policy that grants read-only access to one bucket's
objects - nothing else.

## What you will learn

- **Role vs. user vs. policy**, the three IAM building blocks: a role is
  *assumed*, temporarily, by a person or a service; a policy is a
  document of allowed (or denied) actions; a user is a permanent identity
  (this module deliberately does not create one - see
  [Notes and cautions](#notes-and-cautions)).
- **Trust policy vs. permissions policy.** `assumed_by=` controls *who can
  become* this role (the trust policy); the `iam.PolicyStatement` objects
  control *what the role can do once assumed* (the permissions policy).
  These are two different documents, often confused by beginners.
- **How to scope a policy to one resource**, using `Stack.format_arn(...)`
  to build an ARN instead of writing `"*"` (which would grant access to
  every bucket in the account).
- **Attaching an AWS-managed policy by name**
  (`iam.ManagedPolicy.from_aws_managed_policy_name(...)`) vs. writing your
  own (`iam.ManagedPolicy(...)` with `statements=[...]`).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| IAM | `aws_cdk.aws_iam.Role` | L2 |
| IAM | `aws_cdk.aws_iam.ManagedPolicy` | L2 |
| IAM | `aws_cdk.aws_iam.PolicyStatement` | L2 (props) |
| IAM | `aws_cdk.aws_iam.ServicePrincipal` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see
  [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

This is the first module with tests, so start with
[`../../docs/TESTING.md`](../../docs/TESTING.md) if you haven't yet - it
explains, from zero, what a CDK unit test is, how it works, and how to
write your own.

This module's tests
([`../../tests/unit/test_01_iam.py`](../../tests/unit/test_01_iam.py))
check that: exactly one role and one customer-managed policy are created,
the role's trust policy only allows `lambda.amazonaws.com` to assume it
(nothing else), the policy grants no `s3:Put*`/`s3:Delete*`/`s3:*` action
(this module's whole point - least privilege), and every mandatory tag
(see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is
present on the role. They run in well under a second, with no Docker, no
floci, and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_01_iam.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - make sure you've loaded .env (see REQUIREMENTS.md section 0)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth IamStack     # generates the CloudFormation template, creates nothing
uv run cdk deploy IamStack --require-approval never
```

The `cdk bootstrap` line is needed once per floci instance - the first
time on each computer, and again after deleting floci's data. Without it,
`cdk deploy` stops with `SsmParameterNotFound: SSM parameter
/cdk-bootstrap/hnb659fds/version not found ... Has the environment been
bootstrapped?` - see
[`../../REQUIREMENTS.md`, section 5.7](../../REQUIREMENTS.md#57---bootstrapping-the-cdk-once-per-floci-instance-or-aws-accountregion)
for why.

`cdk synth` is worth running on its own the first time: open
`cdk.out/IamStack.template.json` afterward and find the two IAM policy
documents in it - that's the same JSON IAM uses internally, generated from
the Python code you just read.

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy IamStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws iam get-role --role-name learning-cdk-python-dev-role-app-task
aws iam list-attached-role-policies --role-name learning-cdk-python-dev-role-app-task
```

Or open `http://localhost:4566/_floci/ui` and browse IAM's resources
visually.

## Clean up

```bash
uv run cdk destroy IamStack
```

## Notes and cautions

- **No `iam.User` in this module, on purpose.** AWS's own IAM best
  practices guide (see [References](#references)) recommends roles with
  temporary credentials over IAM users with long-lived access keys,
  wherever the caller can be a role - which is true for every AWS service
  (Lambda here) and, as module 02 shows, for a human using the AWS CLI too.
- IAM roles and policies have no hourly cost, on floci or on real AWS - this
  module is free to deploy and leave running.

## References

- [IAM - What is IAM?](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html)
- [IAM - IAM roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
- [IAM - Policies and permissions](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html)
- [IAM - Security best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_iam.Role`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_iam.PolicyStatement`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html)
