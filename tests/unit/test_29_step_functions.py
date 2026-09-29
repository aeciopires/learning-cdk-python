"""Unit tests for modules/29_step_functions. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

StepFunctionsStack = stack_class("29_step_functions")


def _synth(config):
    app = cdk.App()
    stack = StepFunctionsStack(app, "TestStepFunctionsStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_state_machine(config):
    template = _synth(config)
    template.resource_count_is("AWS::StepFunctions::StateMachine", 1)


def test_definition_contains_the_choice_state(config):
    """The Choice state this module exists to teach - see README.md."""
    template = _synth(config)
    template.has_resource_properties(
        "AWS::StepFunctions::StateMachine",
        {
            "DefinitionString": Match.string_like_regexp(
                r".*IsExpressShipping.*"
            )
        },
    )


def test_definition_branches_on_shipping_type(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::StepFunctions::StateMachine",
        {
            "DefinitionString": Match.string_like_regexp(
                r'.*"Variable":"\$\.shippingType","StringEquals":"express".*'
            )
        },
    )


def test_state_machine_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::StepFunctions::StateMachine", {"Tags": Match.array_with([tag])}
        )
