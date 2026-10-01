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
    - [List every resource with the AWS CLI](#list-every-resource-with-the-aws-cli)
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
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth EcsStack
uv run cdk diff EcsStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy EcsStack --require-approval never --method=direct
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
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff EcsStack --profile <your-aws-cli-profile>   # review the changes first
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
`make cdk-resources STACK=EcsStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=EcsStack
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
# AWS::EC2::InternetGateway (VpcIGWD7BA715C)
aws ec2 describe-internet-gateways --internet-gateway-ids "$(pid VpcIGWD7BA715C)" --query "InternetGateways[].[InternetGatewayId,Attachments[0].VpcId]" --output table --region "$REGION"
# AWS::ECS::Cluster (ClusterEB0386A7)
aws ecs describe-clusters --clusters "${PRODUCT}-${ENV}-ecs-cluster" --query "clusters[].[clusterName,status]" --output table --region "$REGION"
# AWS::IAM::Role (AppTaskDefinitionTaskRole96BC2009)
aws iam get-role --role-name "$(pid AppTaskDefinitionTaskRole96BC2009)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::ECS::TaskDefinition (AppTaskDefinitionCBC902A9)
aws ecs describe-task-definition --task-definition "${PRODUCT}-${ENV}-ecs-app-task" --query "taskDefinition.[family,revision,status]" --output table --region "$REGION"
# AWS::ECS::Service (AppServiceA2F9036C)
aws ecs describe-services --cluster "${PRODUCT}-${ENV}-ecs-cluster" --services "${PRODUCT}-${ENV}-ecs-app-service" --query "services[].[serviceName,status,desiredCount]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AppServiceSecurityGroupCD648D82)
aws ec2 describe-security-groups --group-ids "$(pid AppServiceSecurityGroupCD648D82)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet1RouteTableAssociation4E83B6E4 - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet1DefaultRouteB88F9E93 - shown by its route table
#   AWS::EC2::VPCGatewayAttachment VpcVPCGWBF912B6E - shown by its internet gateway
```
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy EcsStack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
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
