<!-- TOC -->

- [Learning path](#learning-path)
  - [How to use this path](#how-to-use-this-path)
  - [Phase 1 - Identity foundations](#phase-1---identity-foundations)
  - [Phase 2 - Networking](#phase-2---networking)
  - [Phase 3 - Security primitives](#phase-3---security-primitives)
  - [Phase 4 - Storage and compute](#phase-4---storage-and-compute)
  - [Phase 5 - Databases](#phase-5---databases)
  - [Phase 6 - Data and analytics](#phase-6---data-and-analytics)
  - [Phase 7 - Messaging and integration](#phase-7---messaging-and-integration)
  - [Phase 8 - Edge, delivery, and APIs](#phase-8---edge-delivery-and-apis)
  - [Phase 9 - Application identity and communication](#phase-9---application-identity-and-communication)
  - [Phase 10 - Protection and detection](#phase-10---protection-and-detection)
  - [Phase 11 - Governance and operations](#phase-11---governance-and-operations)

<!-- TOC -->

# Learning path

44 modules, each a standalone, minimal AWS CDK (Python) stack that teaches
one AWS service, grouped into 11 phases ordered the way a beginner would
reasonably want to learn them: identity and networking first (almost
everything else depends on them conceptually), then compute and storage,
then the more specialized services. You do not have to follow the order -
every module is independently deployable - but it is the order this
repository recommends for a first pass.

## How to use this path

1. Read [`../REQUIREMENTS.md`](../REQUIREMENTS.md) once and set up uv,
   Node.js + the AWS CDK Toolkit, Docker, and floci.
2. Pick a module below and open its `README.md` (`modules/NN_service/README.md`).
   Each one explains: what you'll learn, which AWS services and CDK
   constructs it uses, how to deploy it against floci (free, local), how to
   verify it, and how to clean it up.
3. Read `modules/NN_service/stack.py` next to its README - the code is
   commented to explain *why*, not just *what*.
4. `uv run cdk destroy <StackId>` when you're done with a module, before
   moving to the next one.

## Phase 1 - Identity foundations

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 01 | [`modules/01_iam`](../modules/01_iam/README.md) | `IamStack` | IAM |
| 02 | [`modules/02_sts`](../modules/02_sts/README.md) | `StsStack` | STS |

## Phase 2 - Networking

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 03 | [`modules/03_vpc`](../modules/03_vpc/README.md) | `VpcStack` | VPC (subnets, security groups, route tables) |
| 04 | [`modules/04_internet_gateway`](../modules/04_internet_gateway/README.md) | `InternetGatewayStack` | Internet Gateway |
| 05 | [`modules/05_nat_gateway`](../modules/05_nat_gateway/README.md) | `NatGatewayStack` | NAT Gateway |
| 06 | [`modules/06_transit_gateway`](../modules/06_transit_gateway/README.md) | `TransitGatewayStack` | Transit Gateway |
| 07 | [`modules/07_vpc_peering`](../modules/07_vpc_peering/README.md) | `VpcPeeringStack` | VPC Peering |

## Phase 3 - Security primitives

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 08 | [`modules/08_kms`](../modules/08_kms/README.md) | `KmsStack` | KMS |
| 09 | [`modules/09_secrets_manager`](../modules/09_secrets_manager/README.md) | `SecretsManagerStack` | Secrets Manager |
| 10 | [`modules/10_parameter_store`](../modules/10_parameter_store/README.md) | `ParameterStoreStack` | Systems Manager Parameter Store |
| 11 | [`modules/11_acm`](../modules/11_acm/README.md) | `AcmStack` | ACM |

## Phase 4 - Storage and compute

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 12 | [`modules/12_s3`](../modules/12_s3/README.md) | `S3Stack` | S3 |
| 13 | [`modules/13_ec2`](../modules/13_ec2/README.md) | `Ec2Stack` | EC2 |
| 14 | [`modules/14_ecr`](../modules/14_ecr/README.md) | `EcrStack` | ECR |
| 15 | [`modules/15_ecs`](../modules/15_ecs/README.md) | `EcsStack` | ECS (Fargate) |
| 16 | [`modules/16_eks`](../modules/16_eks/README.md) | `EksStack` | EKS |
| 17 | [`modules/17_lambda`](../modules/17_lambda/README.md) | `LambdaStack` | Lambda |

## Phase 5 - Databases

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 18 | [`modules/18_rds_mysql`](../modules/18_rds_mysql/README.md) | `RdsMysqlStack` | RDS for MySQL |
| 19 | [`modules/19_rds_postgresql`](../modules/19_rds_postgresql/README.md) | `RdsPostgresqlStack` | RDS for PostgreSQL |
| 20 | [`modules/20_rds_aurora`](../modules/20_rds_aurora/README.md) | `RdsAuroraStack` | Aurora PostgreSQL |
| 21 | [`modules/21_dynamodb`](../modules/21_dynamodb/README.md) | `DynamoDbStack` | DynamoDB |
| 22 | [`modules/22_elasticache`](../modules/22_elasticache/README.md) | `ElastiCacheStack` | ElastiCache (Redis OSS) |
| 23 | [`modules/23_opensearch`](../modules/23_opensearch/README.md) | `OpenSearchStack` | Amazon OpenSearch Service |

## Phase 6 - Data and analytics

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 24 | [`modules/24_kinesis`](../modules/24_kinesis/README.md) | `KinesisStack` | Kinesis Data Streams |
| 25 | [`modules/25_athena`](../modules/25_athena/README.md) | `AthenaStack` | Athena |

## Phase 7 - Messaging and integration

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 26 | [`modules/26_sqs`](../modules/26_sqs/README.md) | `SqsStack` | SQS |
| 27 | [`modules/27_sns`](../modules/27_sns/README.md) | `SnsStack` | SNS |
| 28 | [`modules/28_eventbridge`](../modules/28_eventbridge/README.md) | `EventBridgeStack` | EventBridge |
| 29 | [`modules/29_step_functions`](../modules/29_step_functions/README.md) | `StepFunctionsStack` | Step Functions |

## Phase 8 - Edge, delivery, and APIs

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 30 | [`modules/30_alb`](../modules/30_alb/README.md) | `AlbStack` | Application Load Balancer |
| 31 | [`modules/31_nlb`](../modules/31_nlb/README.md) | `NlbStack` | Network Load Balancer |
| 32 | [`modules/32_cloudfront`](../modules/32_cloudfront/README.md) | `CloudFrontStack` | CloudFront |
| 33 | [`modules/33_route53`](../modules/33_route53/README.md) | `Route53Stack` | Route 53 |
| 34 | [`modules/34_api_gateway`](../modules/34_api_gateway/README.md) | `ApiGatewayStack` | API Gateway (REST) |

## Phase 9 - Application identity and communication

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 35 | [`modules/35_cognito`](../modules/35_cognito/README.md) | `CognitoStack` | Cognito |
| 36 | [`modules/36_ses`](../modules/36_ses/README.md) | `SesStack` | SES |

## Phase 10 - Protection and detection

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 37 | [`modules/37_waf`](../modules/37_waf/README.md) | `WafStack` | WAF (WAFv2) |
| 38 | [`modules/38_guardduty`](../modules/38_guardduty/README.md) | `GuardDutyStack` | GuardDuty |
| 39 | [`modules/39_cloudwatch`](../modules/39_cloudwatch/README.md) | `CloudWatchStack` | CloudWatch |
| 40 | [`modules/40_cloudtrail`](../modules/40_cloudtrail/README.md) | `CloudTrailStack` | CloudTrail |

## Phase 11 - Governance and operations

| # | Module | Stack id | AWS service |
|---|---|---|---|
| 41 | [`modules/41_aws_backup`](../modules/41_aws_backup/README.md) | `AwsBackupStack` | AWS Backup |
| 42 | [`modules/42_cost_explorer`](../modules/42_cost_explorer/README.md) | `CostExplorerStack` | Cost Explorer (cost anomaly detection) |
| 43 | [`modules/43_resource_group_tagging`](../modules/43_resource_group_tagging/README.md) | `ResourceGroupTaggingStack` | Resource Groups & Tagging |
| 44 | [`modules/44_resource_quotas`](../modules/44_resource_quotas/README.md) | *(none - see module)* | Service Quotas |
