"""Lambda: same `lambda_.Function` call verified in modules/17_lambda/stack.py
- except the execution role. modules/17_lambda creates its own; here,
`depends_on = ("iam",)` and the function reuses `context.shared["iam_role"]`
instead.

This is Dependency Inversion in practice: this builder depends on the
*abstraction* "something in context.shared that can be a Lambda execution
role" (typed `iam.IRole`), never on `IamResourceBuilder` the class. Swap in
any other builder that publishes an `iam_role` under that same key and this
file does not change.
"""

from __future__ import annotations

from aws_cdk import Duration
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag

_HANDLER_CODE = """
def handler(event, context):
    return {"statusCode": 200, "body": "hello from the enterprise_stack example"}
"""


class LambdaResourceBuilder(ResourceBuilder):
    key = "lambda"
    depends_on = ("iam",)

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        function_name = resource_name(config.product, config.environment, cell, "lambda", "hello")
        function = lambda_.Function(
            scope,
            "HelloFunction",
            function_name=function_name,
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="index.handler",
            code=lambda_.Code.from_inline(_HANDLER_CODE),
            role=context.shared["iam_role"],
            timeout=Duration.seconds(10),
        )
        apply_name_tag(function, function_name)

        context.shared["lambda_function"] = function
