"""Unit tests for scripts/floci_prune.py - the floci-only orphan-VPC cleanup.

Like tests/unit/test_44_resource_quotas.py, these use botocore's Stubber:
every AWS call gets a canned response, nothing leaves this machine, and the
test fails if the script makes a call it wasn't expected to.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import boto3
import pytest
from botocore.stub import Stubber

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "floci_prune.py"
_spec = importlib.util.spec_from_file_location("floci_prune", SCRIPT)
assert _spec is not None and _spec.loader is not None
prune = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prune)


def _client(service):
    return boto3.client(
        service, region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test"
    )


@pytest.fixture
def ec2():
    client = _client("ec2")
    with Stubber(client) as stubber:
        client.stubber = stubber  # type: ignore[attr-defined]
        yield client
        stubber.assert_no_pending_responses()


@pytest.fixture
def cloudformation():
    client = _client("cloudformation")
    with Stubber(client) as stubber:
        client.stubber = stubber  # type: ignore[attr-defined]
        yield client
        stubber.assert_no_pending_responses()


def _vpc_filter(vpc_id, name="vpc-id"):
    return {"Filters": [{"Name": name, "Values": [vpc_id]}]}


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost:4566", True),
        ("http://127.0.0.1:4566", True),
        ("http://floci:4566", True),
        ("https://localhost.floci.io:4566", True),
        ("https://ec2.us-east-1.amazonaws.com", False),
        ("", False),
        (None, False),
    ],
)
def test_only_floci_endpoints_are_accepted(url, expected):
    assert prune.is_floci_endpoint(url) is expected


def test_owned_vpc_ids_reads_every_live_stack(cloudformation):
    cloudformation.stubber.add_response(
        "list_stacks",
        {
            "StackSummaries": [
                {"StackName": "VpcStack", "StackStatus": "CREATE_COMPLETE", "CreationTime": "2026-01-01"},
                {"StackName": "OldStack", "StackStatus": "DELETE_COMPLETE", "CreationTime": "2026-01-01"},
            ]
        },
        {},
    )
    cloudformation.stubber.add_response(
        "list_stack_resources",
        {
            "StackResourceSummaries": [
                {
                    "LogicalResourceId": "Vpc",
                    "PhysicalResourceId": "vpc-owned",
                    "ResourceType": "AWS::EC2::VPC",
                    "LastUpdatedTimestamp": "2026-01-01",
                    "ResourceStatus": "CREATE_COMPLETE",
                },
                {
                    "LogicalResourceId": "Subnet",
                    "PhysicalResourceId": "subnet-1",
                    "ResourceType": "AWS::EC2::Subnet",
                    "LastUpdatedTimestamp": "2026-01-01",
                    "ResourceStatus": "CREATE_COMPLETE",
                },
            ]
        },
        {"StackName": "VpcStack"},
    )

    assert prune.owned_vpc_ids(cloudformation) == {"vpc-owned"}


def test_orphans_exclude_default_and_owned_vpcs(ec2):
    ec2.stubber.add_response(
        "describe_vpcs",
        {
            "Vpcs": [
                {"VpcId": "vpc-default", "IsDefault": True},
                {"VpcId": "vpc-owned", "IsDefault": False},
                {"VpcId": "vpc-b", "IsDefault": False},
                {"VpcId": "vpc-a"},
            ]
        },
        {},
    )

    assert prune.orphan_vpc_ids(ec2, {"vpc-owned"}) == ["vpc-a", "vpc-b"]


def test_delete_vpc_removes_dependents_in_order(ec2):
    vpc = "vpc-a"
    add = ec2.stubber.add_response
    add(
        "describe_nat_gateways",
        {"NatGateways": [{"NatGatewayId": "nat-1", "State": "available"}, {"NatGatewayId": "nat-2", "State": "deleted"}]},
        _vpc_filter(vpc),
    )
    add("delete_nat_gateway", {"NatGatewayId": "nat-1"}, {"NatGatewayId": "nat-1"})
    add(
        "describe_internet_gateways",
        {"InternetGateways": [{"InternetGatewayId": "igw-1"}]},
        _vpc_filter(vpc, "attachment.vpc-id"),
    )
    add("detach_internet_gateway", {}, {"InternetGatewayId": "igw-1", "VpcId": vpc})
    add("delete_internet_gateway", {}, {"InternetGatewayId": "igw-1"})
    add("describe_subnets", {"Subnets": [{"SubnetId": "subnet-1"}]}, _vpc_filter(vpc))
    add("delete_subnet", {}, {"SubnetId": "subnet-1"})
    add(
        "describe_route_tables",
        {
            "RouteTables": [
                {"RouteTableId": "rtb-main", "Associations": [{"Main": True}]},
                {"RouteTableId": "rtb-1", "Associations": []},
            ]
        },
        _vpc_filter(vpc),
    )
    add("delete_route_table", {}, {"RouteTableId": "rtb-1"})
    add(
        "describe_security_groups",
        {"SecurityGroups": [{"GroupId": "sg-default", "GroupName": "default"}, {"GroupId": "sg-1", "GroupName": "app"}]},
        _vpc_filter(vpc),
    )
    add("delete_security_group", {}, {"GroupId": "sg-1"})
    add("delete_vpc", {}, {"VpcId": vpc})

    prune.delete_vpc(ec2, vpc)  # the main route table and default SG are never touched


def test_already_deleted_resources_are_ignored(ec2):
    vpc = "vpc-a"
    ec2.stubber.add_response("describe_nat_gateways", {"NatGateways": []}, _vpc_filter(vpc))
    ec2.stubber.add_response(
        "describe_internet_gateways", {"InternetGateways": []}, _vpc_filter(vpc, "attachment.vpc-id")
    )
    ec2.stubber.add_response("describe_subnets", {"Subnets": []}, _vpc_filter(vpc))
    ec2.stubber.add_response("describe_route_tables", {"RouteTables": []}, _vpc_filter(vpc))
    ec2.stubber.add_response("describe_security_groups", {"SecurityGroups": []}, _vpc_filter(vpc))
    ec2.stubber.add_client_error("delete_vpc", "InvalidVpcID.NotFound", expected_params={"VpcId": vpc})

    prune.delete_vpc(ec2, vpc)  # no exception


def test_other_errors_are_not_swallowed(ec2):
    ec2.stubber.add_response("describe_nat_gateways", {"NatGateways": []}, _vpc_filter("vpc-a"))
    ec2.stubber.add_response(
        "describe_internet_gateways", {"InternetGateways": []}, _vpc_filter("vpc-a", "attachment.vpc-id")
    )
    ec2.stubber.add_response("describe_subnets", {"Subnets": []}, _vpc_filter("vpc-a"))
    ec2.stubber.add_response("describe_route_tables", {"RouteTables": []}, _vpc_filter("vpc-a"))
    ec2.stubber.add_response("describe_security_groups", {"SecurityGroups": []}, _vpc_filter("vpc-a"))
    ec2.stubber.add_client_error("delete_vpc", "DependencyViolation", expected_params={"VpcId": "vpc-a"})

    with pytest.raises(prune.ClientError):
        prune.delete_vpc(ec2, "vpc-a")


@pytest.mark.parametrize("apply", [False, True])
def test_prune_region_lists_or_deletes(monkeypatch, capsys, apply):
    deleted = []
    monkeypatch.setattr(prune.boto3, "client", lambda service, region_name: service)
    monkeypatch.setattr(prune, "owned_vpc_ids", lambda cfn: {"vpc-owned"})
    monkeypatch.setattr(prune, "orphan_vpc_ids", lambda ec2, owned: ["vpc-a"])
    monkeypatch.setattr(prune, "delete_vpc", lambda ec2, vpc_id: deleted.append(vpc_id))

    assert prune.prune_region("us-east-1", apply=apply) == ["vpc-a"]

    output = capsys.readouterr().out
    if apply:
        assert deleted == ["vpc-a"] and "deleted orphan VPC vpc-a" in output
    else:
        assert deleted == [] and "re-run with --apply" in output


def test_prune_region_with_nothing_to_do(monkeypatch, capsys):
    monkeypatch.setattr(prune.boto3, "client", lambda service, region_name: service)
    monkeypatch.setattr(prune, "owned_vpc_ids", lambda cfn: set())
    monkeypatch.setattr(prune, "orphan_vpc_ids", lambda ec2, owned: [])

    assert prune.prune_region("us-west-2", apply=True) == []
    assert "us-west-2: no orphan VPCs" in capsys.readouterr().out


def test_main_refuses_anything_but_floci(monkeypatch, capsys):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "https://ec2.us-east-1.amazonaws.com")
    assert prune.main([]) == 2
    assert "Refusing to run" in capsys.readouterr().out


def test_main_checks_each_requested_region(monkeypatch):
    calls = []
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    monkeypatch.setattr(prune, "prune_region", lambda region, apply: calls.append((region, apply)))

    assert prune.main(["--region", "us-east-1", "--region", "us-west-2", "--apply"]) == 0
    assert calls == [("us-east-1", True), ("us-west-2", True)]


def test_main_defaults_to_the_configured_region(monkeypatch):
    calls = []
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")
    monkeypatch.setattr(prune, "prune_region", lambda region, apply: calls.append((region, apply)))

    assert prune.main([]) == 0
    assert calls == [("eu-west-1", False)]
