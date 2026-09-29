"""Unit tests for modules/37_waf. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

WafStack = stack_class("37_waf")


def _synth(config):
    app = cdk.App()
    stack = WafStack(app, "TestWafStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_web_acl(config):
    template = _synth(config)
    template.resource_count_is("AWS::WAFv2::WebACL", 1)


def test_web_acl_is_regional_scoped_and_allows_by_default(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::WAFv2::WebACL",
        {"Scope": "REGIONAL", "DefaultAction": {"Allow": {}}},
    )


def test_web_acl_runs_the_aws_managed_common_rule_set(config):
    """This module's whole point: the AWS-managed `AWSManagedRulesCommonRuleSet`
    is wired in, not a hand-written rule - see README.md.
    """
    template = _synth(config)
    template.has_resource_properties(
        "AWS::WAFv2::WebACL",
        {
            "Rules": Match.array_with(
                [
                    Match.object_like(
                        {
                            "Statement": Match.object_like(
                                {
                                    "ManagedRuleGroupStatement": Match.object_like(
                                        {
                                            "VendorName": "AWS",
                                            "Name": "AWSManagedRulesCommonRuleSet",
                                        }
                                    )
                                }
                            )
                        }
                    )
                ]
            )
        },
    )


def test_web_acl_has_the_mandatory_tags(config):
    """`AWS::WAFv2::WebACL` supports a standard `Tags` list of `{"Key": ...,
    "Value": ...}` pairs (confirmed in the real synthesized
    `cdk.out/WafStack.template.json`), so the usual one-`array_with`-call-
    per-tag discipline applies here too.
    """
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::WAFv2::WebACL", {"Tags": Match.array_with([tag])}
        )
