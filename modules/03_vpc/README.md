<!-- TOC -->

- [Module 03 - VPC (subnets, security groups, route tables)](#module-03---vpc-subnets-security-groups-route-tables)
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

# Module 03 - VPC (subnets, security groups, route tables)

## Overview

Amazon VPC (Virtual Private Cloud) is the networking foundation almost every
other module in this learning path builds on: a logically isolated section
of AWS where you control the IP range, subnets, route tables, and security
groups. This module creates one VPC across 2 Availability Zones, with a
public subnet and a private-isolated subnet in each AZ, plus one security
group.

## What you will learn

- How `aws_ec2.Vpc` (the CDK L2 construct) turns a handful of properties
  into a VPC, subnets, route tables, and an Internet Gateway.
- The difference between `PUBLIC`, `PRIVATE_WITH_EGRESS`, and
  `PRIVATE_ISOLATED` subnets (see [Reference 3](#references)).
- How a security group's ingress rule is expressed in code (`Peer` +
  `Port`), instead of the console's form fields.
- Where to find the route table CDK created for you, as a first step toward
  modules 04-07, which build Internet Gateway, NAT Gateway, Transit
  Gateway, and VPC Peering routes by hand.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Amazon VPC | `aws_cdk.aws_ec2.SubnetConfiguration` | L2 (props) |
| Amazon VPC | `aws_cdk.aws_ec2.SecurityGroup` | L2 |
| Amazon VPC | `aws_cdk.aws_ec2.Peer`, `aws_cdk.aws_ec2.Port` | L2 (helpers) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

New to automated testing, or to this repository's tests specifically? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) once, from the top - it
explains what a CDK unit test actually is, how `aws_cdk.assertions` works,
and how to write your own, assuming zero prior testing experience. It's
worth reading before your second module, not just this one.

This module's tests
([`../../tests/unit/test_03_vpc.py`](../../tests/unit/test_03_vpc.py))
check that: exactly one VPC and one security group are created, the VPC has
4 subnets (2 public, 2 private-isolated, across 2 AZs), the security group
only opens port 443 and only from inside the VPC's own CIDR, and every
mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section
7) is present. Unlike "Deploy with floci" below, these run in well under a
second, with no Docker, no floci, and no AWS credentials at all:

```bash
# From the repository root:
uv run pytest tests/unit/test_03_vpc.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth VpcStack
uv run cdk deploy VpcStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(a VPC, subnets, and a security group have no hourly cost by themselves -
see [Notes and cautions](#notes-and-cautions) for what *does* cost money in
the modules that build on this one).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy VpcStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=*vpc-main"
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<vpc-id-from-above>"
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=<vpc-id-from-above>"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
VPC's resources visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
for how the UI is enabled in this repository's `docker-compose.yml`).

## Clean up

```bash
uv run cdk destroy VpcStack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
```

## Notes and cautions

- `nat_gateways=0` is deliberate: a NAT Gateway bills hourly plus per-GB
  data processing the moment it exists, whether or not anything uses it -
  see module 05 (NAT Gateway) before enabling one against a real account.
- Deploying this module against real AWS (not floci) has no hourly cost by
  itself. Cost appears only once you add NAT Gateways, EC2 instances, load
  balancers, etc. in the modules that reference this VPC's pattern.

## References

- [Amazon VPC - What Is Amazon VPC?](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)
- [Amazon VPC - Route tables](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html)
- [Amazon VPC - Security groups](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.SecurityGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SecurityGroup.html)
- [AWS CDK Developer Guide - VPC and networking](https://docs.aws.amazon.com/cdk/v2/guide/aws_construct_lib.html)
