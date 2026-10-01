<!-- TOC -->

- [Module 32 - CloudFront (a distribution in front of a private S3 bucket)](#module-32---cloudfront-a-distribution-in-front-of-a-private-s3-bucket)
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

# Module 32 - CloudFront (a distribution in front of a private S3 bucket)

## Overview

Amazon CloudFront is AWS's content delivery network (CDN): it caches your
content at edge locations around the world, close to your users, so it does
not have to be fetched from the origin (here, an S3 bucket) on every
request. This module creates a private S3 bucket (no public access at all)
and a CloudFront distribution that is the *only* thing allowed to read from
it, using Origin Access Control (OAC).

## What you will learn

- How `cloudfront.Distribution` + `cloudfront.BehaviorOptions` (CDK L2
  constructs) describe "serve this origin, with these caching/viewer
  rules".
- What Origin Access Control (OAC) is: a signed-request mechanism that lets
  CloudFront read from a **private** S3 bucket (`block_public_access=
  s3.BlockPublicAccess.BLOCK_ALL`) without the bucket ever being reachable
  directly from the internet.
- Why this module uses `origins.S3BucketOrigin.with_origin_access_control
  (bucket)` and not the older `origins.S3Origin` (see
  [Notes and cautions](#notes-and-cautions) - this was verified, not
  assumed).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon CloudFront | `aws_cdk.aws_cloudfront.Distribution` | L2 |
| Amazon CloudFront | `aws_cdk.aws_cloudfront.BehaviorOptions` | L2 (props) |
| Amazon CloudFront | `aws_cdk.aws_cloudfront_origins.S3BucketOrigin` | L2 |
| Amazon S3 | `aws_cdk.aws_s3.Bucket` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_32_cloudfront.py`](../../tests/unit/test_32_cloudfront.py))
check that: exactly one distribution is created, its default cache behavior
sets `ViewerProtocolPolicy: redirect-to-https`, the origin bucket's
`PublicAccessBlockConfiguration` has every setting `true` (the whole point
of fronting a private bucket with Origin Access Control), and every
mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section
7) is present on the distribution - `AWS::CloudFront::Distribution` does
carry a top-level `Tags` property, confirmed against the real synthesized
template. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_32_cloudfront.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth CloudFrontStack
uv run cdk diff CloudFrontStack   # what deploy would change - creates nothing (REQUIREMENTS.md section 5.11)
uv run cdk deploy CloudFrontStack --require-approval never --method=direct
```

floci's CloudFront support may be more limited/less faithful than services
like S3 or SQS - see [`../../REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).
If `describe-distributions` below looks incomplete against floci, that is a
known floci fidelity limitation, not a problem with this module's code.

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(see [Notes and cautions](#notes-and-cautions) - CloudFront has no hourly
charge, only usage-based pricing).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk diff CloudFrontStack --profile <your-aws-cli-profile>   # review the changes first
uv run cdk deploy CloudFrontStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws cloudfront list-distributions
aws s3api get-bucket-policy --bucket learning-cdk-python-dev-s3-cdn-origin
aws s3api get-public-access-block --bucket learning-cdk-python-dev-s3-cdn-origin
```

The bucket policy should show a statement granting only
`cloudfront.amazonaws.com` access, conditioned on this distribution's ARN -
that is Origin Access Control in effect. `get-public-access-block` should
show every setting `true` (fully blocked).

On floci (2.1.0), both of those S3 commands fail (`NoSuchBucketPolicy`,
`NoSuchPublicAccessBlockConfiguration`): its CloudFormation creates the
bucket but applies neither the `AWS::S3::BucketPolicy` nor the
`PublicAccessBlockConfiguration` (its unreleased main branch does). On real
AWS they show what's described above.

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
distribution and bucket visually.

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
`make cdk-resources STACK=CloudFrontStack` runs the same commands for you.

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=CloudFrontStack
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::S3::Bucket (OriginBucketCA772B8F)
aws s3api list-buckets --query "Buckets[?Name=='${PRODUCT}-${ENV}-s3-cdn-origin'].[Name,CreationDate]" --output table --region "$REGION"
# AWS::IAM::Role (CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)
aws iam get-role --role-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::Lambda::Function (CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)
aws lambda get-function --function-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# AWS::CloudFront::OriginAccessControl (DistributionOrigin1S3OriginAccessControlEB606076)
aws cloudfront get-origin-access-control --id "$(pid DistributionOrigin1S3OriginAccessControlEB606076)" --query "OriginAccessControl.[Id,OriginAccessControlConfig.Name]" --output table --region "$REGION"
# AWS::CloudFront::Distribution (Distribution830FAC52)
aws cloudfront get-distribution --id "$(pid Distribution830FAC52)" --query "Distribution.[Id,DomainName,Status]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::S3::BucketPolicy OriginBucketPolicyFD67BA59 - shown by its bucket
#   Custom::S3AutoDeleteObjects OriginBucketAutoDeleteObjectsCustomResource064ED07E - shown by the provider Lambda function and role listed here
```
<!-- END resource-commands -->

## Clean up

```bash
uv run cdk destroy CloudFrontStack
```

## Notes and cautions

- **`S3BucketOrigin.with_origin_access_control` vs. `S3Origin` - verified,
  not assumed.** Introspecting the installed `aws_cdk.aws_cloudfront_origins`
  module (aws-cdk-lib 2.271.0) confirms `S3BucketOrigin` exists with a
  `with_origin_access_control` classmethod; checking the construct's source
  (`aws-cloudfront-origins/lib/s3-origin.ts` in the `aws/aws-cdk` repository,
  tag `v2.271.0`) confirms `S3Origin` carries a `@deprecated` tag reading
  *"Use `S3BucketOrigin` or `S3StaticWebsiteOrigin` instead."* This module
  therefore uses `S3BucketOrigin.with_origin_access_control`, the current,
  non-deprecated, AWS-recommended way to originate from a private S3 bucket.
- `removal_policy=RemovalPolicy.DESTROY` and `auto_delete_objects=True` are
  set on the bucket so `cdk destroy` fully cleans this module up (the
  default `RemovalPolicy.RETAIN` would otherwise leave the bucket, and
  anything in it, behind). Reconsider both for a bucket holding real data.
- CloudFront has no hourly charge - you pay for data transfer and requests,
  with a modest AWS Free Tier - see the pricing reference below, and
  re-check current numbers before relying on them.
- This bucket has no content in it - the distribution will return errors
  for any object path until you upload something with, for example,
  `aws s3 cp <file> s3://learning-cdk-python-dev-s3-cdn-origin/`.

## References

- [Amazon CloudFront - Restricting access to an Amazon S3 origin (Origin Access Control)](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html)
- [Amazon CloudFront pricing](https://aws.amazon.com/cloudfront/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_cloudfront.Distribution`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront/Distribution.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_cloudfront.BehaviorOptions`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront/BehaviorOptions.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_cloudfront_origins.S3BucketOrigin`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudfront_origins/S3BucketOrigin.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_s3.Bucket`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_s3/Bucket.html)
