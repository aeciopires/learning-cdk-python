"""Module 37 - WAF (WAFv2): a regional web ACL with one AWS-managed rule group.

AWS docs used while writing this module:
- CfnWebACL (L1) construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_wafv2/CfnWebACL.html
- AWS::WAFv2::WebACL CloudFormation resource: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-wafv2-webacl.html
- How AWS WAF works (CLOUDFRONT scope must be created in us-east-1): https://docs.aws.amazon.com/waf/latest/developerguide/how-aws-waf-works.html
- AWS managed rule groups list: https://docs.aws.amazon.com/waf/latest/developerguide/aws-managed-rule-groups-list.html

There is **no CDK L2 construct for WAFv2** in the current stable
`aws-cdk-lib` - this module uses the L1 `wafv2.CfnWebACL`, a 1:1 mapping to
the `AWS::WAFv2::WebACL` CloudFormation resource (every nested property
class name and field below was verified against that resource's
CloudFormation documentation, linked above, since `Cfn*` constructs mirror
the CloudFormation property names exactly).
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_wafv2 as wafv2
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "WafStack"


class WafStack(Stack):
    """A REGIONAL web ACL that allows by default and runs AWS's common rule set.

    `scope="REGIONAL"` targets resources like an Application Load Balancer
    or API Gateway REST API in *this* region. The other valid scope,
    `"CLOUDFRONT"`, is a real AWS constraint this module does not use: a
    CLOUDFRONT-scoped web ACL must be created in `us-east-1` specifically,
    regardless of which region this stack's other resources live in - see
    the "How AWS WAF works" reference above.
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

        web_acl_name = resource_name(config.product, config.environment, "waf", "web-acl")
        metric_name = resource_name(config.product, config.environment, "waf", "metric")

        self.web_acl = wafv2.CfnWebACL(
            self,
            "WebAcl",
            name=web_acl_name,
            scope="REGIONAL",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                sampled_requests_enabled=True,
                cloud_watch_metrics_enabled=True,
                metric_name=metric_name,
            ),
            rules=[
                wafv2.CfnWebACL.RuleProperty(
                    name="AwsManagedRulesCommonRuleSet",
                    priority=0,
                    statement=wafv2.CfnWebACL.StatementProperty(
                        managed_rule_group_statement=wafv2.CfnWebACL.ManagedRuleGroupStatementProperty(
                            vendor_name="AWS",
                            name="AWSManagedRulesCommonRuleSet",
                        )
                    ),
                    # A managed rule group's own rules already carry an
                    # action; `override_action=none` means "keep each rule's
                    # own action (mostly Block)" instead of overriding every
                    # one to just Count matches.
                    override_action=wafv2.CfnWebACL.OverrideActionProperty(none={}),
                    visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                        sampled_requests_enabled=True,
                        cloud_watch_metrics_enabled=True,
                        metric_name=resource_name(
                            config.product, config.environment, "waf", "common-rule-set"
                        ),
                    ),
                )
            ],
        )
        apply_name_tag(self.web_acl, web_acl_name)


STACK_CLASS = WafStack
