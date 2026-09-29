"""Unit tests for modules/31_nlb. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

NlbStack = stack_class("31_nlb")


def _synth(config):
    app = cdk.App()
    stack = NlbStack(app, "TestNlbStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_load_balancer(config):
    template = _synth(config)
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)


def test_load_balancer_is_network_type_and_internet_facing(config):
    """The whole point of this module vs. module 30 (ALB): a layer-4 NLB."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::LoadBalancer",
        {"Type": "network", "Scheme": "internet-facing"},
    )


def test_creates_exactly_one_empty_tcp_target_group(config):
    template = _synth(config)
    template.resource_count_is("AWS::ElasticLoadBalancingV2::TargetGroup", 1)
    template.has_resource_properties(
        "AWS::ElasticLoadBalancingV2::TargetGroup",
        {"Protocol": "TCP", "Port": 80, "TargetType": "ip"},
    )


def test_load_balancer_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::LoadBalancer",
            {"Tags": Match.array_with([tag])},
        )
