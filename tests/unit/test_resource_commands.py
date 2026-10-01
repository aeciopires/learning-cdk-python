"""Unit tests for scripts/resource_commands.py - the AWS CLI command generator
behind every README's "List every resource with the AWS CLI" section and
`make cdk-resources`. No AWS calls: templates are synthesized locally,
CloudFormation is stubbed with botocore's Stubber, and the shell is mocked.
"""

from __future__ import annotations

import functools
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import aws_cdk as cdk
import boto3
import pytest
from aws_cdk import cx_api
from botocore.stub import Stubber

import app as root_app
from examples.enterprise_stack import app as enterprise_app

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "resource_commands.py"
_spec = importlib.util.spec_from_file_location("resource_commands", SCRIPT)
assert _spec is not None and _spec.loader is not None
rc = importlib.util.module_from_spec(_spec)
sys.modules["resource_commands"] = rc  # @dataclass looks its module up there
_spec.loader.exec_module(rc)

PRODUCT = "learning-cdk-python"


def _synth(main, tmp_path, monkeypatch, **env):
    monkeypatch.setattr(main.__globals__["cdk"], "App", functools.partial(cdk.App, outdir=str(tmp_path)))
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    main()
    return {s.stack_name: s.template for s in cx_api.CloudAssembly(str(tmp_path)).stacks}


@pytest.fixture(scope="module")
def all_templates(tmp_path_factory):
    """Every module stack plus the enterprise example's prd cells (all 14 builders)."""
    monkeypatch = pytest.MonkeyPatch()
    for var in ("CDK_DEFAULT_ACCOUNT", "CDK_DEFAULT_REGION", "AWS_ACCOUNT_ID", "AWS_REGION", "CDK_PRODUCT"):
        monkeypatch.delenv(var, raising=False)
    templates = _synth(root_app.main, tmp_path_factory.mktemp("modules"), monkeypatch, CDK_ENVIRONMENT="dev")
    templates |= _synth(enterprise_app.main, tmp_path_factory.mktemp("ent"), monkeypatch, ENTERPRISE_ENVIRONMENT="prd")
    monkeypatch.undo()
    return templates


def _context(template, environment="dev"):
    return rc.TemplateContext(template, PRODUCT, environment)


def test_every_resource_type_is_handled_or_explained(all_templates):
    """No resource type in this repository falls through to the generic note."""
    for template in all_templates.values():
        commands, notes = rc.build_commands(_context(template, rc.environment_of(template, "dev")))
        for note in notes:
            assert "shown by the table above" not in note, note
        for command in commands:
            assert command.command.startswith("aws ") and command.command.endswith('--region "$REGION"')


def test_names_are_parametrized_by_product_and_environment(all_templates):
    commands, _ = rc.build_commands(_context(all_templates["SqsStack"]))
    assert {c.command for c in commands} >= {
        'aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-sqs-orders" --query "QueueUrl" --output table --region "$REGION"'
    }


def test_unnamed_resources_are_found_through_the_stack(all_templates):
    commands, notes = rc.build_commands(_context(all_templates["VpcStack"]))
    vpc = next(c for c in commands if c.resource_type == "AWS::EC2::VPC")
    assert '--vpc-ids "$(pid Vpc' in vpc.command
    assert any("SubnetRouteTableAssociation" in n and "its route table" in n for n in notes)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("learning-cdk-python-dev-sqs-orders", "${PRODUCT}-${ENV}-sqs-orders"),
        ("/learning-cdk-python/dev/app/greeting", "/${PRODUCT}/${ENV}/app/greeting"),
        ("learning-cdk-python.example.com", "${PRODUCT}.example.com"),
        ("unrelated", "unrelated"),
    ],
)
def test_parametrize(value, expected):
    assert _context({}).parametrize(value) == expected


def test_ref_resolves_ref_getatt_lists_and_literals():
    template = {"Resources": {"Q": {"Type": "AWS::SQS::Queue", "Properties": {"QueueName": "learning-cdk-python-dev-q"}}}}
    context = _context(template)
    assert context.ref({"Ref": "Q"}, "QueueName") == "${PRODUCT}-${ENV}-q"
    assert context.ref({"Fn::GetAtt": ["Q", "Arn"]}) == "$(pid Q)"
    assert context.ref([{"Ref": "Q"}]) == "$(pid Q)"
    assert context.ref("learning-cdk-python-dev-x") == "${PRODUCT}-${ENV}-x"


def test_unknown_types_get_a_generic_note_and_metadata_is_skipped():
    template = {"Resources": {"M": {"Type": "AWS::CDK::Metadata"}, "X": {"Type": "AWS::New::Thing"}}}
    commands, notes = rc.build_commands(_context(template))
    assert commands == [] and notes == ["AWS::New::Thing X - shown by the table above"]


def test_autoscaling_falls_back_without_an_ecs_cluster():
    template = {"Resources": {"T": {"Type": "AWS::ApplicationAutoScaling::ScalableTarget", "Properties": {}}}}
    commands, _ = rc.build_commands(_context(template))
    assert "'${PRODUCT}-${ENV}'" in commands[0].command


def test_unnamed_state_machine_uses_its_physical_arn():
    template = {"Resources": {"S": {"Type": "AWS::StepFunctions::StateMachine", "Properties": {}}}}
    commands, _ = rc.build_commands(_context(template))
    assert '--state-machine-arn "$(pid S)"' in commands[0].command


def test_markdown_adds_account_and_floci_notes(all_templates):
    sns = rc.render_markdown("SnsStack", _context(all_templates["SnsStack"]), "us-east-1")
    assert sns.startswith("```bash\n") and "ACCOUNT=$(aws sts" in sns and "STACK=SnsStack" in sns
    assert "On floci" not in sns

    msk = rc.render_markdown("MskStack", _context(all_templates["MskStack"]), "eu-west-1")
    assert "REGION=eu-west-1" in msk and "`AWS::MSK::Cluster`" in msk and "ACCOUNT=" not in msk

    cloudwatch = rc.render_markdown("CloudWatchStack", _context(all_templates["CloudWatchStack"]))
    assert "`AWS::Logs::MetricFilter` is created, but floci" in cloudwatch


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        ([{"Key": "environment", "Value": "stg"}], "stg"),
        ({"environment": "prd"}, "prd"),
        ([{"Key": "other", "Value": "x"}], "dev"),
        (None, "dev"),
    ],
)
def test_environment_of(tags, expected):
    template = {"Resources": {"R": {"Type": "T", "Properties": {"Tags": tags}}}}
    assert rc.environment_of(template, "dev") == expected


def test_run_stack_counts_only_unexpected_misses(monkeypatch, capsys):
    template = {
        "Resources": {
            "Q": {"Type": "AWS::SQS::Queue", "Properties": {"QueueName": "learning-cdk-python-dev-q"}},
            "Missing": {"Type": "AWS::SQS::Queue", "Properties": {"QueueName": "learning-cdk-python-dev-gone"}},
            "Gap": {"Type": "AWS::MSK::Cluster", "Properties": {"ClusterName": "learning-cdk-python-dev-k"}},
        }
    }
    outputs = {"q\"": ("https://queue", 0), "gone": ("", 254), "k\"": ("", 0)}

    def fake_run(args, **kwargs):
        script = args[2]
        out, code = next(v for k, v in outputs.items() if k in script.splitlines()[-1])
        return subprocess.CompletedProcess(args, code, stdout=out, stderr="boom" if code else "")

    monkeypatch.setattr(rc.subprocess, "run", fake_run)
    assert rc.run_stack("S", template, product=PRODUCT, environment="dev", region="us-east-1") == 1
    output = capsys.readouterr().out
    assert "ok AWS::SQS::Queue Q" in output and "-- AWS::SQS::Queue Missing" in output
    assert "~~ AWS::MSK::Cluster Gap" in output and "boom" in output


def _cloudformation():
    return boto3.client("cloudformation", region_name="us-east-1", aws_access_key_id="t", aws_secret_access_key="t")


def test_deployed_stacks_skips_deleted_nested_and_bootstrap():
    client = _cloudformation()
    with Stubber(client) as stub:
        stub.add_response(
            "list_stacks",
            {
                "StackSummaries": [
                    {"StackName": n, "StackStatus": s, "CreationTime": "2026-01-01", **extra}
                    for n, s, extra in [
                        ("B", "CREATE_COMPLETE", {}),
                        ("A", "UPDATE_COMPLETE", {}),
                        ("Old", "DELETE_COMPLETE", {}),
                        ("A-Nested", "CREATE_COMPLETE", {"ParentId": "arn:parent"}),
                        ("CDKToolkit", "CREATE_COMPLETE", {}),
                    ]
                ]
            },
            {},
        )
        assert rc.deployed_stacks(client) == ["A", "B"]


def test_deployed_template_parses_a_json_string():
    client = _cloudformation()
    with Stubber(client) as stub:
        stub.add_response("get_template", {"TemplateBody": json.dumps({"Resources": {}})}, {"StackName": "S"})
        assert rc.deployed_template(client, "S") == {"Resources": {}}


def test_deployed_template_accepts_an_already_parsed_dict():
    """boto3 itself hands back a JSON template already parsed into a dict."""

    class Client:
        def get_template(self, StackName):  # boto3's parameter name
            return {"TemplateBody": {"Resources": {"R": {}}}}

    assert rc.deployed_template(Client(), "S") == {"Resources": {"R": {}}}


def test_main_markdown(tmp_path, capsys, all_templates):
    template_file = tmp_path / "SqsStack.template.json"
    template_file.write_text(json.dumps(all_templates["SqsStack"]))
    assert rc.main(["--markdown", "SqsStack", "--template", str(template_file)]) == 0
    assert "STACK=SqsStack" in capsys.readouterr().out


def test_main_markdown_needs_one_stack_and_a_template():
    with pytest.raises(SystemExit):
        rc.main(["--markdown", "SqsStack"])


def test_main_needs_a_stack_or_all():
    with pytest.raises(SystemExit):
        rc.main([])


@pytest.mark.parametrize(("missing", "check", "code"), [(0, True, 0), (2, False, 0), (2, True, 1)])
def test_main_runs_named_or_all_stacks(monkeypatch, capsys, missing, check, code):
    calls = []
    monkeypatch.setattr(rc.boto3, "client", lambda service, region_name: region_name)
    monkeypatch.setattr(rc, "deployed_stacks", lambda client: ["EnterprisePrdCell01Stack", "VpcStack"])
    monkeypatch.setattr(rc, "deployed_template", lambda client, stack: {"Resources": {}})

    def fake_run_stack(stack, template, *, product, environment, region):
        calls.append((stack, region))
        return missing

    monkeypatch.setattr(rc, "run_stack", fake_run_stack)
    args = ["--all", "--prefix", "EnterprisePrd", "--region", "us-east-1", "--region", "us-west-2"]
    assert rc.main(args + (["--check"] if check else [])) == code
    assert calls == [("EnterprisePrdCell01Stack", "us-east-1"), ("EnterprisePrdCell01Stack", "us-west-2")]
    assert "2 stack(s)" in capsys.readouterr().out

    calls.clear()
    assert rc.main(["VpcStack"]) == 0
    assert calls == [("VpcStack", "us-east-1")]
