"""Module 01 - IAM: a role and a least-privilege policy.

AWS docs used while writing this module:
- Role construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/Role.html
- PolicyStatement: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/PolicyStatement.html
- IAM roles: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
- IAM best practices (prefer roles over long-lived users): https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Duration, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "IamStack"


class IamStack(Stack):
    """One IAM role a Lambda function can assume, plus one least-privilege policy.

    This intentionally does not create an `iam.User`. AWS's own IAM best
    practices guide recommends roles (temporary, automatically-rotated
    credentials assumed via STS - see module 02) over IAM users with
    long-lived access keys wherever the caller can be a role instead - see
    the "IAM best practices" link above.
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

        role_name = resource_name(config.product, config.environment, "role", "app-task")
        self.app_role = iam.Role(
            self,
            "AppRole",
            role_name=role_name,
            # Only the Lambda service itself is allowed to assume this role -
            # this is the trust policy. Module 02 (STS) builds a role trusted
            # by a *principal* (an account/role) instead, to demonstrate the
            # sts:AssumeRole call a human or another service would make.
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for the learning path's example Lambda workloads.",
            max_session_duration=Duration.hours(1),
        )
        apply_name_tag(self.app_role, role_name)

        # AWS-managed policy: the minimum CloudWatch Logs permissions every
        # Lambda function needs to run at all.
        self.app_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        # A least-privilege, customer-managed policy: read-only access to
        # objects under one prefix of one bucket, not s3:* on every bucket.
        # The bucket does not have to exist yet for this policy to synth -
        # see modules/12_s3 for a stack that creates one.
        read_only_bucket_arn = self.format_arn(
            service="s3",
            resource=resource_name(config.product, config.environment, "s3", "app-data"),
            region="",
            account="",
        )
        self.read_only_policy = iam.ManagedPolicy(
            self,
            "S3ReadOnlyPolicy",
            managed_policy_name=resource_name(config.product, config.environment, "policy", "s3-read-only"),
            description="Read-only access to one bucket's objects, nothing else.",
            statements=[
                iam.PolicyStatement(
                    sid="ListBucket",
                    effect=iam.Effect.ALLOW,
                    actions=["s3:ListBucket"],
                    resources=[read_only_bucket_arn],
                ),
                iam.PolicyStatement(
                    sid="ReadObjects",
                    effect=iam.Effect.ALLOW,
                    actions=["s3:GetObject"],
                    resources=[f"{read_only_bucket_arn}/*"],
                ),
            ],
        )
        self.app_role.add_managed_policy(self.read_only_policy)


STACK_CLASS = IamStack
