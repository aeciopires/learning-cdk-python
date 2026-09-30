<!-- TOC -->

- [Module 37 - WAF (WAFv2 web ACL)](#module-37---waf-wafv2-web-acl)
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

# Module 37 - WAF (WAFv2 web ACL)

## Overview

AWS WAF inspects the web requests reaching a protected resource (an
Application Load Balancer, an API Gateway REST API, CloudFront, a Cognito
user pool, ...) and allows or blocks each one based on rules you define.
This module creates one **web ACL** (web access control list): a default
action of "allow", plus one rule that runs an AWS-managed rule group
covering common web exploits.

## What you will learn

- How a web ACL's `DefaultAction` (what happens when no rule matches) and
  `Rules` (evaluated in `Priority` order) fit together.
- How to reference an AWS-managed rule group (`AWSManagedRulesCommonRuleSet`)
  instead of writing byte-match/rate-based rules by hand.
- The difference between a rule's `Action` (used by a rule with its own
  match statement) and `OverrideAction` (used by a rule that wraps a
  managed rule group, whose *internal* rules already carry actions -
  `none` keeps them, `count` downgrades every one to "count only", useful
  while testing a new rule group before enforcing it).
- Why `Scope="CLOUDFRONT"` web ACLs have a region constraint that
  `Scope="REGIONAL"` ones do not - see [Notes and cautions](#notes-and-cautions).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS WAF (WAFv2) | `aws_cdk.aws_wafv2.CfnWebACL` | **L1** (`Cfn*`) |

There is **no L2 construct for WAFv2** in the current stable `aws-cdk-lib`
(confirmed against the [AWS CDK API Reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_wafv2/CfnWebACL.html)
while writing this module) - this module uses the L1 `CfnWebACL`, a 1:1
mapping to the `AWS::WAFv2::WebACL` CloudFormation resource. Every nested
property class used in `stack.py` (`DefaultActionProperty`,
`VisibilityConfigProperty`, `RuleProperty`, `StatementProperty`,
`ManagedRuleGroupStatementProperty`, `OverrideActionProperty`) was verified
against that CloudFormation resource's own documentation - see
[Reference 3](#references).

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_37_waf.py`](../../tests/unit/test_37_waf.py))
check that: exactly one web ACL is created, it is `REGIONAL`-scoped with a
default action of "allow", the AWS-managed `AWSManagedRulesCommonRuleSet`
rule group is wired into its rules (this module's whole point), and every
mandatory tag (see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section
7) is present - `AWS::WAFv2::WebACL` supports the standard `Tags` list. No
Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_37_waf.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth WafStack
uv run cdk deploy WafStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created. A web ACL
itself has no hourly cost, but AWS WAF bills a small monthly fee per web
ACL plus per-rule and per-million-requests charges once it is *associated*
with a real resource (this module creates the web ACL but does not
associate it with anything) - see [Reference 7](#references).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy WafStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws wafv2 list-web-acls --scope REGIONAL
aws wafv2 get-web-acl --scope REGIONAL --name <web-acl-name> --id <id-from-list>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
web ACL's resources visually.

## Clean up

```bash
uv run cdk destroy WafStack
```

## Notes and cautions

- **`Scope="CLOUDFRONT"` has a real, hard region constraint this module
  does not exercise**: a CLOUDFRONT-scoped web ACL must be created in
  `us-east-1` specifically (regardless of which region the CloudFront
  distribution or this stack's other resources live in), because
  CloudFront is itself a global service managed from `us-east-1`. This
  module uses `Scope="REGIONAL"` instead, which has no such constraint -
  see [Reference 4](#references).
- This web ACL is not associated with any resource (no ALB, API Gateway,
  etc. exists in this stack to attach it to) - see
  `AWS::WAFv2::WebACLAssociation` in [Reference 3](#references) for how a
  real deployment would wire it up.
- `AWSManagedRulesCommonRuleSet` is one of many AWS-managed rule groups;
  see [Reference 5](#references) for the full catalog (SQL injection,
  known bad inputs, anonymous IP lists, and more).

## References

- [AWS WAF - How AWS WAF works](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works.html)
- [AWS WAF - Web ACLs](https://docs.aws.amazon.com/waf/latest/developerguide/web-acl.html)
- [AWS::WAFv2::WebACL - AWS CloudFormation](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-wafv2-webacl.html)
- [AWS WAF - How AWS WAF works (CLOUDFRONT scope / us-east-1)](https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works.html)
- [AWS WAF - AWS managed rule groups list](https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_wafv2.CfnWebACL`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_wafv2/CfnWebACL.html)
- [AWS WAF pricing](https://aws.amazon.com/waf/pricing/)
