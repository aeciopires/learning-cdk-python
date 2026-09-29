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
uv run cdk synth NlbStack
uv run cdk deploy NlbStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost -
**an NLB bills hourly from the moment it exists**, the same as an ALB - see
[Notes and cautions](#notes-and-cautions).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
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

## Clean up

```bash
uv run cdk destroy NlbStack
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
