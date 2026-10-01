<!-- TOC -->

- [Module 30 - ALB (Application Load Balancer)](#module-30---alb-application-load-balancer)
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

# Module 30 - ALB (Application Load Balancer)

## Overview

An Application Load Balancer (ALB) distributes incoming HTTP/HTTPS traffic
across a set of backend targets (EC2 instances, containers, IP addresses),
operating at layer 7 (the application layer) - it can read the HTTP request
itself (path, headers, host) to make routing decisions. This module creates
its own small VPC, an internet-facing ALB, a listener on port 80, and a
target group with no targets registered yet - the load-balancing layer on
its own, deliberately without a backend behind it.

## What you will learn

- How `elbv2.ApplicationLoadBalancer`, `elbv2.ApplicationListener`, and
  `elbv2.ApplicationTargetGroup` (three separate CDK L2 constructs) fit
  together: the load balancer owns listeners, a listener forwards to one or
  more target groups, and a target group holds the actual backend targets.
- Why an **empty** target group (`target_type=elbv2.TargetType.IP`, no
  targets registered) is valid CDK/CloudFormation - it synthesizes and
  deploys cleanly, it just has nothing healthy to route to yet.
- Where a real deployment would register targets (see
  [Notes and cautions](#notes-and-cautions)).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Elastic Load Balancing | `aws_cdk.aws_elasticloadbalancingv2.ApplicationLoadBalancer` | L2 |
| Elastic Load Balancing | `aws_cdk.aws_elasticloadbalancingv2.ApplicationListener` | L2 |
| Elastic Load Balancing | `aws_cdk.aws_elasticloadbalancingv2.ApplicationTargetGroup` | L2 |
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_30_alb.py`](../../tests/unit/test_30_alb.py))
check that: exactly one load balancer is created with `Type: application`
and `Scheme: internet-facing` (this module's whole point vs. module 31's
NLB), exactly one empty target group exists on port 80/HTTP with
`TargetType: ip`, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the load balancer. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_30_alb.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth AlbStack
uv run cdk deploy AlbStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost -
**an ALB bills hourly from the moment it exists**, whether or not it has
healthy targets - see [Notes and cautions](#notes-and-cautions).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy AlbStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws elbv2 describe-load-balancers --names learning-cdk-python-dev-alb-web
aws elbv2 describe-listeners --load-balancer-arn <load-balancer-arn-from-above>
aws elbv2 describe-target-groups --names learning-cdk-python-dev-tg-web
aws elbv2 describe-target-health --target-group-arn <target-group-arn-from-above>
```

`describe-target-health` returns an empty list - there are no registered
targets yet, which is expected for this module (see Overview).

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
load balancer, listener, and target group visually.

## Clean up

```bash
uv run cdk destroy AlbStack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
```

## Notes and cautions

- **A real deployment registers targets from another module against this
  target group** - typically module 13 (EC2), via `target_group.add_target
  (instance)`, or module 15 (ECS), via the service construct's
  `target_group=` prop. This module stays intentionally backend-free and
  independent of every other module, matching this repository's rule that
  no module references another module's stack.
- **Cost on real AWS**: an Application Load Balancer bills hourly plus a
  Load Balancer Capacity Unit (LCU) charge based on traffic, starting the
  moment it exists - see the pricing reference below and re-check current
  numbers before deploying to a real account for any length of time.
- This module's VPC uses `nat_gateways=0` and public subnets only, the same
  reasoning as `modules/03_vpc` - see that module's README for why.

## References

- [Elastic Load Balancing - What is an Application Load Balancer?](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html)
- [Elastic Load Balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticloadbalancingv2.ApplicationLoadBalancer`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationLoadBalancer.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticloadbalancingv2.ApplicationListener`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationListener.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_elasticloadbalancingv2.ApplicationTargetGroup`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2/ApplicationTargetGroup.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
