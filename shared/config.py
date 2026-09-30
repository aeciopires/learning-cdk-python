"""Account/region- and tag-value resolution, kept out of every stack.

Every value here is read from the environment so the same code deploys to
any AWS account/region without editing a single file - see REQUIREMENTS.md
("Flexible account and region") and the AWS CDK "Environments" guide:
https://docs.aws.amazon.com/cdk/v2/guide/environments.html
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import aws_cdk as cdk

from shared.tagging import StandardTags

# The only accepted values for the `environment` tag and the environment
# segment of every resource name - short, fixed-length names keep physical
# names (which often have tight length limits) short and consistent. See
# REQUIREMENTS.md, "Tagging policy".
ENVIRONMENTS: tuple[str, ...] = ("dev", "stg", "prd")

# Long names people commonly type out of habit, mapped to the short name
# to suggest instead - used only to build a helpful error message.
_LONG_ENVIRONMENT_NAMES = {
    "development": "dev",
    "staging": "stg",
    "stage": "stg",
    "prod": "prd",
    "production": "prd",
}


def validate_environment(name: str) -> str:
    """Return `name` normalized (stripped, lower-cased) if it is in `ENVIRONMENTS`.

    Raises `ValueError` otherwise, suggesting the short name when `name` is
    a common long form (e.g. "staging" -> "stg", "prod" -> "prd").
    """
    normalized = name.strip().lower()
    if normalized in ENVIRONMENTS:
        return normalized
    hint = _LONG_ENVIRONMENT_NAMES.get(normalized)
    suggestion = f' - did you mean "{hint}"?' if hint else ""
    raise ValueError(
        f"Invalid environment {name!r}: must be one of {', '.join(ENVIRONMENTS)}{suggestion}"
    )


def get_environment() -> cdk.Environment | None:
    """Build a `cdk.Environment` from the standard CDK/AWS CLI env vars.

    - `CDK_DEFAULT_ACCOUNT` / `CDK_DEFAULT_REGION` are set automatically by
      the CDK CLI from your current AWS CLI credentials/profile when you run
      `cdk synth`/`cdk deploy` (see the CDK "Environments" guide above).
    - `AWS_ACCOUNT_ID` / `AWS_REGION` are accepted as explicit overrides, for
      example when targeting the floci local emulator (see REQUIREMENTS.md).

    Returns `None` (an "environment-agnostic" stack, deployable to any
    account/region, with the limitations described in the CDK guide above)
    when nothing is set - this is what lets `cdk synth` run in CI or in this
    learning path without any AWS credentials configured at all.
    """
    account = os.getenv("CDK_DEFAULT_ACCOUNT") or os.getenv("AWS_ACCOUNT_ID")
    region = os.getenv("CDK_DEFAULT_REGION") or os.getenv("AWS_REGION")
    if not account and not region:
        return None
    return cdk.Environment(account=account, region=region)


@dataclass(frozen=True)
class AppConfig:
    """Tag values shared by every stack, resolved once in app.py.

    Every field maps directly to a mandatory tag in `shared/tagging.py`.
    Override any of them with the matching `CDK_*` environment variable
    before running `cdk synth`/`cdk deploy` - see .env.example.
    """

    product: str
    environment: str
    team_owner: str
    pci: bool
    cell_based: bool
    cell_id: str | None

    def to_standard_tags(self) -> StandardTags:
        return StandardTags(
            product=self.product,
            environment=self.environment,
            team_owner=self.team_owner,
            pci=self.pci,
            cell_based=self.cell_based,
            cell_id=self.cell_id,
        )


def load_app_config() -> AppConfig:
    cell_based = os.getenv("CDK_CELL_BASED", "false").strip().lower() == "true"
    return AppConfig(
        product=os.getenv("CDK_PRODUCT", "learning-cdk-python"),
        environment=validate_environment(os.getenv("CDK_ENVIRONMENT", "dev")),
        team_owner=os.getenv("CDK_TEAM_OWNER", "platform-engineering"),
        pci=os.getenv("CDK_PCI", "false").strip().lower() == "true",
        cell_based=cell_based,
        cell_id=(os.getenv("CDK_CELL_ID") or None) if cell_based else None,
    )
