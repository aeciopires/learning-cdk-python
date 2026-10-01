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
    - [List every resource with the AWS CLI](#list-every-resource-with-the-aws-cli)
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
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth TransitGatewayStack
uv run cdk diff TransitGatewayStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy TransitGatewayStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff TransitGatewayStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy TransitGatewayStack --profile <your-aws-cli-profile>
```

## Verify

```bash
pid() { aws cloudformation describe-stack-resource --stack-name TransitGatewayStack \
  --logical-resource-id "$1" --query StackResourceDetail.PhysicalResourceId --output text; }
aws ec2 describe-transit-gateways --transit-gateway-ids "$(pid TransitGateway)"
aws ec2 describe-transit-gateway-vpc-attachments \
  --filters "Name=transit-gateway-id,Values=$(pid TransitGateway)"
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id "$(pid TransitGatewayRouteTable)" \
  --filters "Name=type,Values=static"
```

The ids come from the stack itself (`describe-stack-resource`) rather than
a `Name`-tag filter: filtering by tag works on real AWS, but floci doesn't
keep EC2 tags, so a tag filter finds nothing there.

On floci (2.1.0) these find nothing: its CloudFormation records the
Transit Gateway resources without creating them - see
[`../../REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
Transit Gateway's resources visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)).

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
`make cdk-resources STACK=TransitGatewayStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=TransitGatewayStack
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::EC2::TransitGateway (TransitGateway)
aws ec2 describe-transit-gateways --transit-gateway-ids "$(pid TransitGateway)" --query "TransitGateways[].[TransitGatewayId,State]" --output table --region "$REGION"
# AWS::EC2::VPC (VpcAAD85CA4C)
aws ec2 describe-vpcs --vpc-ids "$(pid VpcAAD85CA4C)" --query "Vpcs[].[VpcId,CidrBlock,State]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcAisolatedSubnet1Subnet43D53A46)
aws ec2 describe-subnets --subnet-ids "$(pid VpcAisolatedSubnet1Subnet43D53A46)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcAisolatedSubnet1RouteTable1DF492C1)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcAisolatedSubnet1RouteTable1DF492C1)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::VPC (VpcB98A08B07)
aws ec2 describe-vpcs --vpc-ids "$(pid VpcB98A08B07)" --query "Vpcs[].[VpcId,CidrBlock,State]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcBisolatedSubnet1SubnetAF9FCA4D)
aws ec2 describe-subnets --subnet-ids "$(pid VpcBisolatedSubnet1SubnetAF9FCA4D)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcBisolatedSubnet1RouteTable5D649D35)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcBisolatedSubnet1RouteTable5D649D35)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::TransitGatewayVpcAttachment (VpcAAttachment)
aws ec2 describe-transit-gateway-vpc-attachments --transit-gateway-attachment-ids "$(pid VpcAAttachment)" --query "TransitGatewayVpcAttachments[].[TransitGatewayAttachmentId,VpcId,State]" --output table --region "$REGION"
# AWS::EC2::TransitGatewayVpcAttachment (VpcBAttachment)
aws ec2 describe-transit-gateway-vpc-attachments --transit-gateway-attachment-ids "$(pid VpcBAttachment)" --query "TransitGatewayVpcAttachments[].[TransitGatewayAttachmentId,VpcId,State]" --output table --region "$REGION"
# AWS::EC2::TransitGatewayRouteTable (TransitGatewayRouteTable)
aws ec2 describe-transit-gateway-route-tables --transit-gateway-route-table-ids "$(pid TransitGatewayRouteTable)" --query "TransitGatewayRouteTables[].[TransitGatewayRouteTableId,State]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::EC2::SubnetRouteTableAssociation VpcAisolatedSubnet1RouteTableAssociationB8B2B284 - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcBisolatedSubnet1RouteTableAssociationC6DEE4DC - shown by its route table
#   AWS::EC2::TransitGatewayRouteTableAssociation VpcAAssociation - shown by its transit gateway route table
#   AWS::EC2::TransitGatewayRouteTableAssociation VpcBAssociation - shown by its transit gateway route table
#   AWS::EC2::TransitGatewayRoute RouteToVpcB - shown by its transit gateway route table
#   AWS::EC2::TransitGatewayRoute RouteToVpcA - shown by its transit gateway route table
```

**On floci** (2.1.0), CloudFormation records `AWS::EC2::TransitGateway`, `AWS::EC2::TransitGatewayRouteTable`, `AWS::EC2::TransitGatewayVpcAttachment` without creating it, so those commands find nothing there - they work on real AWS. See [`REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy TransitGatewayStack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
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
