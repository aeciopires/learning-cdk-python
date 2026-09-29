"""Module 02 - STS: a role built to be assumed via sts:AssumeRole.

AWS Security Token Service (STS) has no CloudFormation/CDK resource of its
own - `sts:AssumeRole`, `sts:GetCallerIdentity`, and friends are runtime API
calls, not provisioned infrastructure (see "Notes and cautions" in
README.md). What *is* infrastructure, and what this stack creates, is the
IAM role's trust policy: the part of a role that says which principals are
allowed to call `sts:AssumeRole` against it.

AWS docs used while writing this module:
- Role construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html
- AccountPrincipal: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/AccountPrincipal.html
- Temporary security credentials in IAM: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html
- The AssumeRole API: https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRole.html

See README.md in this directory for how to actually call sts:AssumeRole
against the role this stack creates.
"""

from __future__ import annotations

from aws_cdk import Aws, Duration, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "StsStack"


class StsStack(Stack):
    """A role assumable, via STS, by any principal in the same account.

    `iam.AccountPrincipal(Aws.ACCOUNT_ID)` - not a hardcoded account number,
    see shared/config.py and CLAUDE.md section 6 - means "any IAM user or
    role in this account that itself has an `sts:AssumeRole` permissions
    policy naming this role's ARN may assume it". A real cross-account
    version of this pattern would use the *other* account's id instead, and
    almost always adds an `ExternalId` condition (included below even for
    the same-account case, as the pattern to copy) - see the "confused
    deputy" note in README.md.
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

        role_name = resource_name(config.product, config.environment, "role", "assume-demo")
        external_id = resource_name(config.product, config.environment, "external-id")

        self.assumable_role = iam.Role(
            self,
            "AssumableRole",
            role_name=role_name,
            assumed_by=iam.AccountPrincipal(Aws.ACCOUNT_ID).with_conditions(
                {"StringEquals": {"sts:ExternalId": external_id}}
            ),
            description="Assumed via sts:AssumeRole - see modules/02_sts/README.md.",
            max_session_duration=Duration.hours(1),
        )
        apply_name_tag(self.assumable_role, role_name)

        # A trivial, harmless permission so `aws sts assume-role` followed by
        # a real API call has something safe to demonstrate.
        self.assumable_role.add_to_policy(
            iam.PolicyStatement(
                sid="ListBucketsOnly",
                effect=iam.Effect.ALLOW,
                actions=["s3:ListAllMyBuckets"],
                resources=["*"],
            )
        )


STACK_CLASS = StsStack
