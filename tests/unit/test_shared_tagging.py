"""Unit tests for shared/tagging.py - the 7-tag policy every stack applies.

Every module's own test already checks the 6 stack-wide tags for the
non-cell-based case (the shared `config` fixture). This file covers what
those tests can't: the validation rules in `StandardTags` and the extra
`cell-id` tag a cell-based deployment gets. See REQUIREMENTS.md, "Tagging
policy".
"""

from __future__ import annotations

import aws_cdk as cdk
import pytest
from aws_cdk import aws_sqs as sqs
from aws_cdk.assertions import Match, Template

from shared.tagging import StandardTags, apply_name_tag, apply_standard_tags


def _tagged_queue_template(tags: StandardTags) -> Template:
    """A throwaway stack with one taggable resource, tagged like a module does."""
    stack = cdk.Stack(cdk.App(), "TaggingTestStack")
    apply_standard_tags(stack, tags=tags)
    queue = sqs.Queue(stack, "Queue")
    apply_name_tag(queue, "demo-dev-sqs-orders")
    return Template.from_stack(stack)


def test_cell_based_requires_a_cell_id():
    with pytest.raises(ValueError, match="cell_id is required"):
        StandardTags(product="p", environment="dev", team_owner="t", cell_based=True)


def test_cell_id_is_rejected_when_not_cell_based():
    with pytest.raises(ValueError, match="cell_id must only be set"):
        StandardTags(product="p", environment="dev", team_owner="t", cell_id="cell-01")


def test_cell_based_stacks_also_get_the_cell_id_tag():
    template = _tagged_queue_template(
        StandardTags(
            product="p", environment="stg", team_owner="t", cell_based=True, cell_id="cell-01"
        )
    )

    for tag in (
        {"Key": "cell-based", "Value": "true"},
        {"Key": "cell-id", "Value": "cell-01"},
        {"Key": "environment", "Value": "stg"},
    ):
        template.has_resource_properties("AWS::SQS::Queue", {"Tags": Match.array_with([tag])})


def test_non_cell_based_stacks_have_no_cell_id_tag():
    template = _tagged_queue_template(StandardTags(product="p", environment="dev", team_owner="t"))

    tags = next(iter(template.find_resources("AWS::SQS::Queue").values()))["Properties"]["Tags"]
    assert "cell-id" not in {tag["Key"] for tag in tags}


def test_pci_true_becomes_the_string_true():
    template = _tagged_queue_template(
        StandardTags(product="p", environment="prd", team_owner="t", pci=True)
    )

    template.has_resource_properties(
        "AWS::SQS::Queue", {"Tags": Match.array_with([{"Key": "pci", "Value": "true"}])}
    )


def test_apply_name_tag_sets_the_name_tag():
    template = _tagged_queue_template(StandardTags(product="p", environment="dev", team_owner="t"))

    template.has_resource_properties(
        "AWS::SQS::Queue",
        {"Tags": Match.array_with([{"Key": "Name", "Value": "demo-dev-sqs-orders"}])},
    )
