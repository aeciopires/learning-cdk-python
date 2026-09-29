#!/usr/bin/env python3
"""Module 44 - Service Quotas: list, inspect, and request an increase - via boto3, not CDK.

Service Quotas has **no CloudFormation/CDK resource type at all** (verified
by searching the CloudFormation resource and property type reference below,
and confirmed by an AWS CDK GitHub discussion where the CDK maintainers
note the same gap - see README.md's "Notes and cautions" for the full
citation trail). There is nothing to `cdk synth`/`cdk deploy` here, so this
module has no `stack.py` - see CLAUDE.md section 3, point 4 and
app.py's discovery loop, which skips any `modules/*/` directory with no
`stack.py`.

What Service Quotas *does* have is a read/write **API** - this script is a
runnable, commented example of it via `boto3`, not a CDK stack. It is safe
to run read-only (`list_service_quotas`, `get_service_quota`) against
floci or a real account; `request_service_quota_increase` is commented out
by default because it is a real, non-idempotent action even against a real
AWS account (see the function's docstring before uncommenting it).

AWS docs used while writing this script:
- Service Quotas - What Is Service Quotas: https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html
- Service Quotas boto3 client reference: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/service-quotas.html
- AWS resource and property types reference (searched for "ServiceQuotas" - no entry exists): https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-template-resource-type-ref.html

See README.md for whether floci emulates this API (short answer: as of
this writing, the floci service-coverage page lists "Service Quotas" as
supported - re-check https://floci.io/aws/ yourself before relying on it,
since coverage changes over time).
"""

from __future__ import annotations

import argparse
import json

import boto3

# EC2's "Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances"
# quota - a commonly-hit one, used here purely as a runnable example.
# Quota codes are stable per service; see the boto3 reference above or
# `list_service_quotas` itself to discover others.
EXAMPLE_SERVICE_CODE = "ec2"
EXAMPLE_QUOTA_CODE = "L-1216C47A"


def list_quotas(client, service_code: str = EXAMPLE_SERVICE_CODE) -> None:
    """Print every default and account-specific quota for one service.

    `list_service_quotas` returns the account's *current* values (which may
    already differ from the service default, if an increase was granted in
    the past); `list_aws_default_service_quotas` (not called here) returns
    the untouched defaults for comparison.
    """
    paginator = client.get_paginator("list_service_quotas")
    for page in paginator.paginate(ServiceCode=service_code):
        for quota in page["Quotas"]:
            print(f"{quota['QuotaCode']}: {quota['QuotaName']} = {quota['Value']} {quota.get('Unit', '')}".rstrip())


def get_quota(client, service_code: str = EXAMPLE_SERVICE_CODE, quota_code: str = EXAMPLE_QUOTA_CODE) -> dict:
    """Fetch one specific quota by its (service_code, quota_code) pair."""
    response = client.get_service_quota(ServiceCode=service_code, QuotaCode=quota_code)
    print(json.dumps(response["Quota"], indent=2, default=str))
    return response["Quota"]


def request_increase(client, *, service_code: str, quota_code: str, desired_value: float) -> None:
    """Request a quota increase - a real, tracked, non-idempotent request.

    Not called by `main()` by default. On a real AWS account this opens an
    actual support case that AWS reviews - it is not free-form and not
    instantaneous, and calling it twice with the same arguments creates two
    requests, not one. Uncomment the call in `main()` deliberately, only
    against an account/quota you intend to change.
    """
    response = client.request_service_quota_increase(
        ServiceCode=service_code,
        QuotaCode=quota_code,
        DesiredValue=desired_value,
    )
    print(json.dumps(response["RequestedQuota"], indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-code", default=EXAMPLE_SERVICE_CODE)
    parser.add_argument("--quota-code", default=EXAMPLE_QUOTA_CODE)
    args = parser.parse_args()

    # Reads AWS_ENDPOINT_URL/AWS_ACCESS_KEY_ID/etc. from the environment,
    # same as every module's floci setup - see ../../REQUIREMENTS.md.
    client = boto3.client("service-quotas")

    print(f"--- Quotas for service '{args.service_code}' ---")
    list_quotas(client, args.service_code)

    print(f"\n--- Detail for quota '{args.quota_code}' ---")
    get_quota(client, args.service_code, args.quota_code)

    # Left commented out on purpose - see request_increase()'s docstring.
    # request_increase(
    #     client,
    #     service_code=args.service_code,
    #     quota_code=args.quota_code,
    #     desired_value=64,
    # )


if __name__ == "__main__":
    main()
