"""Loads environments/<name>.json - the *only* file that changes between
dev, stg, prd, or between adding a second "cell" - see ../README.md,
"Cells: replicating the same stack across environments, accounts, and
regions".
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import aws_cdk as cdk

ENVIRONMENTS_DIR = Path(__file__).resolve().parent.parent / "environments"


@dataclass(frozen=True)
class CellConfig:
    """One entry of one environment's config file - one deployable cell.

    `account`/`region` follow the same fallback this repository's own
    `shared/config.get_environment()` uses (see REQUIREMENTS.md section 9
    and https://docs.aws.amazon.com/cdk/v2/guide/environments.html):
    explicit value from the JSON file first, then the `CDK_DEFAULT_*`
    variables the CDK CLI sets from your AWS credentials, then
    environment-agnostic (deployable to any account/region, with that
    approach's documented limitations).
    """

    cell_id: str
    account: str | None
    region: str | None
    enabled_resources: tuple[str, ...]

    @property
    def env(self) -> cdk.Environment | None:
        if not self.account and not self.region:
            return None
        return cdk.Environment(account=self.account, region=self.region)


def load_environment(name: str) -> list[CellConfig]:
    """Read environments/<name>.json and return its list of cells.

    `name` is normally the `ENTERPRISE_ENVIRONMENT` environment variable
    (see app.py) - switching `dev` to `stg` to `prd` changes nothing
    in this package's Python code, only which JSON file gets read.
    """
    path = ENVIRONMENTS_DIR / f"{name}.json"
    if not path.exists():
        available = sorted(p.stem for p in ENVIRONMENTS_DIR.glob("*.json"))
        raise FileNotFoundError(
            f"No environment config at {path}. Available: {available} "
            "- see environments/dev.json for the expected shape."
        )

    raw = json.loads(path.read_text())
    return [
        CellConfig(
            cell_id=cell["cell_id"],
            account=cell.get("account") or os.getenv("CDK_DEFAULT_ACCOUNT"),
            region=cell.get("region") or os.getenv("CDK_DEFAULT_REGION"),
            enabled_resources=tuple(cell["enabled_resources"]),
        )
        for cell in raw["cells"]
    ]
