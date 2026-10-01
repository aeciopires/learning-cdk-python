<!-- TOC -->

- [Module 07 - VPC Peering (a direct connection between two VPCs)](#module-07---vpc-peering-a-direct-connection-between-two-vpcs)
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

# Module 07 - VPC Peering (a direct connection between two VPCs)

## Overview

**VPC peering** connects exactly two VPCs directly, so resources in either
one can talk to the other using private IP addresses, as if they were on
the same network. This module creates two small, non-overlapping VPCs and a
peering connection between them, with a route on each side pointing at the
other VPC's CIDR block.

## What you will learn

- **VPC peering has no L2 construct in aws-cdk-lib.** `ec2.CfnVPCPeeringConnection`
  (L1, a 1:1 mapping to `AWS::EC2::VPCPeeringConnection`) is what this
  module uses.
- **Peering is not transitive.** If a third VPC were peered to `vpc_b`, it
  still could not reach `vpc_a` through `vpc_b` - each pair that needs to
  talk needs its own, separate peering connection. This is the main
  practical difference from a Transit Gateway (module 06), which *is* a hub
  all attached VPCs can route through.
- **Peering is symmetric at the routing layer**: both VPCs need their own
  route pointing at the peering connection and the other VPC's CIDR - one
  route only lets traffic flow one way.
- **Non-overlapping CIDR blocks are mandatory.** Two VPCs with overlapping
  IP ranges cannot be peered at all - this module's two VPCs use
  `10.30.0.0/16` and `10.40.0.0/16` specifically so they never overlap.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Amazon VPC (peering connection) | `aws_cdk.aws_ec2.CfnVPCPeeringConnection` | L1 - no L2 exists; [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnVPCPeeringConnection.html) |
| Amazon VPC (route) | `aws_cdk.aws_ec2.CfnRoute` | L1 - [API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_07_vpc_peering.py`](../../tests/unit/test_07_vpc_peering.py))
check that: exactly one peering connection is created and it links both
VPCs (its `VpcId`/`PeerVpcId` reference the two VPCs, in either order), each
VPC gets a route to the *other* VPC's CIDR, both routes explicitly
`DependsOn` the peering connection (the pattern to copy for cross-account or
cross-region peering, where acceptance is not automatic - see
[What you will learn](#what-you-will-learn)), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the peering connection. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_07_vpc_peering.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth VpcPeeringStack
uv run cdk diff VpcPeeringStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy VpcPeeringStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff VpcPeeringStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy VpcPeeringStack --profile <your-aws-cli-profile>
```

## Verify

```bash
pid() { aws cloudformation describe-stack-resource --stack-name VpcPeeringStack \
  --logical-resource-id "$1" --query StackResourceDetail.PhysicalResourceId --output text; }
aws ec2 describe-vpc-peering-connections --vpc-peering-connection-ids "$(pid PeeringConnection)"
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$(pid VpcAAD85CA4C)" \
  --query "RouteTables[].Routes"
```

The ids come from the stack itself (`describe-stack-resource`) rather than
a `Name`-tag filter: filtering by tag works on real AWS, but floci doesn't
keep EC2 tags, so a tag filter finds nothing there.

On floci (2.1.0) the peering connection isn't created (its CloudFormation
records it without creating it), so the first command finds nothing - see
[`../../REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse both
VPCs' resources visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)).

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
`make cdk-resources STACK=VpcPeeringStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=VpcPeeringStack
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

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
# AWS::EC2::VPCPeeringConnection (PeeringConnection)
aws ec2 describe-vpc-peering-connections --vpc-peering-connection-ids "$(pid PeeringConnection)" --query "VpcPeeringConnections[].[VpcPeeringConnectionId,Status.Code]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::EC2::SubnetRouteTableAssociation VpcAisolatedSubnet1RouteTableAssociationB8B2B284 - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcBisolatedSubnet1RouteTableAssociationC6DEE4DC - shown by its route table
#   AWS::EC2::Route VpcARouteToVpcB - shown by its route table
#   AWS::EC2::Route VpcBRouteToVpcA - shown by its route table
```

**On floci** (2.1.0), CloudFormation records `AWS::EC2::VPCPeeringConnection` without creating it, so those commands find nothing there - they work on real AWS. See [`REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy VpcPeeringStack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
```

## Notes and cautions

- A VPC peering connection has no hourly cost by itself, on floci or on
  real AWS - you only pay standard data transfer rates for traffic that
  crosses it.
- Both VPCs here are `PRIVATE_ISOLATED`-only (no NAT Gateway, no Internet
  Gateway) - this module is about the peering connection itself, and
  staying isolated keeps it free to run.
- This module creates a same-account, same-region peering connection, which
  is accepted automatically. A cross-account or cross-region peering
  connection requires the *peer* account to explicitly accept it
  (`aws ec2 accept-vpc-peering-connection`) before routes to it will work -
  see the peering guide in [References](#references).

## References

- [Amazon VPC Peering - What is VPC peering?](https://docs.aws.amazon.com/vpc/latest/peering/what-is-vpc-peering.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnVPCPeeringConnection`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnVPCPeeringConnection.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.CfnRoute`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/CfnRoute.html)
- [AWS CDK API Reference (Python) - `aws_cdk.CfnResource` (`add_resource_dependency`)](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk/CfnResource.html)
