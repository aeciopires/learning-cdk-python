"""Module 43 - Resource Groups: a tag-based group of every `product`-tagged resource.

AWS docs used while writing this module:
- CfnGroup (L1) construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_resourcegroups/CfnGroup.html
- AWS::ResourceGroups::Group CloudFormation resource: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-resourcegroups-group.html
- Build queries and groups in AWS Resource Groups: https://docs.aws.amazon.com/ARG/latest/userguide/gettingstarted-query.html
- Resource Groups Tagging API reference (read-only, no CDK/CloudFormation resource - see README.md): https://docs.aws.amazon.com/resourcegroupstagging/latest/APIReference/Welcome.html

There is **no CDK L2 construct for Resource Groups** in the current stable
`aws-cdk-lib` - this module uses the L1 `resourcegroups.CfnGroup`, a 1:1
mapping to the `AWS::ResourceGroups::Group` CloudFormation resource (every
nested property class/field below was verified against that resource's
CloudFormation documentation, linked above).
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_resourcegroups as resourcegroups
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "ResourceGroupTaggingStack"


class ResourceGroupTaggingStack(Stack):
    """A dynamic resource group: every resource in this account/region tagged `product=<config.product>`.

    `resource_type_filters=["AWS::AllSupported"]` means "any resource type
    Resource Groups can query", not just the ones this repository's other
    modules happen to create - the group's membership is computed live by
    AWS, not a fixed list this stack maintains. See README.md for how the
    separate, read-only Resource Groups Tagging API complements this
    console-facing group.
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

        group_name = resource_name(config.product, config.environment, "resource-group", "by-product")
        self.group = resourcegroups.CfnGroup(
            self,
            "ResourceGroup",
            name=group_name,
            description=f"Every resource tagged product {config.product} in this account and region.",
            resource_query=resourcegroups.CfnGroup.ResourceQueryProperty(
                type="TAG_FILTERS_1_0",
                query=resourcegroups.CfnGroup.QueryProperty(
                    resource_type_filters=["AWS::AllSupported"],
                    tag_filters=[
                        resourcegroups.CfnGroup.TagFilterProperty(
                            key="product",
                            values=[config.product],
                        )
                    ],
                ),
            ),
        )
        apply_name_tag(self.group, group_name)


STACK_CLASS = ResourceGroupTaggingStack
