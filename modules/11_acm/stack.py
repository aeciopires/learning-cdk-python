"""Module 11 - ACM: a DNS-validated public certificate for a placeholder domain.

AWS docs used while writing this module:
- Certificate construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_certificatemanager/Certificate.html
- CertificateValidation construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_certificatemanager/CertificateValidation.html
- Requesting a public certificate (DNS validation): https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html
- ACM pricing (public certificates are free; you pay for the resources that use them): https://aws.amazon.com/certificate-manager/pricing/

See README.md in this directory for the full explanation, including why
this certificate is safe to deploy against real AWS as-is even though it
will sit in "Pending validation" forever.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_certificatemanager as acm
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "AcmStack"


class AcmStack(Stack):
    """One public ACM certificate for a placeholder domain, validated via DNS.

    `acm.Certificate` has no `certificate_name`-style physical name AWS
    itself recognizes - ACM identifies a certificate by its ARN, not a
    user-chosen name (see `CertificateProps.certificate_name`'s own
    docstring in the installed aws-cdk-lib package: "Since the Certificate
    resource doesn't support providing a physical name, the value provided
    here will be recorded in the `Name` tag"). This module still sets it,
    for a readable console label, and calls `apply_name_tag()` afterward as
    every module in this repository does - the two are redundant here
    (`certificate_name` already writes the `Name` tag), which is harmless
    and keeps this module's shape consistent with every other one.

    `validation=acm.CertificateValidation.from_dns()` (no hosted zone
    argument) means DNS records must be added *manually* - see
    "Notes and cautions" in README.md for exactly what that means on real
    AWS (the certificate sits in "Pending validation" forever unless you
    actually own `f"{config.product}.example.com"` and add the CNAME ACM
    asks for, which nobody deploying this learning path will) versus on
    floci, where validation is emulated and the certificate is issued
    immediately.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: AppConfig,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        apply_standard_tags(self, tags=config.to_standard_tags())

        certificate_name = resource_name(config.product, config.environment, "acm", "app")
        domain_name = f"{config.product}.example.com"

        self.certificate = acm.Certificate(
            self,
            "AppCertificate",
            domain_name=domain_name,
            certificate_name=certificate_name,
            validation=acm.CertificateValidation.from_dns(),
        )
        apply_name_tag(self.certificate, certificate_name)


STACK_CLASS = AcmStack
