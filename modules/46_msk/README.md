<!-- TOC -->

- [Module 46 - MSK (Managed Streaming for Apache Kafka)](#module-46---msk-managed-streaming-for-apache-kafka)
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

# Module 46 - MSK (Managed Streaming for Apache Kafka)

## Overview

Amazon MSK runs [Apache Kafka](https://kafka.apache.org) for you. Kafka is
a distributed, append-only log of events: *producers* write events to
*topics*, and any number of *consumers* read them back, each at its own
pace, for as long as the topic retains them. This module creates a small
provisioned MSK cluster - two `kafka.t3.small` brokers, one in each of two
Availability Zones - in its own dedicated VPC, with IAM authentication and
TLS encryption.

It's module 46 (added after the original 44), but it belongs with the
other messaging services - see Phase 7 in
[`../../docs/LEARNING-PATH.md`](../../docs/LEARNING-PATH.md). Compare it
with SQS (26), SNS (27), and Kinesis Data Streams (24), which solve
related problems differently.

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module to a real AWS account.** MSK brokers bill hourly the moment they
exist.

## What you will learn

- **Why this module uses an L1 (`Cfn*`) construct.** The stable
  `aws_cdk.aws_msk` module contains only `Cfn*` classes. An L2 `Cluster`
  exists only in the separate `aws-cdk.aws-msk-alpha` package, which this
  repository never uses (experimental APIs can change between releases) -
  see [Notes and cautions](#notes-and-cautions).
- **How nested L1 properties look in Python.** `CfnCluster` is configured
  with nested `...Property` classes (`BrokerNodeGroupInfoProperty`,
  `StorageInfoProperty`, `ClientAuthenticationProperty`, ...), which map
  1:1 onto the nested objects in the `AWS::MSK::Cluster` CloudFormation
  resource.
- **Brokers and Availability Zones.** Brokers are spread across the subnets
  in `ClientSubnets`, and the number of brokers must be a multiple of the
  number of subnets - two subnets in two AZs with one broker each is the
  smallest layout.
- **IAM authentication for Kafka.** Instead of Kafka usernames/passwords,
  clients sign in with their IAM identity (module 01), on port 9098.
- **Kafka vs. SQS vs. Kinesis**, at a glance:

  | | SQS (26) | Kinesis Data Streams (24) | MSK (46) |
  |---|---|---|---|
  | Model | queue - a message is deleted once processed | ordered log, read by many consumers | ordered log, read by many consumers |
  | You manage | nothing | shards (or on-demand capacity) | brokers, storage, Kafka version |
  | Client API | AWS SDK | AWS SDK / KCL | standard Apache Kafka clients |

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc`, `aws_cdk.aws_ec2.SecurityGroup` | L2 |
| Amazon MSK | `aws_cdk.aws_msk.CfnCluster` | L1 (`Cfn*` - no stable L2 exists) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- Modules 26 (SQS) and 24 (Kinesis) are useful background for comparing
  messaging models, but not required.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_46_msk.py`](../../tests/unit/test_46_msk.py))
check that: exactly one `AWS::MSK::Cluster` is created; it runs Kafka
`3.9.x` on two `kafka.t3.small` brokers spread over two subnets, with 10 GiB
of storage each; clients authenticate with IAM over TLS, and brokers
encrypt traffic between themselves; the security group opens only port
9098; and every mandatory tag is present. **One difference from every other
module's tag test:** `AWS::MSK::Cluster` stores `Tags` as a key/value
*map* (`{"environment": "dev", ...}`), not the usual list of
`{"Key": ..., "Value": ...}` pairs, so the test converts
`mandatory_tag_pairs()` into a map before comparing. CDK's `Tags.of()`
handles both shapes automatically. The tests run in under a second, with
no Docker, no floci, and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_46_msk.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth MskStack
uv run cdk deploy MskStack --require-approval never
```

**What floci creates here (checked while writing this module - re-check
with newer floci versions):** the deploy succeeds and the VPC and security
group are created, but floci's CloudFormation implementation records the
`AWS::MSK::Cluster` without starting brokers - `aws kafka list-clusters-v2`
returns an empty list afterwards. floci's MSK *API* does run a real
Kafka-compatible broker (via [Redpanda](https://www.redpanda.com)), so you
can try the service itself by calling it directly (see [Verify](#verify)).

## Deploy to real AWS (optional)

Only do this if you have read and understood
[Notes and cautions](#notes-and-cautions) - this module has a real,
ongoing hourly cost the moment it is deployed, and a provisioned MSK
cluster can take a while to create.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy MskStack --profile <your-aws-cli-profile>
```

## Verify

On real AWS:

```bash
aws kafka list-clusters-v2 --query "ClusterInfoList[].{Name:ClusterName,State:State,Type:ClusterType}"
# the IAM bootstrap brokers (port 9098) a Kafka client connects to:
aws kafka get-bootstrap-brokers --cluster-arn <cluster-arn-from-above> --query BootstrapBrokerStringSaslIam
```

On floci, check what CloudFormation recorded, then (optionally) create a
cluster through floci's MSK API to try the service itself - and delete it
afterwards:

```bash
aws cloudformation describe-stack-resources --stack-name MskStack \
  --query "StackResources[].[ResourceType,ResourceStatus]" --output table

SUBNETS=$(aws ec2 describe-subnets --query "Subnets[0:2].SubnetId" --output text | tr '\t' ',')
aws kafka create-cluster-v2 --cluster-name try-msk --provisioned \
  "{\"BrokerNodeGroupInfo\":{\"InstanceType\":\"kafka.t3.small\",\"ClientSubnets\":[\"${SUBNETS%%,*}\",\"${SUBNETS##*,}\"]},\"KafkaVersion\":\"3.9.x\",\"NumberOfBrokerNodes\":2}"
aws kafka list-clusters-v2 --query "ClusterInfoList[].[ClusterName,State,ClusterArn]"
aws kafka delete-cluster --cluster-arn <cluster-arn-from-above>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
resources visually.

## Clean up

```bash
uv run cdk destroy MskStack
```

## Notes and cautions

- **No stable CDK L2 construct exists for MSK.** `aws_cdk.aws_msk` provides
  only L1 (`Cfn*`) constructs; the L2 `Cluster` lives in
  `aws-cdk.aws-msk-alpha`, an experimental package this repository never
  uses (see [`../../CLAUDE.md`, section 4](../../CLAUDE.md#4-do-not-invent-things-the-core-guardrail)).
  This module therefore uses
  [`aws_cdk.aws_msk.CfnCluster`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_msk/CfnCluster.html).
- **Bills hourly on real AWS**: each broker is billed continuously from
  creation until `cdk destroy`, plus storage - two brokers here.
  `kafka.t3.small` is the smallest Standard broker size, which AWS
  describes as meant "for low-cost development". Check current rates for
  your region before deploying.
- **Kafka version `3.9.x`**: marked "Recommended" on the MSK supported
  versions page when this module was written. The `.x` form lets MSK apply
  Kafka patch releases without a version upgrade. Versions reach end of
  support on a published schedule - re-check that page before relying on
  this one.
- **Clients must use IAM and TLS**: IAM-authenticated clients connect on
  port 9098 (from inside AWS), and client-broker traffic is TLS only. With
  IAM access control, IAM policies - not Kafka ACLs - decide what each
  client may do; it works for Java and non-Java clients (Python, Go,
  JavaScript, .NET) - see
  [IAM access control](https://docs.aws.amazon.com/msk/latest/developerguide/iam-access-control.html)
  for how to set up a client.
- **Isolated subnets only**: the brokers live in `PRIVATE_ISOLATED`
  subnets, reachable only from inside this module's VPC - no public access.

## References

- [What is Amazon MSK?](https://docs.aws.amazon.com/msk/latest/developerguide/what-is-msk.html)
- [Amazon MSK - Supported Apache Kafka versions](https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html)
- [Amazon MSK - Broker sizes](https://docs.aws.amazon.com/msk/latest/developerguide/broker-instance-sizes.html)
- [Amazon MSK - Port information](https://docs.aws.amazon.com/msk/latest/developerguide/port-info.html)
- [Amazon MSK - IAM access control](https://docs.aws.amazon.com/msk/latest/developerguide/iam-access-control.html)
- [Amazon MSK pricing](https://aws.amazon.com/msk/pricing/)
- [AWS CloudFormation - `AWS::MSK::Cluster`](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-msk-cluster.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_msk.CfnCluster`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_msk/CfnCluster.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
- [floci - AWS services](https://floci.io/aws/)
