<!-- TOC -->

- [Module 04 - Internet Gateway (wiring one up by hand)](#module-04---internet-gateway-wiring-one-up-by-hand)
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

# Module 04 - Internet Gateway (wiring one up by hand)

## Overview

An **Internet Gateway** (IGW) is the component that lets traffic flow
between a VPC and the public internet. In module 03, `ec2.Vpc` created one
for you automatically the moment it saw a `PUBLIC` subnet in
`subnet_configuration` - you never saw the gateway, the attachment, or the
route it created. This module builds a VPC with **no** `PUBLIC` subnet at
all (only `PRIVATE_ISOLATED`, so `ec2.Vpc` has no reason to create an
Internet Gateway), then adds the same three resources by hand with L1
(`Cfn*`) constructs, one at a time, so you can see exactly what module 03's
`ec2.Vpc` was doing for you.

## What you will learn

- **The three pieces behind "public internet access"**: the gateway itself
  (`ec2.CfnInternetGateway`), the attachment that connects it to a specific
  VPC (`ec2.CfnVPCGatewayAttachment` - a gateway is a standalone resource
  until this exists), and the route in a subnet's route table that actually
  sends `0.0.0.0/0` traffic toward it (`ec2.CfnRoute`).
- **Why `ec2.Vpc`'s `PUBLIC` subnet type exists**: it is a shortcut for
  exactly this three-resource pattern, run once per VPC.
- **Explicit CloudFormation dependencies.** `CfnRoute`'s properties
  reference the route table and the gateway, but never the attachment -
  CloudFormation cannot infer "this route needs the attachment to exist
  first" from `Ref`/`Fn::GetAtt` alone here, so the code calls
  `route.add_resource_dependency(attachment)` to say so explicitly. This is
  the most important line in `stack.py` to read closely.
- **`add_resource_dependency` vs. the older `add_dependency`.** Both exist
  on `CfnResource` in aws-cdk-lib 2.271.0; `add_dependency` is documented as
  deprecated in favor of `add_resource_dependency`, which this module uses.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Amazon VPC (Internet Gateway) | `aws_cdk.aws_ec2.CfnInternetGateway` | L1 - no L2 exists for a standalone Internet Gateway; [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnInternetGateway.html) |
| Amazon VPC (gateway attachment) | `aws_cdk.aws_ec2.CfnVPCGatewayAttachment` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnVPCGatewayAttachment.html) |
| Amazon VPC (route) | `aws_cdk.aws_ec2.CfnRoute` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) if you haven't yet -
it explains, from zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_04_internet_gateway.py`](../../tests/unit/test_04_internet_gateway.py))
check that: exactly one Internet Gateway and one gateway attachment are
created, the subnet's default route (`0.0.0.0/0`) targets that Internet
Gateway, the route explicitly `DependsOn` the attachment (this module's
whole point - the dependency CloudFormation cannot infer on its own from
`Ref`/`Fn::GetAtt` alone, see [What you will learn](#what-you-will-learn)),
and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the Internet Gateway. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_04_internet_gateway.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth InternetGatewayStack
uv run cdk deploy InternetGatewayStack --require-approval never
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy InternetGatewayStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ec2 describe-internet-gateways --filters "Name=tag:Name,Values=*igw-main"
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<vpc-id>" \
  --query "RouteTables[].Routes"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
VPC's resources visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)).

## Clean up

```bash
uv run cdk destroy InternetGatewayStack
```

## Notes and cautions

- An Internet Gateway has no hourly cost by itself, on floci or on real AWS
  - you only pay for data transfer out to the internet through it, and for
    anything else in the VPC (EC2 instances, etc.) that actually uses it.
- This module's one subnet is named `"isolated"` in `subnet_configuration`
  but ends up with a `0.0.0.0/0` route to the internet by the end of the
  stack - that is deliberate, it is exactly the point being demonstrated
  (an `ec2.SubnetType.PRIVATE_ISOLATED` subnet is only "isolated" until
  something manually routes it to a gateway, same as this module does).
  Do not copy this pattern for a subnet that should stay actually isolated.

## References

- [Amazon VPC - Internet gateways](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnInternetGateway`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnInternetGateway.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnVPCGatewayAttachment`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnVPCGatewayAttachment.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnRoute`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html)
- [AWS CDK API Reference (Python) - `aws_cdk.CfnResource` (`add_resource_dependency`)](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/CfnResource.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
