<!-- TOC -->

- [Module 33 - Route 53 (a private hosted zone)](#module-33---route-53-a-private-hosted-zone)
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

# Module 33 - Route 53 (a private hosted zone)

## Overview

Amazon Route 53 is AWS's DNS (Domain Name System) service: it translates
names (`app.example.internal`) into IP addresses (or other targets). A
**hosted zone** is a container for the DNS records of one domain. This
module creates a **private** hosted zone - one that only resolves inside a
VPC, never on the public internet - plus its own small VPC and one example
`A` record.

## What you will learn

- What a hosted zone and a record are, and the two hosted zone types:
  `route53.PrivateHostedZone` (this module) resolves only inside the VPC(s)
  it is associated with; `route53.PublicHostedZone` resolves anywhere on the
  internet, for a real registered domain.
- Why this module defaults to **Private**: no cost, and safe to deploy
  without owning a real domain name (see
  [Notes and cautions](#notes-and-cautions) for the cost `PublicHostedZone`
  has instead).
- How `route53.ARecord(zone=..., target=route53.RecordTarget
  .from_ip_addresses(...))` creates a DNS record pointing a name at one or
  more IP addresses.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon Route 53 | `aws_cdk.aws_route53.PrivateHostedZone` | L2 |
| Amazon Route 53 | `aws_cdk.aws_route53.ARecord` | L2 |
| Amazon Route 53 | `aws_cdk.aws_route53.RecordTarget` | L2 (helper) |
| Amazon VPC | `aws_cdk.aws_ec2.Vpc` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_33_route53.py`](../../tests/unit/test_33_route53.py))
check that: exactly one private hosted zone is created and associated with
the VPC (what makes it "private"), exactly one `A` record exists pointing at
`10.0.0.10`, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the hosted zone - note `AWS::Route53::HostedZone` carries its tags under a
property named `HostedZoneTags`, not `Tags`, a real exception confirmed
against the real synthesized template. No Docker, floci, or AWS credentials
needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_33_route53.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth Route53Stack
uv run cdk deploy Route53Stack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost -
a **private** hosted zone has no cost (see
[Notes and cautions](#notes-and-cautions) for what a *public* hosted zone
would cost instead, which this module does not create).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy Route53Stack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws route53 list-hosted-zones
aws route53 list-resource-record-sets --hosted-zone-id <hosted-zone-id-from-above>
```

You should see the zone named `learning-cdk-python.internal` (or your
`CDK_PRODUCT` value + `.internal`) and one `A` record named `app` pointing
at `10.0.0.10`.

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
hosted zone and record visually.

## Clean up

```bash
uv run cdk destroy Route53Stack
uv run python scripts/floci_prune.py --apply   # floci only: deletes the empty VPC floci leaves behind (REQUIREMENTS.md section 5.9)
```

## Notes and cautions

- **`PublicHostedZone` is the real-world alternative for actual internet
  DNS** - you would use it once you own a real registered domain and want
  the world to resolve it. **It bills a small monthly fee for as long as it
  exists**, independent of query volume: per the
  [Amazon Route 53 pricing page](https://aws.amazon.com/route53/pricing/)
  (checked while writing this module), the charge is **$0.50/month for each
  of the first 25 hosted zones, and $0.10/month for each additional hosted
  zone** - re-check that page before relying on this number, as AWS pricing
  can change over time. This ongoing charge, even for an unused zone, is
  exactly why this module defaults to `PrivateHostedZone` instead, which has
  no such charge.
- `zone_name = f"{config.product}.internal"` is built directly from
  `config.product`, not via `resource_name()` - `resource_name()` is for
  physical *resource* names (bucket names, queue names, ...), while a zone
  name is a DNS domain name with its own syntax rules.
- This module's VPC uses `nat_gateways=0` and a private-isolated subnet, the
  same reasoning as `modules/03_vpc` - see that module's README for why.

## References

- [Amazon Route 53 - Working with private hosted zones](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zone-private.html)
- [Amazon Route 53 pricing](https://aws.amazon.com/route53/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_route53.PrivateHostedZone`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_route53/PrivateHostedZone.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_route53.ARecord`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_route53/ARecord.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_route53.RecordTarget`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_route53/RecordTarget.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_ec2.Vpc`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html)
