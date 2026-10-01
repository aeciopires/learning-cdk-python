<!-- TOC -->

- [Module 43 - Resource Groups & Tagging](#module-43---resource-groups--tagging)
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

# Module 43 - Resource Groups & Tagging

## Overview

AWS Resource Groups lets you view and manage a set of resources that share
something in common - usually a tag - as one logical group in the console,
instead of hunting for them one service at a time. This module creates one
**tag-based group**: every resource in this account/region tagged
`product=<config.product>` (the same mandatory `product` tag every module
in this repository already applies - see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md#7-tagging-policy)).

## What you will learn

- How `resourcegroups.CfnGroup` with a `TAG_FILTERS_1_0` resource query
  builds a *dynamic* group - its membership is computed live by AWS
  whenever you view it, not a fixed list this stack maintains.
- How this repository's own mandatory tagging policy (`shared/tagging.py`)
  becomes directly queryable once you have a group like this one.
- The difference between this module (a persistent, named, console-visible
  group) and the separate, read-only **Resource Groups Tagging API** - see
  [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS Resource Groups | `aws_cdk.aws_resourcegroups.CfnGroup` | **L1** (`Cfn*`) |

There is **no L2 construct for Resource Groups** in the current stable
`aws-cdk-lib` (confirmed against the
[AWS CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_resourcegroups/CfnGroup.html)
while writing this module) - this module uses the L1 `CfnGroup`, a 1:1
mapping to the `AWS::ResourceGroups::Group` CloudFormation resource. Every
nested property class (`ResourceQueryProperty`, `QueryProperty`,
`TagFilterProperty`) was verified against that resource's own
CloudFormation documentation - see [Reference 2](#references).

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_43_resource_group_tagging.py`](../../tests/unit/test_43_resource_group_tagging.py))
check that: exactly one resource group is created, its tag-based query
filters on the `product` key/value this repository's other modules already
tag with (this module's whole point), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present. No
Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_43_resource_group_tagging.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth ResourceGroupTaggingStack
uv run cdk diff ResourceGroupTaggingStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy ResourceGroupTaggingStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created. AWS Resource
Groups itself has no dedicated charge - it is a free organizing/management
feature over resources you already pay for individually - see
[Reference 1](#references).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff ResourceGroupTaggingStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy ResourceGroupTaggingStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws resource-groups list-groups
aws resource-groups list-group-resources --group-name <group-name-from-above>
```

The `boto3`/AWS CLI examples below (the separate Resource Groups Tagging
API) also work once you have deployed a few other modules in this
repository - every one of them tags its resources with the same `product`
value:

```python
# Documented example - the Resource Groups Tagging API is read-only, so
# there is nothing to deploy for it (see "Notes and cautions" below).
import boto3

client = boto3.client("resourcegroupstaggingapi")
response = client.get_resources(
    TagFilters=[{"Key": "product", "Values": ["learning-cdk-python"]}]
)
for resource in response["ResourceTagMappingList"]:
    print(resource["ResourceARN"], resource["Tags"])
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
group visually.

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
`make cdk-resources STACK=ResourceGroupTaggingStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=ResourceGroupTaggingStack
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::ResourceGroups::Group (ResourceGroup)
aws resource-groups get-group --group-name "${PRODUCT}-${ENV}-resource-group-by-product" --query "Group.[Name,GroupArn]" --output table --region "$REGION"
```

**On floci** (2.1.0), CloudFormation records `AWS::ResourceGroups::Group` without creating it, so those commands find nothing there - they work on real AWS. See [`REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy ResourceGroupTaggingStack
```

## Notes and cautions

- **This module and the Resource Groups Tagging API are two different
  things that complement each other.** `resourcegroups.CfnGroup` (this
  module) creates a persistent, named object visible in the AWS Resource
  Groups console, with a query AWS re-evaluates each time you open it. The
  **Resource Groups Tagging API** (`boto3.client("resourcegroupstaggingapi")`,
  shown above) is a separate, read-only/query-only API for *ad hoc*
  tag-based lookups (`get_resources`, `get_tag_keys`, `get_tag_values`) -
  it has **no CloudFormation/CDK resource of its own** to create, since
  there is nothing to provision: every call is a live query, not a managed
  object - see [Reference 4](#references).
- `resource_type_filters=["AWS::AllSupported"]` means "every resource type
  Resource Groups can query", not a hand-maintained list - as you deploy
  more of this repository's modules, they appear in this group
  automatically (as long as they carry the `product` tag, which every
  module does via `apply_standard_tags`).

## References

- [AWS Resource Groups - What is AWS Resource Groups?](https://docs.aws.amazon.com/ARG/latest/userguide/welcome.html)
- [AWS::ResourceGroups::Group - AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-resourcegroups-group.html)
- [AWS Resource Groups - Build queries and groups](https://docs.aws.amazon.com/ARG/latest/userguide/gettingstarted-query.html)
- [AWS Resource Groups Tagging API Reference](https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/Welcome.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_resourcegroups.CfnGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_resourcegroups/CfnGroup.html)
