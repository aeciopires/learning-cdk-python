<!-- TOC -->

- [Module 31 - NLB (Network Load Balancer)](#module-31---nlb-network-load-balancer)
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

# Module 31 - NLB (Network Load Balancer)

## Overview

A Network Load Balancer (NLB) distributes incoming TCP/UDP/TLS traffic
across a set of backend targets, operating at layer 4 (the transport layer)
- it forwards raw connections rather than reading HTTP requests, which gives
it very high throughput and ultra-low latency. This module has the same
shape as module 30 (ALB): its own small VPC, an internet-facing NLB, a
listener on port 80 (protocol TCP), and a target group with no targets
registered yet.

## What you will learn

- How `elbv2.NetworkLoadBalancer`, `elbv2.NetworkListener`, and
  `elbv2.NetworkTargetGroup` fit together - the same three-part shape as the
  ALB in module 30, at a different layer.
- **ALB vs. NLB, for a beginner deciding which one to use:**

  | | Application Load Balancer (module 30) | Network Load Balancer (this module) |
  |---|---|---|
  | OSI layer | 7 (application) | 4 (transport) |
  | Protocols | HTTP, HTTPS, gRPC | TCP, UDP, TLS |
  | Understands | URL paths, headers, host names | Raw connections only |
  | Typical use | Web apps, microservices, path/host-based routing | Extreme low latency, static IPs, non-HTTP protocols (databases, gaming, IoT) |
  | Client IP preservation | Via `X-Forwarded-For` header | Native (source IP preserved) |

  Pick an ALB by default for HTTP(S) web traffic; pick an NLB when you need
  raw TCP/UDP, a static IP per Availability Zone, or the lowest possible
  latency.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Elastic Load Balancing | `aws_cdk.aws_elasticloadbalancingv2.NetworkLoadBalancer` | L2 |
| Elastic Load Balancing | `aws_cdk.aws_elasticloadbalancingv2.NetworkListener` | L2 |
| Elastic Load Balancing | `aws_cdk.aws_elasticloadbalancingv2.NetworkTargetGroup` | L2 |
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_31_nlb.py`](../../tests/unit/test_31_nlb.py))
check that: exactly one load balancer is created with `Type: network` and
`Scheme: internet-facing` (this module's whole point vs. module 30's ALB),
exactly one empty target group exists on port 80/TCP with `TargetType: ip`,
and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the load balancer. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_31_nlb.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth NlbStack
uv run cdk diff NlbStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy NlbStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost -
**an NLB bills hourly from the moment it exists**, the same as an ALB - see
[Notes and cautions](#notes-and-cautions).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff NlbStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy NlbStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws elbv2 describe-load-balancers --names learning-cdk-python-dev-nlb-tcp
aws elbv2 describe-listeners --load-balancer-arn <load-balancer-arn-from-above>
aws elbv2 describe-target-groups --names learning-cdk-python-dev-tg-tcp
aws elbv2 describe-target-health --target-group-arn <target-group-arn-from-above>
```

`describe-target-health` returns an empty list - there are no registered
targets yet, which is expected for this module (see Overview).

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
load balancer, listener, and target group visually.

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
`make cdk-resources STACK=NlbStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=NlbStack
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::EC2::VPC (Vpc8378EB38)
aws ec2 describe-vpcs --vpc-ids "$(pid Vpc8378EB38)" --query "Vpcs[].[VpcId,CidrBlock,State]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet1Subnet2BB74ED7)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet1Subnet2BB74ED7)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet1RouteTable15C15F8E)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet1RouteTable15C15F8E)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet2SubnetE34B022A)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet2SubnetE34B022A)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet2RouteTableC5A6DF77)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet2RouteTableC5A6DF77)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::InternetGateway (VpcIGWD7BA715C)
aws ec2 describe-internet-gateways --internet-gateway-ids "$(pid VpcIGWD7BA715C)" --query "InternetGateways[].[InternetGatewayId,Attachments[0].VpcId]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::LoadBalancer (NlbBCDB97FE)
aws elbv2 describe-load-balancers --load-balancer-arns "$(pid NlbBCDB97FE)" --query "LoadBalancers[].[LoadBalancerName,Type,State.Code]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::TargetGroup (TargetGroup3D7CD9B8)
aws elbv2 describe-target-groups --target-group-arns "$(pid TargetGroup3D7CD9B8)" --query "TargetGroups[].[TargetGroupName,Port,TargetType]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::Listener (Listener828B0E81)
aws elbv2 describe-listeners --listener-arns "$(pid Listener828B0E81)" --query "Listeners[].[Port,Protocol]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet1RouteTableAssociation4E83B6E4 - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet1DefaultRouteB88F9E93 - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet2RouteTableAssociationCCE257FF - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet2DefaultRoute732F0BEB - shown by its route table
#   AWS::EC2::VPCGatewayAttachment VpcVPCGWBF912B6E - shown by its internet gateway
```
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy NlbStack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
```

## Notes and cautions

- **A real deployment registers targets from another module against this
  target group** - the same idea as module 30 (ALB): module 13 (EC2) or
  module 15 (ECS) would register their instances/tasks here. This module
  stays intentionally backend-free and independent of every other module.
- **Cost on real AWS**: a Network Load Balancer bills hourly plus an NLB
  Capacity Unit (NLCU) charge based on traffic, starting the moment it
  exists - see the pricing reference below and re-check current numbers
  before deploying to a real account for any length of time.
- This module's VPC uses `nat_gateways=0` and public subnets only, the same
  reasoning as `modules/03_vpc` - see that module's README for why.

## References

- [Elastic Load Balancing - What is a Network Load Balancer?](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html)
- [Elastic Load Balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticloadbalancingv2.NetworkLoadBalancer`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/NetworkLoadBalancer.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticloadbalancingv2.NetworkListener`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/NetworkListener.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticloadbalancingv2.NetworkTargetGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/NetworkTargetGroup.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
