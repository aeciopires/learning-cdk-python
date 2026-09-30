"""Unit tests for modules/44_resource_quotas/script.py.

Module 44 is the one module with no stack.py (Service Quotas has no
CloudFormation resource - see its README.md), so instead of a synthesized
template, this file tests its boto3 script. No request ever leaves this
machine: botocore's `Stubber` (https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.html)
intercepts each API call and returns a canned response, and fails the test
if the script calls anything it didn't expect.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import boto3
import pytest
from botocore.stub import Stubber

SCRIPT = Path(__file__).resolve().parents[2] / "modules" / "44_resource_quotas" / "script.py"

# The module directory has no __init__.py (it has no stack.py to import),
# so the script is loaded straight from its file path.
_spec = importlib.util.spec_from_file_location("resource_quotas_script", SCRIPT)
assert _spec is not None and _spec.loader is not None
script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(script)

QUOTA = {
    "ServiceCode": "ec2",
    "QuotaCode": "L-1216C47A",
    "QuotaName": "Running On-Demand Standard instances",
    "Value": 32.0,
    "Unit": "None",
}


@pytest.fixture
def client():
    """A real service-quotas client with fake credentials, wrapped in a Stubber."""
    real = boto3.client(
        "service-quotas",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    with Stubber(real) as stubber:
        real.stubber = stubber  # type: ignore[attr-defined]
        yield real
        stubber.assert_no_pending_responses()


def test_list_quotas_prints_every_page(client, capsys):
    client.stubber.add_response(
        "list_service_quotas",
        {"Quotas": [QUOTA], "NextToken": "page-2"},
        {"ServiceCode": "ec2"},
    )
    client.stubber.add_response(
        "list_service_quotas",
        {"Quotas": [{**QUOTA, "QuotaCode": "L-OTHER", "Unit": ""}]},
        {"ServiceCode": "ec2", "NextToken": "page-2"},
    )

    script.list_quotas(client, "ec2")

    output = capsys.readouterr().out.splitlines()
    assert output == [
        "L-1216C47A: Running On-Demand Standard instances = 32.0 None",
        "L-OTHER: Running On-Demand Standard instances = 32.0",
    ]


def test_get_quota_returns_and_prints_the_quota(client, capsys):
    client.stubber.add_response(
        "get_service_quota",
        {"Quota": QUOTA},
        {"ServiceCode": "ec2", "QuotaCode": "L-1216C47A"},
    )

    quota = script.get_quota(client)

    assert quota["Value"] == 32.0
    assert '"QuotaCode": "L-1216C47A"' in capsys.readouterr().out


def test_request_increase_sends_the_desired_value(client, capsys):
    client.stubber.add_response(
        "request_service_quota_increase",
        {"RequestedQuota": {"Id": "req-1", "DesiredValue": 64.0}},
        {"ServiceCode": "ec2", "QuotaCode": "L-1216C47A", "DesiredValue": 64.0},
    )

    script.request_increase(client, service_code="ec2", quota_code="L-1216C47A", desired_value=64.0)

    assert '"Id": "req-1"' in capsys.readouterr().out


def test_main_lists_then_inspects_but_never_requests_an_increase(client, monkeypatch, capsys):
    # No request_service_quota_increase response is queued: if main() ever
    # called it, the Stubber would raise and this test would fail.
    client.stubber.add_response("list_service_quotas", {"Quotas": [QUOTA]}, {"ServiceCode": "ec2"})
    client.stubber.add_response(
        "get_service_quota", {"Quota": QUOTA}, {"ServiceCode": "ec2", "QuotaCode": "L-1216C47A"}
    )
    monkeypatch.setattr(script.boto3, "client", lambda service_name: client)
    monkeypatch.setattr(sys, "argv", ["script.py"])

    script.main()

    output = capsys.readouterr().out
    assert "--- Quotas for service 'ec2' ---" in output
    assert "--- Detail for quota 'L-1216C47A' ---" in output
