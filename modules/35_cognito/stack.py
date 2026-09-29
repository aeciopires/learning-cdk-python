"""Module 35 - Cognito: a user pool and a public app client.

AWS docs used while writing this module:
- UserPool construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cognito/UserPool.html
- UserPoolClient construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cognito/UserPoolClient.html
- What Is Amazon Cognito: https://docs.aws.amazon.com/cognito/latest/developerguide/what-is-amazon-cognito.html
- Cognito user pools: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html
- Cognito identity pools: https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-identity.html

See README.md in this directory for the full explanation, including the
difference between user pools and identity pools.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_cognito as cognito
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "CognitoStack"


class CognitoStack(Stack):
    """A Cognito user pool (sign-up/sign-in) plus one public app client.

    This module only covers the *user pool* side of Cognito - see
    README.md for why identity pools (federated AWS credentials) are a
    separate concept this module does not create.
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

        user_pool_name = resource_name(config.product, config.environment, "cognito", "users")
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=user_pool_name,
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True)
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            # DESTROY (not the L2 default of RETAIN) so `cdk destroy` fully
            # cleans up this learning-path stack against floci or a real
            # sandbox account - see modules/03_vpc's README for the same
            # reasoning applied to other stateful resources in this repo.
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        apply_name_tag(self.user_pool, user_pool_name)

        # A "public" client: no client secret, suitable for a browser or
        # mobile app that cannot keep a secret confidential (it authenticates
        # end users directly against the user pool, e.g. via the hosted UI
        # or the SDK's sign-up/sign-in calls).
        client_name = resource_name(config.product, config.environment, "cognito", "web-client")
        self.user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=self.user_pool,
            user_pool_client_name=client_name,
            generate_secret=False,
        )
        apply_name_tag(self.user_pool_client, client_name)


STACK_CLASS = CognitoStack
