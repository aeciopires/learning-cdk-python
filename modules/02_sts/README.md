<!-- TOC -->

- [Module 02 - STS (AssumeRole)](#module-02---sts-assumerole)
  - [Overview](#overview)
  - [What you will learn](#what-you-will-learn)
  - [AWS services and CDK constructs used](#aws-services-and-cdk-constructs-used)
  - [Prerequisites](#prerequisites)
  - [Tests](#tests)
  - [Deploy with floci (local, free)](#deploy-with-floci-local-free)
  - [Deploy to real AWS (optional)](#deploy-to-real-aws-optional)
  - [Verify](#verify)
    - [List every resource with the AWS CLI](#list-every-resource-with-the-aws-cli)
  - [Clean up](#clean-up)
  - [Notes and cautions](#notes-and-cautions)
  - [References](#references)

<!-- TOC -->

# Module 02 - STS (AssumeRole)

## Overview

AWS STS (Security Token Service) hands out **temporary** credentials (an
access key, a secret key, and a session token, typically valid for minutes
to hours) when a principal calls `sts:AssumeRole` against a role's ARN. This
module creates the IAM role side of that exchange - the same `iam.Role`
construct as module 01, but with its trust policy written to allow
`sts:AssumeRole` from a principal (rather than from an AWS *service*, as in
module 01) - and its README shows how to actually call `AssumeRole` against
it with the AWS CLI.

## What you will learn

- **STS has no CloudFormation/CDK resource.** There is nothing named
  `Cfn::STS::*` or an `aws_cdk.aws_sts` module - assuming a role is an API
  call your *code* makes at runtime (via the AWS CLI or an SDK like
  `boto3`), not infrastructure you provision. What this module provisions
  is the role that call targets.
- **`iam.AccountPrincipal`** - a trust-policy principal meaning "this AWS
  account", as opposed to module 01's `iam.ServicePrincipal` ("this AWS
  service").
- **The `ExternalId` condition** - a shared secret the caller must also
  supply, required by AWS for third-party cross-account role assumption
  specifically to prevent the ["confused deputy" problem](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html)
  (see [References](#references)). This module uses it even for a
  same-account example, since it's the pattern worth practicing.
- **`aws sts assume-role`** and **`aws sts get-caller-identity`** - the two
  STS CLI commands you'll use constantly once you work with roles day to
  day.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| IAM | `aws_cdk.aws_iam.Role` | L2 |
| IAM | `aws_cdk.aws_iam.AccountPrincipal` | L2 (helper) |
| IAM | `aws_cdk.aws_iam.PolicyStatement` | L2 (props) |
| STS | *(none - see "What you will learn" above)* | - |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_02_sts.py`](../../tests/unit/test_02_sts.py))
check that: exactly one role is created, its trust policy requires the
`sts:ExternalId` condition (the "confused deputy" protection this module
exists to teach - see [Notes and cautions](#notes-and-cautions)), it grants
only the one trivial `s3:ListAllMyBuckets` action and nothing else, and
every mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
section 7) is present. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_02_sts.py -v
```

## Deploy with floci (local, free)

```bash
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth StsStack
uv run cdk diff StsStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy StsStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff StsStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy StsStack --profile <your-aws-cli-profile>
```

## Verify

```bash
# Who am I, before assuming anything:
aws sts get-caller-identity

# Assume the role this stack created (replace <account-id> with your own,
# or floci's default test account, 000000000000):
aws sts assume-role \
  --role-arn "arn:aws:iam::<account-id>:role/learning-cdk-python-dev-role-assume-demo" \
  --role-session-name "learning-cdk-python-demo" \
  --external-id "learning-cdk-python-dev-external-id"

# The command above prints temporary AccessKeyId/SecretAccessKey/SessionToken.
# Export them, then confirm you're now "someone else":
export AWS_ACCESS_KEY_ID=<from-the-output-above>
export AWS_SECRET_ACCESS_KEY=<from-the-output-above>
export AWS_SESSION_TOKEN=<from-the-output-above>
aws sts get-caller-identity   # now shows the assumed role's ARN, not your original identity

# Restore your original credentials afterward, e.g. by re-sourcing .env
# (see REQUIREMENTS.md section 0) or unsetting the three variables above.
```

<!-- BEGIN resource-commands (generated by scripts/resource_commands.py) -->
### List every resource with the AWS CLI

Every resource this stack creates, one `aws` command each, parametrized
by environment (`ENV`), region (`REGION`) and - where a command builds an
ARN - account (`ACCOUNT`): set them to match your deployment, with your
`.env` loaded (floci) or your AWS profile active (real AWS). A resource
without a name of its own is looked up through the stack by its *logical
id* (`pid <LogicalId>`), which is the same in every environment. This block
is generated from the stack's template by
[`scripts/resource_commands.py`](../../scripts/resource_commands.py) - see
[`../../REQUIREMENTS.md`, section 5.10](../../REQUIREMENTS.md#510---listing-every-resource-a-stack-created);
`make cdk-resources STACK=StsStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=StsStack
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::IAM::Role (AssumableRole68D2A207)
aws iam get-role --role-name "${PRODUCT}-${ENV}-role-assume-demo" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::IAM::Policy AssumableRoleDefaultPolicy2A55320F - shown by its IAM role
```
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy StsStack
```

## Notes and cautions

- Temporary credentials from `sts:AssumeRole` expire (this module sets
  `max_session_duration` to 1 hour) - if a later command suddenly fails
  with an authentication error, you likely need to assume the role again or
  restore your original credentials.
- IAM roles have no hourly cost, on floci or on real AWS.

## References

- [STS - AssumeRole API reference](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html)
- [IAM - Temporary security credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html)
- [IAM - The confused deputy problem and how ExternalId solves it](https://docs.aws.amazon.com/IAM/latest/UserGuide/confused-deputy.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_iam.Role`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_iam.AccountPrincipal`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/AccountPrincipal.html)
