#!/usr/bin/env python3
"""Find - and, with --apply, delete - VPCs floci left behind after `cdk destroy`.

Why this exists: floci's CloudFormation does not delete `AWS::EC2::VPC`
resources when a stack is deleted (its VPC provisioner has no delete step -
see REQUIREMENTS.md section 5.9). Everything else a module's VPC owns
(subnets, route tables, internet/NAT gateways, security groups) *is*
deleted, so each `cdk destroy` + `cdk deploy` cycle leaves one more empty
VPC behind. Real AWS CloudFormation deletes VPCs normally - this is a
floci-only cleanup, and it refuses to run against anything but floci.

A VPC is an orphan when it is not a default VPC and no CloudFormation stack
(nested stacks included) in the same account/region lists it as one of its
resources. Run from the repository root, with .env loaded:

    uv run python scripts/floci_prune.py                  # list orphans (dry run)
    uv run python scripts/floci_prune.py --apply          # delete them
    uv run python scripts/floci_prune.py --region us-east-1 --region us-west-2 --apply

Uses the account your credentials map to on floci (AWS_ACCESS_KEY_ID - see
floci's multi-account docs) and AWS_ENDPOINT_URL.
"""

from __future__ import annotations

import argparse
import os
from typing import Any
from urllib.parse import urlparse

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

# Hostnames floci is reachable at from this repository's setup: the host
# (docker-compose.yml publishes port 4566 on localhost) or the Compose
# network (FLOCI_HOSTNAME=floci).
FLOCI_HOSTS = {"localhost", "127.0.0.1", "floci", "localhost.floci.io"}

# Error codes that mean "already gone" - deleting something twice is fine.
NOT_FOUND_CODES = {
    "InvalidVpcID.NotFound",
    "InvalidSubnetID.NotFound",
    "InvalidInternetGatewayID.NotFound",
    "InvalidRouteTableID.NotFound",
    "InvalidGroup.NotFound",
    "NatGatewayNotFound",
    "Gateway.NotAttached",
}


def is_floci_endpoint(endpoint_url: str | None) -> bool:
    """True only for an endpoint that points at floci, never at real AWS."""
    if not endpoint_url:
        return False
    return urlparse(endpoint_url).hostname in FLOCI_HOSTS


def owned_vpc_ids(cloudformation: Any) -> set[str]:
    """Every VPC id some live stack (nested stacks included) lists as a resource."""
    owned: set[str] = set()
    for page in cloudformation.get_paginator("list_stacks").paginate():
        for summary in page["StackSummaries"]:
            if summary["StackStatus"] == "DELETE_COMPLETE":
                continue
            resources = cloudformation.get_paginator("list_stack_resources").paginate(
                StackName=summary["StackName"]
            )
            for resource_page in resources:
                for resource in resource_page["StackResourceSummaries"]:
                    if resource["ResourceType"] == "AWS::EC2::VPC":
                        owned.add(resource["PhysicalResourceId"])
    return owned


def orphan_vpc_ids(ec2: Any, owned: set[str]) -> list[str]:
    """Non-default VPCs no stack owns, sorted."""
    vpcs = ec2.describe_vpcs()["Vpcs"]
    return sorted(v["VpcId"] for v in vpcs if not v.get("IsDefault") and v["VpcId"] not in owned)


def _ignore_not_found(call: Any, **kwargs: Any) -> None:
    try:
        call(**kwargs)
    except ClientError as error:
        if error.response["Error"]["Code"] not in NOT_FOUND_CODES:
            raise


def delete_vpc(ec2: Any, vpc_id: str) -> None:
    """Delete one VPC, after anything inside it that would block the delete.

    On floci an orphan VPC is normally empty except for what every VPC comes
    with (its default security group and main route table, which go with
    it), but anything else found inside is removed first, in dependency
    order, so a half-deleted stack doesn't block the cleanup.
    """
    vpc_filter = [{"Name": "vpc-id", "Values": [vpc_id]}]

    for nat in ec2.describe_nat_gateways(Filters=vpc_filter)["NatGateways"]:
        if nat.get("State") not in ("deleted", "deleting"):
            _ignore_not_found(ec2.delete_nat_gateway, NatGatewayId=nat["NatGatewayId"])

    igw_filter = [{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
    for igw in ec2.describe_internet_gateways(Filters=igw_filter)["InternetGateways"]:
        igw_id = igw["InternetGatewayId"]
        _ignore_not_found(ec2.detach_internet_gateway, InternetGatewayId=igw_id, VpcId=vpc_id)
        _ignore_not_found(ec2.delete_internet_gateway, InternetGatewayId=igw_id)

    for subnet in ec2.describe_subnets(Filters=vpc_filter)["Subnets"]:
        _ignore_not_found(ec2.delete_subnet, SubnetId=subnet["SubnetId"])

    for table in ec2.describe_route_tables(Filters=vpc_filter)["RouteTables"]:
        if not any(a.get("Main") for a in table.get("Associations", [])):
            _ignore_not_found(ec2.delete_route_table, RouteTableId=table["RouteTableId"])

    for group in ec2.describe_security_groups(Filters=vpc_filter)["SecurityGroups"]:
        if group["GroupName"] != "default":
            _ignore_not_found(ec2.delete_security_group, GroupId=group["GroupId"])

    _ignore_not_found(ec2.delete_vpc, VpcId=vpc_id)


def prune_region(region: str, *, apply: bool) -> list[str]:
    """List (and, with apply=True, delete) one region's orphan VPCs."""
    cloudformation = boto3.client("cloudformation", region_name=region)
    ec2 = boto3.client("ec2", region_name=region)
    orphans = orphan_vpc_ids(ec2, owned_vpc_ids(cloudformation))
    for vpc_id in orphans:
        if apply:
            delete_vpc(ec2, vpc_id)
            print(f"{region}: deleted orphan VPC {vpc_id}")
        else:
            print(f"{region}: orphan VPC {vpc_id} (re-run with --apply to delete)")
    if not orphans:
        print(f"{region}: no orphan VPCs")
    return orphans


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--region", action="append", dest="regions",
                        help="region to check (repeatable; default: AWS_DEFAULT_REGION)")
    parser.add_argument("--apply", action="store_true", help="delete the orphans found")
    args = parser.parse_args(argv)

    endpoint = os.getenv("AWS_ENDPOINT_URL")
    if not is_floci_endpoint(endpoint):
        print(f"Refusing to run: AWS_ENDPOINT_URL={endpoint!r} is not floci. This cleanup "
              "is only for floci - real AWS CloudFormation deletes VPCs itself.")
        return 2

    regions = args.regions or [os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION") or "us-east-1"]
    for region in regions:
        prune_region(region, apply=args.apply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
