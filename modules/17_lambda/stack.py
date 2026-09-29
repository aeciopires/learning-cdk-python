"""Module 17 - Lambda: one inline-code function, dependency-free.

AWS docs used while writing this module:
- Function construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Function.html
- Code (Code.from_inline): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Code.html
- Runtime: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_lambda/Runtime.html
- AWS Lambda - What is Lambda: https://docs.aws.amazon.com/lambda/latest/dg/welcome.html
- Working with the AWS CDK in Python (aliasing `aws_lambda` because `lambda`
  is a Python keyword): https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html#python-cdk-idioms

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "LambdaStack"

# A short, literal handler, passed as a string via Code.from_inline. This
# keeps this module dependency-free and Docker-bundling-free, which matters
# for a beginner's first Lambda function - see README.md "Notes and
# cautions" and the References section for what a real function with
# third-party dependencies needs instead (asset bundling, out of scope here).
_HANDLER_CODE = """
def handler(event, context):
    return {"statusCode": 200, "body": "hello from learning-cdk-python"}
"""


class LambdaStack(Stack):
    """One Lambda function (`Code.from_inline`) plus its own execution role.

    The execution role is built the same way as `modules/01_iam`: an
    `iam.Role` assumed only by the Lambda service (`lambda.amazonaws.com`),
    plus the AWS-managed `AWSLambdaBasicExecutionRole` policy - the minimum
    CloudWatch Logs permissions every Lambda function needs to run at all.
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

        role_name = resource_name(config.product, config.environment, "role", "lambda-execution")
        self.execution_role = iam.Role(
            self,
            "ExecutionRole",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for this module's example Lambda function.",
            max_session_duration=Duration.hours(1),
        )
        self.execution_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )
        apply_name_tag(self.execution_role, role_name)

        function_name = resource_name(config.product, config.environment, "lambda", "hello")
        self.function = lambda_.Function(
            self,
            "HelloFunction",
            function_name=function_name,
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=lambda_.Code.from_inline(_HANDLER_CODE),
            role=self.execution_role,
            timeout=Duration.seconds(10),
        )
        apply_name_tag(self.function, function_name)


STACK_CLASS = LambdaStack
