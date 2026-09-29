"""IAM: one role, reused by LambdaResourceBuilder as its execution role.

Same `iam.Role`/`iam.ManagedPolicy` calls verified in
modules/01_iam/stack.py.
"""

from __future__ import annotations

from aws_cdk import Duration, Stack
from aws_cdk import aws_iam as iam
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag


class IamResourceBuilder(ResourceBuilder):
    key = "iam"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        role_name = resource_name(config.product, config.environment, cell, "role", "app-task")
        role = iam.Role(
            scope,
            "AppRole",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Shared execution role for this cell's Lambda workloads.",
            max_session_duration=Duration.hours(1),
        )
        apply_name_tag(role, role_name)
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        # Same ARN-by-convention approach as modules/01_iam/stack.py - it
        # works whether or not the "s3" resource is actually enabled for
        # this cell. A fuller implementation could instead inject the live
        # bucket construct from context.shared["s3_bucket"] when "s3" is
        # enabled (see the "Referencing resources" pattern in
        # docs/IMPORTING-EXISTING-RESOURCES.md) - left out here to keep
        # this builder's only hard dependency on nothing at all.
        read_only_bucket_arn = Stack.of(scope).format_arn(
            service="s3",
            resource=resource_name(config.product, config.environment, cell, "s3", "app-data"),
            region="",
            account="",
        )
        read_only_policy_name = resource_name(config.product, config.environment, cell, "policy", "s3-read-only")
        read_only_policy = iam.ManagedPolicy(
            scope,
            "S3ReadOnlyPolicy",
            managed_policy_name=read_only_policy_name,
            description="Read-only access to this cell's app-data bucket, nothing else.",
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
        role.add_managed_policy(read_only_policy)

        context.shared["iam_role"] = role
