<!-- TOC -->

- [Module 15 - ECS (Fargate cluster, task definition, service)](#module-15---ecs-fargate-cluster-task-definition-service)
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

# Module 15 - ECS (Fargate cluster, task definition, service)

## Overview

Amazon ECS (Elastic Container Service) is AWS's container orchestrator; AWS
Fargate is the serverless compute mode for ECS - you describe a task (one or
more containers, CPU/memory) and AWS runs it without you managing any EC2
instances. This module creates a small ECS cluster, a Fargate task
definition with one `nginx` container, and a Fargate service that keeps one
copy of that task running, reachable on a public IP.

## What you will learn

- How `aws_ecs.Cluster`, `aws_ecs.FargateTaskDefinition`, and
  `aws_ecs.FargateService` fit together: a cluster is a logical grouping, a
  task definition is a blueprint (like a `docker-compose.yml` for one or
  more containers), and a service keeps a desired number of copies of that
  blueprint running.
- `ecs.ContainerImage.from_registry(...)` - pulling a public image
  (`public.ecr.aws/nginx/nginx:latest`, from the
  [Amazon ECR Public Gallery](https://gallery.ecr.aws/nginx/nginx)) with no
  registry authentication needed.
- Why this module's task runs with `assign_public_ip=True` in a
  `PUBLIC`-only VPC instead of behind a NAT Gateway or a load balancer - see
  [Notes and cautions](#notes-and-cautions).
- Why this module does **not** use
  `aws_ecs_patterns.ApplicationLoadBalancedFargateService` even though it is
  the fastest way to get "ECS behind a load balancer" in real code - see
  [References](#references) for where that pattern belongs.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon ECS | `aws_cdk.aws_ecs.Cluster` | L2 |
| Amazon ECS | `aws_cdk.aws_ecs.FargateTaskDefinition` | L2 |
| Amazon ECS | `aws_cdk.aws_ecs.FargateService` | L2 |
| Amazon ECS | `aws_cdk.aws_ecs.ContainerImage` | L2 (helper) |
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- floci runs ECS/Fargate as an actual local Docker backend (not a
  lightweight mock) - see
  [`../../REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations) -
  so deploying this module needs somewhat more RAM/CPU and takes longer to
  become healthy than, say, module 12 (S3).

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_15_ecs.py`](../../tests/unit/test_15_ecs.py))
check that: exactly one cluster, one task definition, and one service are
created, the task definition requires `FARGATE` compatibility with
`awsvpc` networking, `cpu=256`/`memory_limit_mib=512`, and one container
running `public.ecr.aws/nginx/nginx:latest` on port 80 (this module's
whole point), the service runs with `LaunchType=FARGATE`,
`DesiredCount=1`, and `AssignPublicIp=ENABLED`, and every mandatory tag
(see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is
present on the cluster. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_15_ecs.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth EcsStack
uv run cdk deploy EcsStack --require-approval never
```

## Deploy to real AWS (optional)

**A running Fargate task bills for as long as it is running** (per-vCPU and
per-GB-memory, by the second, with a minimum billing duration) - see
[AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/). This
module's `cpu=256`/`memory_limit_mib=512` task is Fargate's smallest size,
but it still isn't free. Destroy the stack when you're done (see
[Clean up](#clean-up)) so it stops billing.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy EcsStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ecs describe-clusters --clusters learning-cdk-python-dev-ecs-cluster
aws ecs list-tasks --cluster learning-cdk-python-dev-ecs-cluster
aws ecs describe-tasks --cluster learning-cdk-python-dev-ecs-cluster --tasks <task-arn-from-above>
```

On a real AWS account, once the task is `RUNNING`, its public IP (from
`describe-tasks` -> the attached network interface) serves nginx's default
page on port 80. Or open the floci UI at `http://localhost:4566/_floci/ui`
and browse the cluster/service/tasks visually (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) for how the UI is enabled
in this repository's `docker-compose.yml`).

## Clean up

```bash
uv run cdk destroy EcsStack
```

## Notes and cautions

- **Cost**: see the explicit warning in
  [Deploy to real AWS](#deploy-to-real-aws-optional).
- **No load balancer, on purpose.** This module keeps the Fargate service
  itself in focus: the task gets a public IP directly
  (`assign_public_ip=True`) instead of sitting behind an Application Load
  Balancer, so there is no extra billed resource and no extra concept to
  learn before you've seen ECS/Fargate on its own. Module 30 (ALB) adds a
  load balancer in front of a service; the combined "cluster + service + ALB
  in one construct" shortcut,
  `aws_cdk.aws_ecs_patterns.ApplicationLoadBalancedFargateService`, is
  mentioned in References as the production-shortcut version of what
  modules 15 and 30 build by hand.
- `nat_gateways=0` and a `PUBLIC`-only VPC keep this module's networking
  free of NAT Gateway cost - see module 03 (VPC) and module 05 (NAT
  Gateway) for why a NAT Gateway bills hourly the moment it exists. A public
  IP directly on the task is what lets it reach the internet (to pull the
  nginx image) without one.
- `public.ecr.aws/nginx/nginx:latest` is a real, currently-pullable image on
  the [Amazon ECR Public Gallery](https://gallery.ecr.aws/nginx/nginx) that
  needs no registry login - re-check the gallery page before relying on the
  `latest` tag long-term, since any public registry's `latest` tag can move.

## References

- [Amazon ECS - What is Amazon ECS?](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html)
- [AWS Fargate - What is AWS Fargate?](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/what-is-fargate.html)
- [AWS Fargate pricing](https://aws.amazon.com/fargate/pricing/)
- [Amazon ECR Public Gallery - nginx](https://gallery.ecr.aws/nginx/nginx)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ecs.Cluster`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/Cluster.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ecs.FargateTaskDefinition`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/FargateTaskDefinition.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ecs.FargateService`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/FargateService.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ecs_patterns.ApplicationLoadBalancedFargateService`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs_patterns/ApplicationLoadBalancedFargateService.html) (production shortcut, not used here - see module 30)
