"""ECR: a private repository meant to hold a copy of the public
https://hub.docker.com/r/aeciopires/mytoolkit image - same `ecr.Repository`
call verified in modules/14_ecr/stack.py. `EcsResourceBuilder` (see
`ecs_builder.py`, `depends_on = ("vpc", "ecr")`) points its task
definition's container at this repository via
`ecs.ContainerImage.from_ecr_repository()`.

CloudFormation/CDK cannot pull an image from Docker Hub and push it into
ECR for you - that is a Docker operation, not an infrastructure one (the
same reason modules/14_ecr/README.md documents its own image push as a
manual step). Copy the image in once, after this resource is deployed:

    aws ecr get-login-password --region <region> | \\
        docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
    docker pull docker.io/aeciopires/mytoolkit:latest
    docker tag docker.io/aeciopires/mytoolkit:latest <account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest
    docker push <account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest

See ../README.md, "The ecr resource" for the exact command with this
cell's real repository name filled in, and section 12 for what happens if
`ecs` is enabled before an image has actually been pushed.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import aws_ecr as ecr
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag

#: The public image this repository is meant to hold a private copy of.
SOURCE_IMAGE = "docker.io/aeciopires/mytoolkit:latest"


class EcrResourceBuilder(ResourceBuilder):
    key = "ecr"

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""

        repository_name = resource_name(config.product, config.environment, cell, "ecr", "mytoolkit")
        repository = ecr.Repository(
            scope,
            "AppRepository",
            repository_name=repository_name,
            image_scan_on_push=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            empty_on_delete=True,
        )
        apply_name_tag(repository, repository_name)

        context.shared["ecr_repository"] = repository
