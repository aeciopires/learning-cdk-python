"""ACM: same `acm.Certificate` call verified in modules/11_acm/stack.py."""

from __future__ import annotations

from aws_cdk import aws_certificatemanager as acm
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class AcmResourceBuilder(ResourceBuilder):
    key = "acm"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        certificate_name = resource_name(config.product, config.environment, cell, "acm", "app")
        domain_name = f"{config.product}.example.com"
        certificate = acm.Certificate(
            scope,
            "AppCertificate",
            domain_name=domain_name,
            certificate_name=certificate_name,
            validation=acm.CertificateValidation.from_dns(),
        )
        apply_name_tag(certificate, certificate_name)

        context.shared["acm_certificate"] = certificate
