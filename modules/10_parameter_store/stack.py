"""Module 10 - Systems Manager Parameter Store: a free-tier String parameter.

AWS docs used while writing this module:
- StringParameter construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ssm/StringParameter.html
- Parameter Store naming requirements: https://docs.aws.amazon.com/systems-manager/latest/userguide/sysman-paramstore-su-create.html#sysman-paramstore-su-create-cli
- AWS::SSM::Parameter (confirms "Parameters of type SecureString are not
  supported by AWS CloudFormation"): https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-ssm-parameter.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from shared.config import AppConfig
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "ParameterStoreStack"


class ParameterStoreStack(Stack):
    """One free-tier (Standard) String parameter under a "/"-hierarchy name.

    Parameter Store's own naming convention groups parameters with a `/`
    hierarchy (`/product/environment/app/setting`) rather than this
    repository's usual `-`-separated `resource_name()` convention - see
    "Notes and cautions" in README.md for why that is a deliberate,
    documented exception, not a naming-policy violation. `config.product`
    and `config.environment` still come from `shared.config.AppConfig`, not
    a hardcoded value - only the `/` structure and the `"app"`/`"greeting"`
    path segments are this module's own choice, same as any other module's
    resource-purpose segment.

    `tier=ssm.ParameterTier.STANDARD` is the free tier (no per-parameter
    charge, up to 10,000 parameters per account/Region, 4 KB value limit) -
    see the naming-requirements link above for the `Advanced`/
    `Intelligent-Tiering` tiers this module does not use.

    This module does **not** create a SecureString-type parameter: neither
    `aws_cdk.aws_ssm.StringParameter` (this L2 construct's own docstring
    says so directly) nor the underlying `AWS::SSM::Parameter`
    CloudFormation resource (see the CloudFormation reference link above)
    supports *creating* one - SecureString parameters can only be created
    outside of CloudFormation (console, CLI, or `boto3`) and then
    *referenced* from CDK with
    `StringParameter.from_secure_string_parameter_attributes(...)`, which
    imports an existing parameter rather than provisioning a new one. That
    is out of scope for a "creates a deployable resource" module, so this
    module sticks to the Standard String type it can actually check into
    documentation without guessing.
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

        parameter_name = f"/{config.product}/{config.environment}/app/greeting"
        self.parameter = ssm.StringParameter(
            self,
            "GreetingParameter",
            parameter_name=parameter_name,
            string_value="Hello from learning-cdk-python!",
            description=(
                f"Example configuration value for the {config.product} learning path "
                "- see modules/10_parameter_store/README.md."
            ),
            tier=ssm.ParameterTier.STANDARD,
        )
        apply_name_tag(self.parameter, parameter_name)


STACK_CLASS = ParameterStoreStack
