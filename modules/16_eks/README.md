<!-- TOC -->

- [Module 16 - EKS (control plane only, no worker nodes)](#module-16---eks-control-plane-only-no-worker-nodes)
  - [Overview](#overview)
  - [What you will learn](#what-you-will-learn)
  - [AWS services and CDK constructs used](#aws-services-and-cdk-constructs-used)
  - [Prerequisites](#prerequisites)
  - [Tests](#tests)
  - [Deploy with floci (local, free)](#deploy-with-floci-local-free)
  - [Deploy to real AWS (optional, and costly)](#deploy-to-real-aws-optional-and-costly)
  - [Verify](#verify)
    - [List every resource with the AWS CLI](#list-every-resource-with-the-aws-cli)
  - [Clean up](#clean-up)
  - [Notes and cautions](#notes-and-cautions)
  - [References](#references)

<!-- TOC -->

# Module 16 - EKS (control plane only, no worker nodes)

> **This is the most complex and most expensive module in the whole
> learning path.** Read [Notes and cautions](#notes-and-cautions) before
> deploying this to a real AWS account. **Strongly prefer floci for this
> module** - the "Deploy to real AWS" section is optional and costs real
> money the moment the cluster exists.

## Overview

Amazon EKS (Elastic Kubernetes Service) is AWS's managed Kubernetes control
plane - the API server, `etcd`, and scheduler that a Kubernetes cluster
needs, run and patched by AWS instead of by you. This module creates
**only that control plane**, with `default_capacity=0` (no managed node
group, so no worker EC2 instances and no pods can actually be scheduled) -
enough to see the CDK `eks.Cluster` construct and the cluster itself exist,
without the cost or complexity of a full worker-node setup.

## What you will learn

- How `aws_eks.Cluster` provisions an EKS control plane, and what
  `default_capacity=0` deliberately leaves out (a managed node group -
  worker EC2 instances that would let pods actually run).
- Why EKS needs a VPC spanning **at least 2 Availability Zones**
  (`max_azs=2` below), unlike modules 13 (EC2) and 15 (ECS), which only
  needed one.
- Why `kubectl_layer` is a required argument on the current, stable
  `eks.Cluster` construct, and what package it comes from - see
  [Notes and cautions](#notes-and-cautions).
- The cost shape of EKS: **the control plane itself bills hourly, whether
  or not any node or pod ever exists** - the opposite of most services in
  this path, where an empty resource is free.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon EKS | `aws_cdk.aws_eks.Cluster` | L2 |
| Amazon EKS | `aws_cdk.aws_eks.KubernetesVersion` | L2 (helper) |
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| (support) | `aws_cdk.lambda_layer_kubectl_v36.KubectlV36Layer` (separate PyPI package - see [Notes and cautions](#notes-and-cautions)) | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- floci runs EKS as an actual local Docker backend (not a lightweight mock) -
  see [`../../REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations) -
  so this module needs more RAM/CPU and takes noticeably longer to become
  healthy than most other modules in this path. `cdk synth`/`cdk deploy` for
  this stack are also slower than average because of the nested
  CloudFormation stacks EKS's kubectl handler needs (see the
  `.template.json` output - this stack synthesizes two nested stacks).

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_16_eks.py`](../../tests/unit/test_16_eks.py))
check that: exactly one cluster is created (as a
`Custom::AWSCDK-EKS-Cluster` resource - EKS's L2 construct provisions the
control plane through a CDK custom resource, not a native CloudFormation
resource type), it runs Kubernetes `1.36` with no managed node group
(`default_capacity=0` - this module's whole point, confirmed by asserting
zero `AWS::AutoScaling::AutoScalingGroup` resources exist), the VPC spans
2 Availability Zones (EKS's minimum requirement), and every mandatory tag
(see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is
present on the cluster's control-plane security group - the custom
resource itself has no CloudFormation `Tags` property to assert on. No
Docker, floci, or AWS credentials needed (and, unlike `cdk synth`/`cdk
deploy` for this module, these tests run in well under a second):

```bash
# From the repository root:
uv run pytest tests/unit/test_16_eks.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth EksStack
uv run cdk diff EksStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy EksStack --require-approval never --method=direct
```

## Deploy to real AWS (optional, and costly)

> **Every Amazon EKS cluster costs money the moment it exists** - the
> control plane is billed **per hour**, currently **$0.10/hour** per
> cluster (**~$73/month** if left running for a full month), **regardless
> of whether it has any worker nodes, pods, or traffic at all** - see
> [Amazon EKS pricing](https://aws.amazon.com/eks/pricing/) for the current
> rate, which can change. This module adds no worker nodes
> (`default_capacity=0`), so it avoids the *additional* EC2/EBS cost a real
> node group would add - but the control plane charge alone still applies.
> **Destroy this stack as soon as you're done** (see
> [Clean up](#clean-up)); do not leave it running "just in case".

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff EksStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy EksStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws eks describe-cluster --name learning-cdk-python-dev-eks-main
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
cluster visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) for
how the UI is enabled in this repository's `docker-compose.yml`).

On a real AWS account, with the AWS CLI's `eks` command and `kubectl`
installed, you can point `kubectl` at the (nodeless) cluster:

```bash
aws eks update-kubeconfig --name learning-cdk-python-dev-eks-main
kubectl get nodes   # expected: empty - default_capacity=0 means no nodes
```

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
`make cdk-resources STACK=EksStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=EksStack
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
# AWS::Lambda::LayerVersion (KubectlLayer600207B5)
aws lambda list-layer-versions --layer-name "$(pid KubectlLayer600207B5 | cut -d: -f7)" --query "LayerVersions[].[LayerVersionArn,Version]" --output table --region "$REGION"
# AWS::IAM::Role (ClusterKubectlHandlerRole94549F93)
aws iam get-role --role-name "$(pid ClusterKubectlHandlerRole94549F93)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::IAM::Role (ClusterRoleFA261979)
aws iam get-role --role-name "$(pid ClusterRoleFA261979)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (ClusterControlPlaneSecurityGroupD274242C)
aws ec2 describe-security-groups --group-ids "$(pid ClusterControlPlaneSecurityGroupD274242C)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::IAM::Role (ClusterCreationRole360249B6)
aws iam get-role --role-name "$(pid ClusterCreationRole360249B6)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# Custom::AWSCDK-EKS-Cluster (Cluster9EE0221C)
aws eks describe-cluster --name "$(pid Cluster9EE0221C)" --query "cluster.[name,status,version]" --output table --region "$REGION"
# AWS::SSM::Parameter (ClusterKubectlReadyBarrier200052AF)
aws ssm get-parameter --name "$(pid ClusterKubectlReadyBarrier200052AF)" --query "Parameter.[Name,Type]" --output table --region "$REGION"
# AWS::CloudFormation::Stack (awscdkawseksClusterResourceProviderNestedStackawscdkawseksClusterResourceProviderNestedStackResource9827C454)
aws cloudformation describe-stacks --stack-name "$(pid awscdkawseksClusterResourceProviderNestedStackawscdkawseksClusterResourceProviderNestedStackResource9827C454)" --query "Stacks[].[StackName,StackStatus]" --output table --region "$REGION"
# AWS::CloudFormation::Stack (awscdkawseksKubectlProviderNestedStackawscdkawseksKubectlProviderNestedStackResourceA7AEBA6B)
aws cloudformation describe-stacks --stack-name "$(pid awscdkawseksKubectlProviderNestedStackawscdkawseksKubectlProviderNestedStackResourceA7AEBA6B)" --query "Stacks[].[StackName,StackStatus]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet1RouteTableAssociation4E83B6E4 - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet1DefaultRouteB88F9E93 - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet2RouteTableAssociationCCE257FF - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet2DefaultRoute732F0BEB - shown by its route table
#   AWS::EC2::VPCGatewayAttachment VpcVPCGWBF912B6E - shown by its internet gateway
#   AWS::IAM::Policy ClusterKubectlHandlerRoleDefaultPolicyE44083DD - shown by its IAM role
#   AWS::IAM::Policy ClusterCreationRoleDefaultPolicyE8BDFC7B - shown by its IAM role
```
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy EksStack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
```

Real-account cleanup can take several minutes - EKS control plane deletion
is not instant. Confirm with `aws eks describe-cluster` (or the console)
that the cluster is actually gone, not just that `cdk destroy` returned.

## Notes and cautions

- **Cost - read this before deploying to a real account.** See the boxed
  warning at the top of [Deploy to real AWS](#deploy-to-real-aws-optional-and-costly).
  This is the only module in this path with a genuinely ongoing,
  non-trivial hourly charge that starts the instant the resource is
  created - not once you add traffic or storage, unlike S3 or ECR.
- **The `kubectl_layer` dependency.** Inspecting the installed
  `aws_cdk.aws_eks.Cluster.__init__` signature directly
  (`aws-cdk-lib==2.271.0`) shows `kubectl_layer` as a **required** keyword
  argument, with no default. `aws-cdk-lib`'s stable package no longer
  bundles a default kubectl/Helm Lambda layer for the cluster's internal
  "apply Kubernetes manifests" handler; the current, still-stable
  (non-alpha) mechanism is one small, separate package **per Kubernetes
  minor version**, published by the same AWS CDK team under
  [`cdklabs/awscdk-asset-kubectl`](https://github.com/cdklabs/awscdk-asset-kubectl).
  This module uses `aws-cdk.lambda-layer-kubectl-v36`, matching
  `KubernetesVersion.V1_36` below, and it was added to this repository's
  `pyproject.toml` with `uv add aws-cdk.lambda-layer-kubectl-v36` for this
  reason - **this is the one module in the whole path that needs a
  dependency beyond `aws-cdk-lib` + `constructs`**. It is a regular,
  versioned PyPI package (not an `-alpha` package), so it does not violate
  this repository's rule against alpha/experimental CDK packages (see
  [`../../CLAUDE.md`, section 4](../../CLAUDE.md#4-do-not-invent-things-the-core-guardrail)).
- **No worker nodes, on purpose.** `default_capacity=0` means `kubectl get
  nodes` returns nothing (see [Verify](#verify)) - this module only proves
  the control plane exists and is reachable. A real, workload-ready EKS
  cluster needs a managed node group or Fargate profile added on top,
  which is out of scope for a beginner module focused on the control plane
  itself.
- `nat_gateways=0` and a `PUBLIC`-only, 2-AZ VPC keep this module's
  networking free of NAT Gateway cost - see module 03 (VPC) and module 05
  (NAT Gateway). A production EKS VPC normally also has private subnets
  with a NAT Gateway for worker nodes; this module has no nodes to put
  there, so it skips that entirely.
- **Kubernetes version.** `KubernetesVersion.V1_36` was Amazon EKS's current
  standard-support Kubernetes version at the time this module was written -
  re-check [Amazon EKS Kubernetes version support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-standard.html)
  before relying on this, and keep the `kubectl_layer` package version
  (`-v36`) matched to whatever `KubernetesVersion` constant you use.

## References

- [Amazon EKS - What is Amazon EKS?](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html)
- [Amazon EKS pricing](https://aws.amazon.com/eks/pricing/)
- [Amazon EKS Kubernetes version support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-standard.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_eks.Cluster`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_eks/Cluster.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_eks.KubernetesVersion`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_eks/KubernetesVersion.html)
- [`aws-cdk.lambda-layer-kubectl-v36` on PyPI](https://pypi.org/project/aws-cdk.lambda-layer-kubectl-v36/)
- [`cdklabs/awscdk-asset-kubectl` on GitHub](https://github.com/cdklabs/awscdk-asset-kubectl)
