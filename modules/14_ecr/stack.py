"""Module 14 - ECR: a private container image repository.

AWS docs used while writing this module:
- Repository construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecr/Repository.html
- Amazon ECR - What is Amazon ECR: https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html
- Image scanning: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_ecr as ecr
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "EcrStack"


class EcrStack(Stack):
    """One private ECR repository, with scan-on-push and DESTROY cleanup.

    `empty_on_delete=True` - confirmed present on the `Repository` construct's
    constructor in the installed `aws-cdk-lib==2.271.0` (inspected directly;
    see README.md "Notes and cautions") - lets CDK empty the repository of
    images before deleting it on `cdk destroy`. Without it, a repository that
    still has images in it cannot be deleted by CloudFormation at all, and
    needs a manual `aws ecr batch-delete-image` (or console) cleanup first.
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

        repository_name = resource_name(config.product, config.environment, "ecr", "app")
        self.repository = ecr.Repository(
            self,
            "AppRepository",
            repository_name=repository_name,
            image_scan_on_push=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            empty_on_delete=True,
        )
        apply_name_tag(self.repository, repository_name)


STACK_CLASS = EcrStack
