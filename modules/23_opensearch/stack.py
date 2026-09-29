"""Module 23 - Amazon OpenSearch Service: a single-node, single-AZ domain.

AWS docs used while writing this module:
- Domain construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_opensearchservice/Domain.html
- EngineVersion construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_opensearchservice/EngineVersion.html
  (checked directly against the installed aws-cdk-lib==2.271.0 source: the
  highest constant defined is `OPENSEARCH_3_7`, not marked deprecated - see
  README.md for how this was verified. This module uses `aws_opensearchservice`,
  not the older `aws_elasticsearch` module, which CLAUDE.md section 4
  explicitly calls out as the one to avoid.)
- CapacityConfig, EbsOptions, ZoneAwarenessConfig (all in the same module):
  https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_opensearchservice/
- AccountPrincipal construct (IAM): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_iam/AccountPrincipal.html
- Amazon OpenSearch Service - identity and access management: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/ac.html
- Amazon OpenSearch Service pricing (hourly per data node): https://aws.amazon.com/opensearch-service/pricing/

See README.md in this directory for the full explanation, deploy steps, and
the prominent real-AWS cost warning (an OpenSearch data node bills hourly
even at the smallest instance size) plus the floci-coverage caveat for this
particular service.
"""

from __future__ import annotations

from aws_cdk import Aws, RemovalPolicy, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_opensearchservice as opensearchservice
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "OpenSearchStack"


class OpenSearchStack(Stack):
    """One single-node OpenSearch domain, public (no VPC), access-scoped to this account.

    `zone_awareness` is left disabled and `capacity.data_nodes=1`: a single
    node in a single AZ is the cheapest possible OpenSearch domain, at the
    cost of no high availability - not a concern for a learning module, but
    exactly the wrong choice for anything production-facing.

    This domain is **not** placed inside a VPC. AWS supports both a public
    ("internet-facing", though still access-controlled) domain and a
    VPC-attached one; a public domain paired with an IAM-account-scoped
    `access_policies` statement is simpler to reason about for a first look
    at this service than adding VPC security group/subnet plumbing on top -
    see modules/03_vpc and modules/18_rds_mysql for what that plumbing looks
    like in modules that do need it. `iam.AccountPrincipal(Aws.ACCOUNT_ID)`
    (not a hardcoded account number - see CLAUDE.md section 6) scopes
    `es:*` to callers authenticated as this AWS account, not to the public
    internet at large.
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

        # Amazon OpenSearch Service domain names have a hard AWS-enforced
        # limit of 28 characters (see the "Domain naming" reference in
        # README.md) - shorter than this repository's usual
        # product-environment-service-purpose name for most product/
        # environment values. `resource_name()` still builds the full,
        # policy-compliant name first; it is truncated only as the very
        # last step, purely to satisfy this one service's hard limit -
        # see REQUIREMENTS.md section 8 on service-specific naming
        # constraints.
        domain_name = resource_name(config.product, config.environment, "search")[:28].rstrip("-")
        self.domain = opensearchservice.Domain(
            self,
            "Domain",
            domain_name=domain_name,
            version=opensearchservice.EngineVersion.OPENSEARCH_3_7,
            capacity=opensearchservice.CapacityConfig(
                data_node_instance_type="t3.small.search",
                data_nodes=1,
                master_nodes=0,
            ),
            ebs=opensearchservice.EbsOptions(volume_size=10),
            zone_awareness=opensearchservice.ZoneAwarenessConfig(enabled=False),
            access_policies=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[iam.AccountPrincipal(Aws.ACCOUNT_ID)],
                    actions=["es:*"],
                    resources=["*"],
                )
            ],
            removal_policy=RemovalPolicy.DESTROY,
        )
        apply_name_tag(self.domain, domain_name)


STACK_CLASS = OpenSearchStack
