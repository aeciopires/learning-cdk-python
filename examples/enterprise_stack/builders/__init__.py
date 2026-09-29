"""The one place every resource builder this example knows about is listed.

Adding a 15th resource: write `builders/whatever_builder.py` (copy the
shape of any file in this package), import its class below, add one
`registry.register(...)` line. Nothing else in this package, `stack.py`,
or `app.py` changes - that is the Open/Closed principle in effect, see
../README.md.

Alternative: importing builders from separately-versioned packages
--------------------------------------------------------------------
Every import below is a *local file* in this same repository (a
"monorepo" layout - all 14 builders released together, on one lifecycle).
Nothing about `build_default_registry()` requires that: it only ever
touches the `ResourceBuilder` abstraction (`.key`, `.depends_on`,
`.build()` - see `core/resource_builder.py`), never anything specific to
how a concrete class's module got onto disk. So if, say, the networking
team wanted to own `vpc`/`alb`/`nlb` in their own git repository, released
under their own Semantic Versioning (https://semver.org/) schedule instead
of this repository's, the only change needed *here* is which line imports
`VpcResourceBuilder` - for example:

    from acme_cdk_vpc_builder import VpcResourceBuilder   # installed package,
                                                            # pinned in pyproject.toml
    # instead of:
    from .vpc_builder import VpcResourceBuilder            # local file, this repo

...with the registration loop below completely unchanged either way. See
../README.md, section 13 ("Alternative: one git repository (and one
release cadence) per builder") for: why a team might want this, exactly
how to pin such a package with uv's `[tool.uv.sources]` (a git URL + a
semver tag, or a private index such as AWS CodeArtifact), and the
trade-offs against the single-repository layout this example actually
uses. That section is written from the current, single-repository
imports below - nothing in this file has actually been split out.
"""

from __future__ import annotations

from examples.enterprise_stack.core.resource_registry import ResourceRegistry

from .acm_builder import AcmResourceBuilder
from .alb_builder import AlbResourceBuilder
from .dynamodb_builder import DynamoDbResourceBuilder
from .ec2_builder import Ec2ResourceBuilder
from .ecr_builder import EcrResourceBuilder
from .ecs_builder import EcsResourceBuilder
from .iam_builder import IamResourceBuilder
from .kms_builder import KmsResourceBuilder
from .lambda_builder import LambdaResourceBuilder
from .nlb_builder import NlbResourceBuilder
from .s3_builder import S3ResourceBuilder
from .sns_builder import SnsResourceBuilder
from .sqs_builder import SqsResourceBuilder
from .vpc_builder import VpcResourceBuilder


def build_default_registry() -> ResourceRegistry:
    registry = ResourceRegistry()
    for builder in (
        IamResourceBuilder(),
        VpcResourceBuilder(),
        EcrResourceBuilder(),
        KmsResourceBuilder(),
        S3ResourceBuilder(),
        SqsResourceBuilder(),
        SnsResourceBuilder(),
        DynamoDbResourceBuilder(),
        LambdaResourceBuilder(),
        Ec2ResourceBuilder(),
        AcmResourceBuilder(),
        EcsResourceBuilder(),
        AlbResourceBuilder(),
        NlbResourceBuilder(),
    ):
        registry.register(builder)
    return registry
