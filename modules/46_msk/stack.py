"""Module 46 - MSK: a small, provisioned Amazon Managed Streaming for Apache Kafka cluster.

AWS docs used while writing this module:
- CfnCluster construct (L1 - see note below): https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_msk/CfnCluster.html
- AWS::MSK::Cluster (required: BrokerNodeGroupInfo, ClusterName (1-64
  characters), KafkaVersion, NumberOfBrokerNodes; Tags is a key/value map):
  https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-msk-cluster.html
- Supported Apache Kafka versions (3.9.x is marked "Recommended"): https://docs.aws.amazon.com/msk/latest/developerguide/supported-kafka-versions.html
- Broker sizes (kafka.t3.small is the smallest Standard broker, "for
  low-cost development"): https://docs.aws.amazon.com/msk/latest/developerguide/broker-instance-sizes.html
- Port information (IAM access control within AWS: port 9098): https://docs.aws.amazon.com/msk/latest/developerguide/port-info.html
- Amazon MSK pricing (hourly per broker, plus storage): https://aws.amazon.com/msk/pricing/

**L1-only note:** the stable `aws_cdk.aws_msk` module has **no L2 (curated)
construct** - only `Cfn*` classes. An L2 `Cluster` exists only in the
separate `aws-cdk.aws-msk-alpha` package, which this repository never uses
(CLAUDE.md section 4, point 3). This module therefore uses `CfnCluster`, a
1:1 mapping to the `AWS::MSK::Cluster` CloudFormation resource type.

See README.md in this directory for the full explanation, deploy steps, and
the real-AWS cost warning (MSK brokers bill hourly the moment they exist).
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_msk as msk
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "MskStack"

# Re-check the supported-versions page linked above before changing this:
# Kafka versions reach end of support on a published schedule. "3.9.x"
# (not "3.9.0") lets MSK apply patch releases without a version upgrade.
KAFKA_VERSION = "3.9.x"
BROKER_INSTANCE_TYPE = "kafka.t3.small"
BROKER_VOLUME_SIZE_GIB = 10
IAM_PORT = 9098  # brokers' port for IAM-authenticated clients inside AWS


class MskStack(Stack):
    """A dedicated 2-AZ VPC plus a 2-broker MSK cluster (one broker per AZ).

    Amazon MSK runs Apache Kafka for you: an append-only, partitioned log
    that producers write events to and consumers read from, at their own
    pace. The brokers are spread across the subnets in `client_subnets`,
    and the number of brokers must be a multiple of the number of subnets -
    so two subnets in two AZs, with one broker each, is the smallest layout.

    Security choices, all set explicitly so they're visible in the template:
    - Clients authenticate with IAM (`sasl.iam`), not a username/password -
      the same IAM permissions module 01 teaches decide who may produce or
      consume. IAM-authenticated clients connect on port 9098.
    - Traffic is encrypted between clients and brokers (`TLS`) and between
      brokers (`in_cluster=True`).
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "msk")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            ip_addresses=ec2.IpAddresses.cidr("10.46.0.0/16"),
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
        apply_name_tag(self.vpc, vpc_name)

        sg_name = resource_name(config.product, config.environment, "sg", "msk")
        self.security_group = ec2.SecurityGroup(
            self,
            "BrokerSecurityGroup",
            vpc=self.vpc,
            security_group_name=sg_name,
            description=f"Allows inbound Kafka with IAM auth ({IAM_PORT}) from within the VPC only.",
            allow_all_outbound=True,
        )
        self.security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(IAM_PORT),
            description="Kafka (IAM auth) from inside the VPC",
        )
        apply_name_tag(self.security_group, sg_name)

        subnet_ids = self.vpc.select_subnets(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED).subnet_ids

        cluster_name = resource_name(config.product, config.environment, "msk", "events")
        self.cluster = msk.CfnCluster(
            self,
            "Cluster",
            cluster_name=cluster_name,
            kafka_version=KAFKA_VERSION,
            # One broker per subnet (= per AZ) - see the class docstring.
            number_of_broker_nodes=len(subnet_ids),
            broker_node_group_info=msk.CfnCluster.BrokerNodeGroupInfoProperty(
                client_subnets=subnet_ids,
                instance_type=BROKER_INSTANCE_TYPE,
                security_groups=[self.security_group.security_group_id],
                storage_info=msk.CfnCluster.StorageInfoProperty(
                    ebs_storage_info=msk.CfnCluster.EBSStorageInfoProperty(
                        volume_size=BROKER_VOLUME_SIZE_GIB
                    )
                ),
            ),
            client_authentication=msk.CfnCluster.ClientAuthenticationProperty(
                sasl=msk.CfnCluster.SaslProperty(iam=msk.CfnCluster.IamProperty(enabled=True))
            ),
            encryption_info=msk.CfnCluster.EncryptionInfoProperty(
                encryption_in_transit=msk.CfnCluster.EncryptionInTransitProperty(
                    client_broker="TLS", in_cluster=True
                )
            ),
        )
        apply_name_tag(self.cluster, cluster_name)


STACK_CLASS = MskStack
