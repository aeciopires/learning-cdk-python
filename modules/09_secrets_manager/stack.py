"""Module 09 - Secrets Manager: an auto-generated secret, never a hardcoded value.

AWS docs used while writing this module:
- Secret construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_secretsmanager/Secret.html
- SecretStringGenerator construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_secretsmanager/SecretStringGenerator.html
- Secrets Manager concepts: https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html
- Deleting a secret (the recovery window): https://docs.aws.amazon.com/secretsmanager/latest/userguide/delete-secret.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

import json

from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "SecretsManagerStack"


class SecretsManagerStack(Stack):
    """One secret with an auto-generated password - never a real-looking hardcoded value.

    `generate_secret_string=secretsmanager.SecretStringGenerator(...)` asks
    Secrets Manager itself to generate the random value at deploy time - the
    CDK code and the CloudFormation template it produces never contain an
    actual secret value, only the *shape* of one (a JSON template with a
    `username` field and a `password` field Secrets Manager fills in). This
    is the pattern to copy any time a module needs a password/API key/token:
    never type a real-looking value into source code.

    `removal_policy=RemovalPolicy.DESTROY` is what lets `cdk destroy` remove
    this secret in this learning module - see "Notes and cautions" in
    README.md for what that removal_policy does and does not skip on real
    AWS (it does not skip Secrets Manager's own recovery window; there is no
    `force_delete_without_recovery` construct property on `Secret` to opt
    out of it from CDK - that flag exists only on the `DeleteSecret` API/CLI
    call, outside of CloudFormation's control).
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

        secret_name = resource_name(config.product, config.environment, "secret", "app-credential")
        self.secret = secretsmanager.Secret(
            self,
            "AppSecret",
            secret_name=secret_name,
            description=(
                f"Example application credential for the {config.product} learning path "
                "- see modules/09_secrets_manager/README.md."
            ),
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({"username": "app_user"}),
                generate_string_key="password",
                password_length=32,
                exclude_punctuation=True,
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )
        apply_name_tag(self.secret, secret_name)


STACK_CLASS = SecretsManagerStack
