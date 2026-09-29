"""Unit tests for modules/11_acm. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

AcmStack = stack_class("11_acm")


def _synth(config):
    app = cdk.App()
    stack = AcmStack(app, "TestAcmStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_certificate(config):
    template = _synth(config)
    template.resource_count_is("AWS::CertificateManager::Certificate", 1)


def test_certificate_uses_dns_validation(config):
    """The whole point of this module: DNS validation, not email validation."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::CertificateManager::Certificate", {"ValidationMethod": "DNS"}
    )


def test_domain_name_uses_the_product_placeholder_domain(config):
    template = _synth(config)
    expected_domain = f"{config.product}.example.com"
    template.has_resource_properties(
        "AWS::CertificateManager::Certificate", {"DomainName": expected_domain}
    )


def test_certificate_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::CertificateManager::Certificate", {"Tags": Match.array_with([tag])}
        )
