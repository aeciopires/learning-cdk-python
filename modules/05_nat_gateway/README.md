<!-- TOC -->

- [Module 05 - NAT Gateway (outbound-only internet access)](#module-05---nat-gateway-outbound-only-internet-access)
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

# Module 05 - NAT Gateway (outbound-only internet access)

## Overview

A **NAT Gateway** ("Network Address Translation" gateway) lets resources in
a private subnet initiate outbound connections to the internet (to download
a package, call an external API, ...) without being reachable *from* the
internet - unlike the Internet Gateway from module 04, which allows both
directions. This module builds a VPC with a public and a private subnet
(like module 03), then wires up a NAT Gateway by hand with L1 (`Cfn*`)
constructs to show what `ec2.Vpc`'s `nat_gateways=N` shortcut does for you
in production code.

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module to a real AWS account** - a NAT Gateway is one of the few resources
in this early part of the learning path that bills by the hour.

## What you will learn

- **The three pieces of a NAT Gateway**: an Elastic IP address
  (`ec2.CfnEIP`, the public IP the gateway uses), the NAT Gateway itself
  (`ec2.CfnNatGateway`, placed in a *public* subnet and bound to that
  Elastic IP), and a route in a *private* subnet's route table pointing at
  it (`ec2.CfnRoute`).
- **Why the NAT Gateway sits in the public subnet, not the private one.**
  It needs its own route to the internet (via the Internet Gateway) to
  forward traffic for everything behind it.
- **No manual dependency needed here**, unlike module 04. `CfnNatGateway`
  references the Elastic IP directly (`allocation_id`), and `CfnRoute`
  references the NAT Gateway directly (`nat_gateway_id`) - CloudFormation
  infers both orderings automatically from those `Ref`/`Fn::GetAtt`
  references, because there is no separate "attachment" resource sitting
  outside that reference chain, unlike module 04's Internet Gateway
  attachment.
- **`ec2.Vpc(..., nat_gateways=N)`** - the idiomatic, one-line production
  alternative to everything this module builds by hand: pass `nat_gateways=2`
  to `ec2.Vpc` and it creates one NAT Gateway per Availability Zone (up to
  `N`), each with its own Elastic IP and route, automatically.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Amazon VPC (Elastic IP) | `aws_cdk.aws_ec2.CfnEIP` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnEIP.html) |
| Amazon VPC (NAT Gateway) | `aws_cdk.aws_ec2.CfnNatGateway` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnNatGateway.html) |
| Amazon VPC (route) | `aws_cdk.aws_ec2.CfnRoute` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_05_nat_gateway.py`](../../tests/unit/test_05_nat_gateway.py))
check that: exactly one NAT Gateway and one Elastic IP are created, the NAT
Gateway's `AllocationId` references that Elastic IP's allocation, the
private subnet's default route (`0.0.0.0/0`) has its `NatGatewayId` pointing
at the NAT Gateway (this module's whole point - outbound-only access via the
NAT Gateway, not a direct Internet Gateway route), and every mandatory tag
(see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present
on the NAT Gateway. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_05_nat_gateway.py -v
```

## Deploy with floci (local, free)

floci emulates NAT Gateways without any real hourly charge - this is the
one place in this module's instructions where "free" is unconditionally
true.

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth NatGatewayStack
uv run cdk deploy NatGatewayStack --require-approval never
```

## Deploy to real AWS (optional)

**Read [Notes and cautions](#notes-and-cautions) first - this creates a
resource that bills by the hour the moment it exists.**

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy NatGatewayStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ec2 describe-nat-gateways --filter "Name=tag:Name,Values=*nat-main"
aws ec2 describe-addresses --filters "Name=tag:Name,Values=*eip-nat"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
VPC's resources visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)).

## Clean up

```bash
uv run cdk destroy NatGatewayStack
```

On real AWS, confirm in the console (VPC > NAT Gateways) that it actually
reaches the `Deleted` state - deletion is not instant, and the associated
Elastic IP is not released until it does.

## Notes and cautions

- **A NAT Gateway bills hourly, plus per-GB data processing, on real AWS,
  from the moment it is created until it is deleted** - whether or not
  anything ever uses it. This is one of the costs called out in
  [`../../REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).
  Check current pricing before deploying this module to a real account (see
  [References](#references)) and destroy the stack as soon as you are done
  with it.
- The Elastic IP this module allocates also has its own (much smaller) cost
  on real AWS if it is ever left unassociated from a running resource -
  `cdk destroy` releases it along with everything else, so this only
  matters if a `cdk destroy` is interrupted partway through.
- For production code, prefer `ec2.Vpc(..., nat_gateways=N)` over building
  this by hand - see [What you will learn](#what-you-will-learn). This
  module's manual version exists purely to teach what that shortcut does.

## References

- [Amazon VPC - NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html)
- [Amazon VPC pricing (NAT Gateway hourly + data processing rates)](https://aws.amazon.com/vpc/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnEIP`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnEIP.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnNatGateway`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnNatGateway.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnRoute`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
