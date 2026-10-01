<!-- TOC -->

- [Module 11 - ACM (a DNS-validated public certificate)](#module-11---acm-a-dns-validated-public-certificate)
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

# Module 11 - ACM (a DNS-validated public certificate)

## Overview

AWS Certificate Manager (ACM) issues and manages TLS/SSL certificates for
use with services like CloudFront (module 32), Application Load Balancer
(module 30), and API Gateway (module 34). This module requests one public
certificate for a placeholder domain
(`f"{config.product}.example.com"`, e.g. `learning-cdk-python.example.com`),
using DNS validation.

## What you will learn

- **DNS validation** is how ACM confirms you actually control a domain
  before issuing a certificate for it: it gives you a CNAME record to add to
  that domain's DNS, and only issues the certificate once that record is
  visible. `validation=acm.CertificateValidation.from_dns()` (with no
  hosted zone argument) means those records must be added *manually* -
  `CertificateValidation.from_dns(hosted_zone=...)` (not used here) would
  add them automatically, but only works when the domain's DNS is hosted in
  Route 53 in the same account.
- **Why this module is safe to deploy against real AWS as-is, even though
  nobody deploying this learning path owns `example.com`.** Requesting a
  public certificate is free, and ACM simply leaves it in a
  `PENDING_VALIDATION` state forever if the CNAME is never added - it does
  not retry aggressively, alert anyone, or cost anything while pending. See
  [Notes and cautions](#notes-and-cautions).
- **`certificate_name`** - ACM/CloudFormation gives a certificate no
  user-chosen physical name (it is identified by ARN); this property exists
  purely to set the certificate's `Name` tag for a readable label in the
  console, which is why `stack.py` also calls `apply_name_tag()` right
  after - the two are redundant here, and that is fine.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS Certificate Manager | `aws_cdk.aws_certificatemanager.Certificate` | L2 |
| AWS Certificate Manager | `aws_cdk.aws_certificatemanager.CertificateValidation` | L2 (helper) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_11_acm.py`](../../tests/unit/test_11_acm.py))
check that: exactly one certificate is created, it uses DNS validation
(`ValidationMethod: "DNS"`, this module's whole point - see
[What you will learn](#what-you-will-learn)), the domain name matches this
repository's `<product>.example.com` placeholder, and every mandatory tag
(see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present.
No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_11_acm.py -v
```

## Deploy with floci (local, free)

floci emulates ACM's issuance process without waiting for real DNS
validation, so this certificate is issued immediately.

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth AcmStack
uv run cdk diff AcmStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy AcmStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

**Read [Notes and cautions](#notes-and-cautions) first** - this is safe and
free to deploy as-is, but the certificate will sit in
`PENDING_VALIDATION` forever unless you actually own the placeholder domain.

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff AcmStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy AcmStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws acm list-certificates --query "CertificateSummaryList[?DomainName=='learning-cdk-python.example.com']"
aws acm describe-certificate --certificate-arn <arn-from-above>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
certificate visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)).

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
`make cdk-resources STACK=AcmStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=AcmStack
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::CertificateManager::Certificate (AppCertificateE0EB6E86)
aws acm list-certificates --query "CertificateSummaryList[?DomainName=='${PRODUCT}.example.com'].[DomainName,Status,CertificateArn]" --output table --region "$REGION"
```
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy AcmStack
```

## Notes and cautions

- **On real AWS, this certificate will remain `PENDING_VALIDATION`
  forever**, because nobody deploying this learning path owns
  `example.com` (a domain [reserved by IANA](https://www.iana.org/help/example-domains)
  specifically so no one can ever register or control it) and therefore
  cannot add the CNAME record ACM asks for. This is expected, harmless, and
  free - a pending public certificate costs nothing and does not expire on
  its own on a timeline you need to worry about for this exercise.
- Requesting a public ACM certificate is free on real AWS; you only pay
  indirectly through the resources (load balancer, CloudFront distribution,
  ...) that end up using an *issued* certificate - a pending one used by
  nothing has zero cost.
- If you want to see an actually-issued certificate, you need a domain you
  control and either manual DNS validation (add the CNAME ACM gives you) or
  `CertificateValidation.from_dns(hosted_zone=...)` against a Route 53
  hosted zone for that domain (module 33) in the same account.

## References

- [AWS Certificate Manager - Request a public certificate](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html)
- [AWS Certificate Manager pricing](https://aws.amazon.com/certificate-manager/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_certificatemanager.Certificate`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_certificatemanager/Certificate.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_certificatemanager.CertificateValidation`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_certificatemanager/CertificateValidation.html)
