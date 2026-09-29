"""Module 36 - SES: an email identity to verify a sender address.

AWS docs used while writing this module:
- EmailIdentity construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ses/EmailIdentity.html
- Identity class: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ses/Identity.html
- Verifying an identity in Amazon SES: https://docs.aws.amazon.com/ses/latest/dg/verify-addresses-and-domains.html
- Request production access (moving out of the sandbox): https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html

`ses.EmailIdentity` is a stable CDK L2 construct (confirmed against the API
reference above and the `aws-cdk-lib` v2.271.0 source), so this module uses
it instead of the L1 `ses.CfnEmailIdentity`. See README.md for the SES
sandbox limitation every new AWS account starts with.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ses as ses
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "SesStack"


class SesStack(Stack):
    """One SES email identity, verified as a single sender address.

    `ses.Identity.email(...)` verifies a single address (the recipient gets
    a confirmation link) - the simplest possible identity to teach with. A
    real production setup usually verifies a whole domain instead
    (`ses.Identity.domain(...)`, or `ses.Identity.public_hosted_zone(...)`
    when the domain's DNS is already a Route 53 hosted zone in this
    account), so it can send from any address `@that-domain`. See
    README.md for why a real account cannot actually *send* mail with only
    this stack deployed (the SES sandbox).
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

        # A generic, non-company placeholder address - see CLAUDE.md
        # section 1 ("never a real company's internals"). Replace with a
        # real address you control before verifying against real AWS.
        sender_address = "noreply@example.com"
        self.email_identity = ses.EmailIdentity(
            self,
            "EmailIdentity",
            identity=ses.Identity.email(sender_address),
        )
        apply_name_tag(
            self.email_identity,
            resource_name(config.product, config.environment, "ses", "sender-identity"),
        )


STACK_CLASS = SesStack
