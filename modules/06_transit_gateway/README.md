<!-- TOC -->

- [Module 06 - Transit Gateway (a routing hub for many VPCs)](#module-06---transit-gateway-a-routing-hub-for-many-vpcs)
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

# Module 06 - Transit Gateway (a routing hub for many VPCs)

## Overview

A **Transit Gateway** is a regional network hub: instead of connecting VPCs
to each other pairwise (see module 07, VPC Peering), each VPC connects once
to the Transit Gateway, and the gateway routes traffic between them. This
module creates one Transit Gateway and attaches two small VPCs to it, with
an explicit transit gateway route table controlling how traffic flows
between them.

## What you will learn

- **Transit Gateway has no L2 construct in aws-cdk-lib.** Every construct
  this module uses is L1 (`Cfn*`) - a 1:1 mapping to the
  `AWS::EC2::TransitGateway*` CloudFormation resource types. This is one of
  the services CLAUDE.md's guardrail calls out explicitly: prefer L2 where
  one exists, use L1 and say so where it does not.
- **A VPC attachment (`ec2.CfnTransitGatewayVpcAttachment`)** is what
  connects one VPC to the Transit Gateway - you need one per VPC, each
  naming the subnets (one per Availability Zone you want reachable) that
  attachment uses.
- **Why this module creates its own transit gateway route table instead of
  using the "default" one.** AWS creates a default route table for every
  Transit Gateway automatically, but `ec2.CfnTransitGateway` has no
  attribute exposing that default table's id - it is not a documented
  `Fn::GetAtt` on the underlying CloudFormation resource either (see the
  `AWS::EC2::TransitGateway` reference in [References](#references), under
  "Return values": only `Id` and `EncryptionSupportState` are exposed).
  Rather than guess at an undocumented way to reach it, this module creates
  an explicit `ec2.CfnTransitGatewayRouteTable`, associates both
  attachments with it (`ec2.CfnTransitGatewayRouteTableAssociation`), and
  adds routes to it by hand (`ec2.CfnTransitGatewayRoute`) - the
  documented, honest way to control this from CDK.
- **Each VPC reaches the other through the *other's* attachment** - a
  Transit Gateway route's `transit_gateway_attachment_id` names the
  attachment traffic should exit through, not the attachment it arrived on.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Transit Gateway | `aws_cdk.aws_ec2.CfnTransitGateway` | L1 - no L2 exists; [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnTransitGateway.html) |
| Transit Gateway | `aws_cdk.aws_ec2.CfnTransitGatewayVpcAttachment` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnTransitGatewayVpcAttachment.html) |
| Transit Gateway | `aws_cdk.aws_ec2.CfnTransitGatewayRouteTable` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnTransitGatewayRouteTable.html) |
| Transit Gateway | `aws_cdk.aws_ec2.CfnTransitGatewayRouteTableAssociation` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnTransitGatewayRouteTableAssociation.html) |
| Transit Gateway | `aws_cdk.aws_ec2.CfnTransitGatewayRoute` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnTransitGatewayRoute.html) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_06_transit_gateway.py`](../../tests/unit/test_06_transit_gateway.py))
check that: exactly one Transit Gateway and two VPC attachments are
created, exactly one explicit `CfnTransitGatewayRouteTable` exists with two
associations (this module's whole point - the CDK construct exposes no
attribute for AWS's auto-created default route table, so `stack.py` creates
its own instead, see [What you will learn](#what-you-will-learn)), each VPC
gets a route toward the *other* VPC's CIDR through the *other* VPC's
attachment, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the Transit Gateway. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_06_transit_gateway.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth TransitGatewayStack
uv run cdk deploy TransitGatewayStack --require-approval never
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy TransitGatewayStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ec2 describe-transit-gateways --filters "Name=tag:Name,Values=*tgw-hub"
aws ec2 describe-transit-gateway-vpc-attachments
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id <route-table-id-from-above> \
  --filters "Name=type,Values=static"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
Transit Gateway's resources visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)).

## Clean up

```bash
uv run cdk destroy TransitGatewayStack
```

## Notes and cautions

- **A Transit Gateway has its own hourly charge per attachment on real
  AWS**, separate from any NAT Gateway or data transfer cost - check
  current pricing (see [References](#references)) before deploying this
  module to a real account, and destroy the stack when you are done.
- Both VPCs in this module are `PRIVATE_ISOLATED`-only (no NAT Gateway, no
  Internet Gateway) - this module is about the Transit Gateway's own
  routing between the two VPCs, not about internet access, and staying
  isolated keeps the VPCs themselves free.
- A real-world Transit Gateway usually connects many more than two VPCs,
  and often a VPN or Direct Connect attachment as well - two VPCs is the
  minimum needed to demonstrate routing between them.

## References

- [AWS Transit Gateway - What is a transit gateway?](https://docs.aws.amazon.com/vpc/latest/tgw/what-is-transit-gateway.html)
- [AWS Transit Gateway pricing](https://aws.amazon.com/transit-gateway/pricing/)
- [AWS CloudFormation - `AWS::EC2::TransitGateway`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgateway.html)
- [AWS CloudFormation - `AWS::EC2::TransitGatewayVpcAttachment`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgatewayvpcattachment.html)
- [AWS CloudFormation - `AWS::EC2::TransitGatewayRouteTable`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgatewayroutetable.html)
- [AWS CloudFormation - `AWS::EC2::TransitGatewayRouteTableAssociation`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgatewayroutetableassociation.html)
- [AWS CloudFormation - `AWS::EC2::TransitGatewayRoute`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-transitgatewayroute.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnTransitGateway`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnTransitGateway.html)
