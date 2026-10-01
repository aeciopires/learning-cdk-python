<!-- TOC -->

- [Module 13 - EC2 (one instance, its own minimal VPC)](#module-13---ec2-one-instance-its-own-minimal-vpc)
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

# Module 13 - EC2 (one instance, its own minimal VPC)

## Overview

Amazon EC2 (Elastic Compute Cloud) is AWS's virtual machine service. This
module creates one small (`t3.micro`) EC2 instance running Amazon Linux
2023, inside its own minimal, single-Availability-Zone VPC, with a security
group that allows **no inbound traffic at all** and an IAM role that only
grants access via AWS Systems Manager Session Manager - not SSH.

## What you will learn

- How `aws_ec2.Instance` turns an instance type, a machine image, a VPC, a
  security group, and an IAM role into a running virtual machine.
- `ec2.InstanceType.of(InstanceClass, InstanceSize)` - how CDK expresses an
  instance type (e.g. `t3.micro`) as two enums instead of a raw string.
- `ec2.MachineImage.resolve_ssm_parameter_at_launch(...)` - always using
  the *current* Amazon Linux 2023 AMI for the deployment region, instead of
  a hardcoded, region-specific, eventually-stale AMI ID. The template holds
  `ImageId: resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64`
  (an AWS-maintained public SSM parameter), and EC2 resolves it at launch.
  The more common `latest_amazon_linux2023()` reads the same parameter
  through a CloudFormation *parameter* instead, which makes the CDK CLI
  redeploy the stack on every `cdk deploy` - on floci, launching a
  duplicate instance each time (see
  [`../../REQUIREMENTS.md`, section 5.8](../../REQUIREMENTS.md#58---re-running-cdk-deploy-on-floci-without-duplicating-resources)).
- Why this module's security group has zero ingress rules, and how AWS
  Systems Manager Session Manager replaces SSH for reaching an instance -
  see [Notes and cautions](#notes-and-cautions).
- Why this module builds its own tiny VPC instead of reusing module 03's
  pattern as-is: every module in this path is self-contained (see
  [`../../CLAUDE.md`](../../CLAUDE.md)).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon EC2 | `aws_cdk.aws_ec2.Instance` | L2 |
| Amazon EC2 | `aws_cdk.aws_ec2.InstanceType`, `InstanceClass`, `InstanceSize` | L2 (helpers) |
| Amazon EC2 | `aws_cdk.aws_ec2.MachineImage` | L2 (helper) |
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Amazon VPC | `aws_cdk.aws_ec2.SecurityGroup` | L2 |
| AWS IAM | `aws_cdk.aws_iam.Role` | L2 |
| AWS IAM | `aws_cdk.aws_iam.ManagedPolicy.from_aws_managed_policy_name` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_13_ec2.py`](../../tests/unit/test_13_ec2.py))
check that: exactly one instance is created, its instance type is
`t3.micro` (this module's whole point - the cheapest general-purpose
size), the security group has no inbound rule at all (no SSH port - reach
it via SSM Session Manager instead), the instance role only attaches the
AWS-managed `AmazonSSMManagedInstanceCore` policy, and every mandatory tag
(see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is
present. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_13_ec2.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth Ec2Stack
uv run cdk diff Ec2Stack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy Ec2Stack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

**A running EC2 instance bills hourly the moment it exists, whether or not
you use it.** A `t3.micro` instance *may* fall within the
[AWS Free Tier](https://aws.amazon.com/free/) for a new account for its
first 12 months - "may", because Free Tier eligibility depends on your
specific account's history and current AWS offer terms, so verify your own
account's Free Tier status before assuming this deploy is free. Outside Free
Tier eligibility, a `t3.micro` costs a small amount per hour - see
[Amazon EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/) for the
current rate in your region. Stop or destroy the instance when you are done
(see [Clean up](#clean-up)) so it does not keep billing.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff Ec2Stack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy Ec2Stack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ec2 describe-instances --filters "Name=tag:Name,Values=*ec2-app"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
instance visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) for
how the UI is enabled in this repository's `docker-compose.yml`).

On a **real AWS account**, once the instance is running and the SSM Agent
has registered it, you can start a shell with no SSH key and no open port:

```bash
aws ssm start-session --target <instance-id>
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
`make cdk-resources STACK=Ec2Stack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=Ec2Stack
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
# AWS::EC2::SecurityGroup (InstanceSecurityGroup896E10BF)
aws ec2 describe-security-groups --group-ids "$(pid InstanceSecurityGroup896E10BF)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::IAM::Role (InstanceRole3CCE2F1D)
aws iam get-role --role-name "${PRODUCT}-${ENV}-role-ec2-instance" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::IAM::InstanceProfile (AppInstanceInstanceProfileC6B6EFAA)
aws iam get-instance-profile --instance-profile-name "$(pid AppInstanceInstanceProfileC6B6EFAA)" --query "InstanceProfile.[InstanceProfileName,Arn]" --output table --region "$REGION"
# AWS::EC2::Instance (AppInstance13C82D50)
aws ec2 describe-instances --instance-ids "$(pid AppInstance13C82D50)" --query "Reservations[].Instances[].[InstanceId,InstanceType,State.Name]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet1RouteTableAssociation4E83B6E4 - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet1DefaultRouteB88F9E93 - shown by its route table
#   AWS::EC2::VPCGatewayAttachment VpcVPCGWBF912B6E - shown by its internet gateway
```
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy Ec2Stack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
```

## Notes and cautions

- **Cost**: see the explicit warning in
  [Deploy to real AWS](#deploy-to-real-aws-optional) - stop the meter with
  `cdk destroy` as soon as you are done experimenting on a real account.
- **No SSH, on purpose.** This module's security group has no inbound rule
  at all - not even port 22. AWS recommends
  [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
  instead of SSH: no inbound port to manage or forget about, no SSH key
  pairs to distribute or rotate, and every session is recorded in
  CloudTrail. This module attaches the AWS-managed
  `AmazonSSMManagedInstanceCore` policy to the instance's role so Session
  Manager works on a real account (the SSM Agent ships preinstalled on
  Amazon Linux 2023 AMIs) - wiring up the agent or the role in more depth is
  out of scope here, since this module is about EC2 itself.
- **floci and Session Manager**: floci emulates the EC2 API surface, not a
  real virtual machine you can SSM into - `aws ssm start-session` only works
  once this stack is deployed to a real AWS account with the SSM Agent
  actually running on the instance.
- `nat_gateways=0` and a `PUBLIC`-only subnet keep this module's VPC free of
  NAT Gateway cost - see module 03 (VPC) and module 05 (NAT Gateway) for
  why a NAT Gateway bills hourly the moment it exists.

## References

- [Amazon EC2 - What is Amazon EC2?](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/concepts.html)
- [Amazon EC2 instance types](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html)
- [Amazon EC2 pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [AWS Systems Manager Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [Systems Manager - set up an instance profile with `AmazonSSMManagedInstanceCore`](https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-instance-profile.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Instance`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Instance.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.MachineImage`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/MachineImage.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
