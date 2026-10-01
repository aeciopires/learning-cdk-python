"""Unit tests for modules/23_opensearch. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

OpenSearchStack = stack_class("23_opensearch")


def _synth(config):
    app = cdk.App()
    stack = OpenSearchStack(app, "TestOpenSearchStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_domain(config):
    template = _synth(config)
    template.resource_count_is("AWS::OpenSearchService::Domain", 1)


def test_domain_is_a_single_node_single_az_deployment(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::OpenSearchService::Domain",
        {
            "EngineVersion": "OpenSearch_3.7",
            "ClusterConfig": Match.object_like(
                {
                    "InstanceCount": 1,
                    "InstanceType": "t3.small.search",
                    "ZoneAwarenessEnabled": False,
                }
            ),
        },
    )


def test_domain_name_respects_the_28_character_aws_limit(config):
    """Amazon OpenSearch Service domain names have a hard 28-character AWS
    limit - stack.py truncates resource_name()'s output to fit. See README.md."""
    template = _synth(config)
    domains = template.find_resources("AWS::OpenSearchService::Domain")
    (domain,) = domains.values()
    domain_name = domain["Properties"]["DomainName"]
    assert len(domain_name) <= 28


def test_domain_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::OpenSearchService::Domain", {"Tags": Match.array_with([tag])}
        )


def test_access_policy_is_on_the_domain_not_a_custom_resource(config):
    """floci's CloudFormation doesn't create OpenSearch domains, so the L2's
    Custom::OpenSearchAccessPolicy (an API call after creation) can't work
    there - the policy is set as the domain's own AccessPolicies instead."""
    template = _synth(config)
    template.resource_count_is("Custom::OpenSearchAccessPolicy", 0)
    template.has_resource_properties(
        "AWS::OpenSearchService::Domain",
        {
            "AccessPolicies": {
                "Statement": [
                    Match.object_like(
                        {
                            "Effect": "Allow",
                            "Action": "es:*",
                            "Resource": "*",
                            "Principal": {"AWS": Match.any_value()},
                        }
                    )
                ],
                "Version": "2012-10-17",
            }
        },
    )
