<!-- TOC -->

- [learning-cdk-python](#learning-cdk-python)
  - [What this is](#what-this-is)
  - [Quickstart](#quickstart)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [Developers](#developers)
  - [License](#license)

<!-- TOC -->

# learning-cdk-python

A beginner learning path for managing AWS resources with the
[AWS Cloud Development Kit (CDK) v2](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
in Python, using [uv](https://docs.astral.sh/uv/) as the package manager
and [floci](https://floci.io) (via `docker-compose.yml`, or `floci-cli`) as
a free, local AWS emulator - 44 small, independent, deployable modules, one
per AWS service, each with its own explanation and step-by-step
instructions. No AWS account or cost is required to complete it.

## What this is

- **44 modules** (`modules/01_iam` through `modules/44_resource_quotas`),
  grouped into 11 phases in [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md)
  - IAM, STS, VPC networking (subnets, security groups, route tables,
    Internet/NAT/Transit Gateway, VPC Peering), KMS, Secrets Manager,
    Parameter Store, ACM, S3, EC2, ECR, ECS, EKS, Lambda, RDS (MySQL,
    PostgreSQL, Aurora), DynamoDB, ElastiCache, OpenSearch, Kinesis,
    Athena, SQS, SNS, EventBridge, Step Functions, ALB, NLB, CloudFront,
    Route 53, API Gateway, Cognito, SES, WAF, GuardDuty, CloudWatch,
    CloudTrail, AWS Backup, Cost Explorer, and Resource Groups & Tagging.
- Each module is a minimal, real, deployable **AWS CDK stack written in
  Python**, plus a README explaining what it teaches, which CDK constructs
  it uses, and how to deploy/verify/clean it up.
- Every resource follows one **tagging policy** (`environment`, `product`,
  `Name`, `team-owner`, `pci`, `cell-based`, `cell-id`) and one **naming
  policy** (hyphen-separated names) - see
  [`REQUIREMENTS.md`](REQUIREMENTS.md).
- Every stack is **account/region-agnostic** - no hardcoded AWS account ID,
  region, or Availability Zone.

## Quickstart

Never used AWS CDK, Docker, or uv before? Follow
[`REQUIREMENTS.md`, section 0](REQUIREMENTS.md#0-zero-to-your-first-deploy-in-order)
- it explains the concepts and gets you to your first `cdk deploy` in 9
steps. The short version, once the prerequisites in
[`REQUIREMENTS.md`, section 3](REQUIREMENTS.md#3-required-software) are
installed:

```bash
git clone <this-repository-url> && cd learning-cdk-python
make check                            # confirms everything above is actually installed
uv sync
docker compose up -d floci
cp .env.example .env && set -a; source .env; set +a
uv run cdk list                       # see every module's stack id
uv run cdk deploy IamStack --require-approval never   # deploy the first module
uv run cdk destroy IamStack           # and clean it up when you're done
```

## Documentation

| | |
|---|---|
| Prerequisites, floci/uv setup, tagging and naming policy | [`REQUIREMENTS.md`](REQUIREMENTS.md) |
| The full 44-module path, grouped into 11 phases | [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md) |
| Diagrams: the CDK workflow, the floci local environment, and how AWS resources relate to each other | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Conventions for anyone (human or AI assistant) extending this repository | [`CLAUDE.md`](CLAUDE.md) |
| Changelog | [`CHANGELOG.md`](CHANGELOG.md) |

## Contributing

For information on how to propose a change or add a new module, see
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Developers

Aécio dos Santos Pires<br>
https://linktr.ee/aeciopires

## License

[GNU General Public License v3.0](LICENSE).
