<!-- TOC -->

- [Module 20 - Aurora (PostgreSQL-compatible)](#module-20---aurora-postgresql-compatible)
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

# Module 20 - Aurora (PostgreSQL-compatible)

## Overview

Amazon Aurora is AWS's own cloud-native relational database engine,
compatible with either MySQL or PostgreSQL wire protocols but built on a
different, distributed storage layer than standalone RDS. This module
creates one Aurora PostgreSQL-compatible cluster with a single
`db.t3.medium` writer instance, plus its own dedicated 2-Availability-Zone
VPC and a Secrets Manager secret for the generated master password.

**Read [Notes and cautions](#notes-and-cautions) before deploying this
module to a real AWS account.** Aurora is typically **pricier** than an
equivalent-size standalone RDS instance (module 18/19) and, like every RDS
family engine, bills hourly the moment it exists.

## What you will learn

- The cluster/instance split: `aws_rds.DatabaseCluster` provisions Aurora's
  shared storage layer; `rds.ClusterInstance.provisioned(...)` provisions
  the compute instance(s) attached to it (here, one `writer`, no
  `readers`).
- **The current (non-deprecated) `DatabaseCluster` API.** `aws_cdk.aws_rds`
  has changed this construct's API across CDK versions: an older shape
  configured instance count via `instances=<int>` and `instance_props=`;
  the current shape - the one this module uses - is
  `writer=rds.ClusterInstance.provisioned("Writer", instance_type=...)`
  with an optional `readers=[...]` list. This was verified directly against
  the `aws_cdk.aws_rds` source shipped in this project's pinned
  `aws-cdk-lib==2.271.0` (not recalled from memory - see the module's
  `stack.py` docstring for exactly what was checked).
- Why a cluster still needs a 2-AZ VPC even though Aurora's storage is
  already replicated across AZs internally - the DB subnet group
  requirement applies the same way it does to standalone RDS (modules 18
  and 19).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |
| Amazon Aurora | `aws_cdk.aws_rds.DatabaseCluster` | L2 |
| Amazon Aurora | `aws_cdk.aws_rds.ClusterInstance` | L2 (helper) |
| Amazon Aurora | `aws_cdk.aws_rds.DatabaseClusterEngine`, `aws_cdk.aws_rds.AuroraPostgresEngineVersion` | L2 (helpers) |
| Amazon Aurora / AWS Secrets Manager | `aws_cdk.aws_rds.Credentials`, `aws_cdk.aws_secretsmanager.Secret`, `aws_cdk.SecretValue` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- floci's Aurora/RDS coverage runs as a real Docker container under the hood
  (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md), "Observations and
  limitations") - this is one of the heavier modules to deploy locally, and
  Aurora-specific behavior (its distributed storage layer, cluster
  endpoints) is one of the harder things for any local emulator to fully
  replicate; treat floci here as "does the CDK code work", not as a
  faithful Aurora performance/availability simulation.

## Tests

New to this repository's tests? Read
[`../../docs/TESTING.md`](../../docs/TESTING.md) first - it explains, from
zero, what a CDK unit test is and how to write your own.

This module's tests
([`../../tests/unit/test_20_rds_aurora.py`](../../tests/unit/test_20_rds_aurora.py))
check that: exactly one `AWS::RDS::DBCluster` and exactly one
`AWS::RDS::DBInstance` are created (the cluster's one writer - no
`readers=` is configured, see `stack.py`), the cluster uses the
`aurora-postgresql` engine at version `17.9`, the writer instance is a
`db.t3.medium` with `PromotionTier: 0` (CloudFormation's marker for the
writer), and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the cluster. The tests also check that the master password is a literal
`{{resolve:secretsmanager:learning-cdk-python-<env>-secret-rds-aurora:SecretString:password::}}`
reference to a named, generated secret, and that the database depends on
that secret (a by-name reference has no implicit dependency). They run in well under a second, with no Docker, no floci,
and no AWS credentials:

```bash
# From the repository root:
uv run pytest tests/unit/test_20_rds_aurora.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth RdsAuroraStack
uv run cdk diff RdsAuroraStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy RdsAuroraStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you have read and understood
[Notes and cautions](#notes-and-cautions) - this module has a real,
ongoing hourly cost, typically higher than modules 18/19, the moment it is
deployed.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff RdsAuroraStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy RdsAuroraStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws rds describe-db-clusters --query "DBClusters[].{Id:DBClusterIdentifier,Status:Status,Engine:Engine}"
aws rds describe-db-instances --query "DBInstances[].{Id:DBInstanceIdentifier,Cluster:DBClusterIdentifier,Status:DBInstanceStatus}"
aws secretsmanager list-secrets --query "SecretList[].Name"
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
cluster, its writer instance, and the generated secret visually.

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
`make cdk-resources STACK=RdsAuroraStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=RdsAuroraStack
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
# AWS::EC2::Subnet (VpcisolatedSubnet1SubnetE62B1B9B)
aws ec2 describe-subnets --subnet-ids "$(pid VpcisolatedSubnet1SubnetE62B1B9B)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcisolatedSubnet1RouteTableE442650B)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcisolatedSubnet1RouteTableE442650B)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcisolatedSubnet2Subnet39217055)
aws ec2 describe-subnets --subnet-ids "$(pid VpcisolatedSubnet2Subnet39217055)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcisolatedSubnet2RouteTable334F9764)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcisolatedSubnet2RouteTable334F9764)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::SecretsManager::Secret (MasterSecretA11BF785)
aws secretsmanager describe-secret --secret-id "${PRODUCT}-${ENV}-secret-rds-aurora" --query "[Name,ARN]" --output table --region "$REGION"
# AWS::RDS::DBSubnetGroup (ClusterSubnetsDCFA5CB7)
aws rds describe-db-subnet-groups --db-subnet-group-name "$(pid ClusterSubnetsDCFA5CB7)" --query "DBSubnetGroups[].DBSubnetGroupName" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (ClusterSecurityGroup0921994B)
aws ec2 describe-security-groups --group-ids "$(pid ClusterSecurityGroup0921994B)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::RDS::DBCluster (ClusterEB0386A7)
aws rds describe-db-clusters --db-cluster-identifier "${PRODUCT}-${ENV}-rds-aurora" --query "DBClusters[].[DBClusterIdentifier,Engine,Status]" --output table --region "$REGION"
# AWS::RDS::DBInstance (ClusterWriterA91BB273)
aws rds describe-db-instances --db-instance-identifier "$(pid ClusterWriterA91BB273)" --query "DBInstances[].[DBInstanceIdentifier,Engine,DBInstanceStatus]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::EC2::SubnetRouteTableAssociation VpcisolatedSubnet1RouteTableAssociationD259E31A - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcisolatedSubnet2RouteTableAssociation25A4716F - shown by its route table
```
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy RdsAuroraStack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
```

## Notes and cautions

- **Aurora is typically pricier than an equivalent-size standalone RDS
  instance**, and - like every module in the RDS/Aurora family in this
  path - bills **hourly from the moment the cluster and its writer instance
  exist**, regardless of whether anything ever connects to them. This is
  one of the more expensive modules in this learning path on real AWS; see
  the pricing reference below and check current rates for your region
  before deploying to a real account.
- **Master username:** this module uses
  `"dbadmin"` (in its generated secret and `rds.Credentials.from_password()`), not `"admin"`.
  `cdk synth RdsAuroraStack` flags `"admin"` with a CloudFormation
  template-validation warning (not a hard error) -
  `MasterUsername: 'admin' must not be one of ['admin'] for a
  PostgreSQL-compatible engine, where it is a reserved word` - so this
  module and module 19 (RDS PostgreSQL) both use `"dbadmin"` instead.
- `removal_policy=RemovalPolicy.DESTROY` is chosen so this module is easy
  to tear down while learning; `readers=` is intentionally left unset (no
  read replica) to keep this module to the lowest cost an Aurora cluster
  can be while still demonstrating the writer/reader instance model.
- The exact minimum/currently-supported instance classes for Aurora
  PostgreSQL can change over time - re-check the
  [Aurora PostgreSQL instance class support](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Concepts.html)
  page before relying on `db.t3.medium` remaining valid.

## References

- [Amazon Aurora User Guide - Overview](https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/CHAP_AuroraOverview.html)
- [Amazon Aurora pricing](https://aws.amazon.com/rds/aurora/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.DatabaseCluster`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/DatabaseCluster.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.ClusterInstance`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/ClusterInstance.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.AuroraPostgresEngineVersion`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/AuroraPostgresEngineVersion.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_rds.Credentials`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_rds/Credentials.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
