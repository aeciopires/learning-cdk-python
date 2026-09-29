"""Module 29 - Step Functions: a small state machine with no external dependencies.

AWS docs used while writing this module:
- StateMachine construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_stepfunctions/StateMachine.html
- DefinitionBody construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_stepfunctions/DefinitionBody.html
- Pass, Wait, Choice, Condition, Result: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_stepfunctions/
- AWS Step Functions - Amazon States Language: https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html

`StateMachine.__init__` in aws-cdk-lib 2.271.0 still accepts both
`definition=` and `definition_body=`, but the API reference marks
`definition` "(deprecated)" in its own docstring and tells you to use
`definition_body` instead - confirmed by introspecting the installed
`aws_cdk.aws_stepfunctions.StateMachine.__init__` signature and its parameter
docs before writing this module. This stack therefore uses
`definition_body=sfn.DefinitionBody.from_chainable(chain)`, the current,
non-deprecated way to attach a state machine's definition.

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Duration, Stack
from aws_cdk import aws_stepfunctions as sfn
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "StepFunctionsStack"


class StepFunctionsStack(Stack):
    """A 4-state order-shipping workflow: Pass -> Wait -> Choice -> Pass.

    No Lambda function or other external service is involved - every state
    here is a Step Functions built-in state, so the whole module is
    deployable and testable with zero other AWS resources:

    - `sfn.Pass` ("ReceiveOrder") - a no-op state that simply passes its
      input through, standing in for "an order was received".
    - `sfn.Wait` ("WaitForProcessing") - pauses the execution for a fixed
      duration (`sfn.WaitTime.duration(...)`), standing in for a processing
      delay.
    - `sfn.Choice` ("IsExpressShipping") - branches on a field of the
      execution's input (`$.shippingType`) using `sfn.Condition
      .string_equals`, to either the express or the standard `Pass` state.
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

        receive_order = sfn.Pass(
            self,
            "ReceiveOrder",
            comment="Simulates receiving a new order as the execution's input.",
        )

        wait_for_processing = sfn.Wait(
            self,
            "WaitForProcessing",
            time=sfn.WaitTime.duration(Duration.seconds(5)),
            comment="Simulates a short processing delay before shipping.",
        )

        express_order = sfn.Pass(
            self,
            "ExpressOrder",
            comment="Reached when input.shippingType == 'express'.",
            result=sfn.Result.from_object({"priority": "express"}),
        )

        standard_order = sfn.Pass(
            self,
            "StandardOrder",
            comment="Reached for any other shippingType.",
            result=sfn.Result.from_object({"priority": "standard"}),
        )

        is_express_shipping = sfn.Choice(self, "IsExpressShipping")
        is_express_shipping.when(
            sfn.Condition.string_equals("$.shippingType", "express"),
            express_order,
        )
        is_express_shipping.otherwise(standard_order)

        chain = receive_order.next(wait_for_processing).next(is_express_shipping)

        state_machine_name = resource_name(config.product, config.environment, "sfn", "order-workflow")
        self.state_machine = sfn.StateMachine(
            self,
            "OrderStateMachine",
            state_machine_name=state_machine_name,
            definition_body=sfn.DefinitionBody.from_chainable(chain),
            tracing_enabled=False,
        )
        apply_name_tag(self.state_machine, state_machine_name)


STACK_CLASS = StepFunctionsStack
