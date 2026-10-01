<!-- TOC -->

- [Module 10 - Systems Manager Parameter Store (a free-tier String parameter)](#module-10---systems-manager-parameter-store-a-free-tier-string-parameter)
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

# Module 10 - Systems Manager Parameter Store (a free-tier String parameter)

## Overview

AWS Systems Manager Parameter Store is a simple, hierarchical key-value
store for configuration data and secrets - a lighter-weight alternative to
Secrets Manager (module 09) for values that are not necessarily sensitive
(feature flags, non-secret configuration, ...). This module creates one
`Standard`-tier `String` parameter, the free option.

## What you will learn

- **`ssm.StringParameter`** - the L2 construct for a Parameter Store
  parameter, and `tier=ssm.ParameterTier.STANDARD` - the free tier (no
  per-parameter charge, up to 10,000 parameters per account/Region, 4 KB
  value limit).
- **Why this parameter is named with `/`, not `-`.** Parameter Store's own
  convention is a `/`-separated hierarchy
  (`/learning-cdk-python/dev/app/greeting`), which lets you list or grant
  access to a whole subtree at once (`/learning-cdk-python/dev/*`) - see the
  naming-requirements link in [References](#references). This is a
  deliberate exception to this repository's usual `-`-separated
  `resource_name()` convention (see
  [`../../REQUIREMENTS.md`, section 8](../../REQUIREMENTS.md#8-naming-policy)),
  not a policy violation: `config.product` and `config.environment` still
  come from `shared.config.AppConfig`, never hardcoded, only the separator
  and path structure differ.
- **Why this module does not create a `SecureString` parameter.** Neither
  the CDK `StringParameter` L2 construct nor the underlying
  `AWS::SSM::Parameter` CloudFormation resource supports *creating* one -
  see [Notes and cautions](#notes-and-cautions) for the exact wording from
  both sources and what your options are if you actually need one.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Systems Manager (Parameter Store) | `aws_cdk.aws_ssm.StringParameter` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_10_parameter_store.py`](../../tests/unit/test_10_parameter_store.py))
check that: exactly one parameter is created, it uses the free `Standard`
tier and the `String` type (this module's whole point - no Advanced-tier
charge), its name follows the `/`-hierarchy convention described in
[What you will learn](#what-you-will-learn), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present.
Note that `AWS::SSM::Parameter`'s `Tags` property is a plain `{key: value}`
map rather than the usual list of `{"Key": ..., "Value": ...}` pairs, so
this file's tag check adapts `mandatory_tag_pairs()` accordingly - see the
test file's comments. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_10_parameter_store.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth ParameterStoreStack
uv run cdk deploy ParameterStoreStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy ParameterStoreStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ssm get-parameter --name "/learning-cdk-python/dev/app/greeting"
aws ssm get-parameters-by-path --path "/learning-cdk-python/dev" --recursive
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
parameter visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)).

## Clean up

```bash
uv run cdk destroy ParameterStoreStack
```

## Notes and cautions

- **`SecureString` parameters cannot be created through CloudFormation (and
  therefore not through CDK).** The CDK `aws_cdk.aws_ssm` module's own
  documentation states: *"SecureString parameter cannot be created directly
  from a CDK application"*. The CloudFormation `AWS::SSM::Parameter`
  reference is equally direct: *"Parameters of type SecureString are not
  supported by AWS CloudFormation."* (see
  [References](#references) for both source pages). If you need to
  *reference* a `SecureString` parameter created another way (console, AWS
  CLI, or `boto3`), use
  `StringParameter.from_secure_string_parameter_attributes(...)` to import
  it - that imports an existing parameter, it does not provision a new one,
  so it is out of scope for this "creates a resource" module.
- A `Standard`-tier `String` parameter has no cost on real AWS (up to the
  10,000-parameter free-tier limit per account/Region) - this is one of the
  few modules with no cost caveat at all.

## References

- [AWS Systems Manager - About requirements and constraints for parameter names](https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-su-create.html#sysman-paramstore-su-create-cli)
- [AWS CloudFormation - `AWS::SSM::Parameter`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ssm-parameter.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ssm.StringParameter`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ssm/StringParameter.html)
