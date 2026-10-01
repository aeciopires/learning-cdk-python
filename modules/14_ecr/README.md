<!-- TOC -->

- [Module 14 - ECR (a private container image repository)](#module-14---ecr-a-private-container-image-repository)
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

# Module 14 - ECR (a private container image repository)

## Overview

Amazon ECR (Elastic Container Registry) is AWS's Docker/OCI container image
registry - a private place to `docker push`/`docker pull` the images your
own services build, as opposed to a public registry. This module creates
one private repository with vulnerability scanning enabled on every image
push.

## What you will learn

- How `aws_ecr.Repository` turns a handful of properties into a private
  image repository, with the same encryption-at-rest and access-control
  model as every other AWS resource in this path.
- What `image_scan_on_push=True` does: every image pushed is automatically
  scanned for known OS/package vulnerabilities (via Amazon ECR's built-in
  scanning, based on the open-source Clair project) as soon as it lands.
- Why a repository containing images cannot simply be deleted, and how
  `empty_on_delete=True` solves that for this learning path - see
  [Notes and cautions](#notes-and-cautions).
- This module creates the repository only - pushing an image into it (with
  `docker push`, from your own build) is a separate, manual step covered in
  [Verify](#verify).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon ECR | `aws_cdk.aws_ecr.Repository` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.
- Docker Engine running locally, only if you want to actually `docker push`
  an image in the [Verify](#verify) section - the stack itself does not
  need Docker to deploy.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_14_ecr.py`](../../tests/unit/test_14_ecr.py))
check that: exactly one repository is created, `ScanOnPush` is enabled
(this module's whole point - every pushed image gets scanned
automatically), `EmptyOnDelete` is `true` (without it, `cdk destroy`
cannot remove a repository that still has images), and every mandatory tag
(see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is
present. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_14_ecr.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth EcrStack
uv run cdk deploy EcrStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(an empty ECR repository has no cost by itself - see
[Notes and cautions](#notes-and-cautions) for the small cost that *does*
apply once you store images in it).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy EcrStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws ecr describe-repositories --repository-names learning-cdk-python-dev-ecr-app
```

Optionally, push a tiny image into it (needs Docker running locally):

```bash
aws ecr get-login-password | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker pull public.ecr.aws/nginx/nginx:latest
docker tag public.ecr.aws/nginx/nginx:latest <account-id>.dkr.ecr.<region>.amazonaws.com/learning-cdk-python-dev-ecr-app:test
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/learning-cdk-python-dev-ecr-app:test
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
repository visually (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
for how the UI is enabled in this repository's `docker-compose.yml`).

## Clean up

```bash
uv run cdk destroy EcrStack
```

## Notes and cautions

- **`empty_on_delete=True`** - a property confirmed present on the
  `Repository` construct's constructor in the installed
  `aws-cdk-lib==2.271.0` - tells CDK to empty the repository of every image
  before CloudFormation deletes it. Without this property, a repository
  that still contains images cannot be deleted by CloudFormation at all; you
  would need to remove every image first with `aws ecr batch-delete-image`
  (or the console) before `cdk destroy`/`aws cloudformation delete-stack`
  would succeed.
- `removal_policy=cdk.RemovalPolicy.DESTROY` is, as with every other
  "delete cleanly" module in this learning path, a choice that suits a
  learning environment - production repositories usually keep
  `RemovalPolicy.RETAIN` so a stack deletion never silently destroys
  published images other services still depend on.
- Storing images in ECR on real AWS has a small, usage-based storage cost
  (per-GB-month) plus data-transfer charges on pull - see
  [Amazon ECR pricing](https://aws.amazon.com/ecr/pricing/). An empty
  repository, on its own, costs nothing.

## References

- [Amazon ECR - What is Amazon ECR?](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html)
- [Amazon ECR - Image scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html)
- [Amazon ECR pricing](https://aws.amazon.com/ecr/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ecr.Repository`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecr/Repository.html)
