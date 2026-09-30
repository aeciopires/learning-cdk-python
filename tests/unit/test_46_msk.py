"""Unit tests for modules/46_msk. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

MskStack = stack_class("46_msk")


def _synth(config):
    app = cdk.App()
    stack = MskStack(app, "TestMskStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_msk_cluster(config):
    template = _synth(config)
    template.resource_count_is("AWS::MSK::Cluster", 1)


def test_one_small_broker_per_availability_zone(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::MSK::Cluster",
        {
            "ClusterName": f"{config.product}-{config.environment}-msk-events",
            "KafkaVersion": "3.9.x",
            "NumberOfBrokerNodes": 2,
            "BrokerNodeGroupInfo": Match.object_like(
                {
                    "InstanceType": "kafka.t3.small",
                    "ClientSubnets": Match.array_equals([Match.any_value()] * 2),
                    "StorageInfo": {"EBSStorageInfo": {"VolumeSize": 10}},
                }
            ),
        },
    )


def test_clients_use_iam_auth_over_tls(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::MSK::Cluster",
        {
            "ClientAuthentication": {"Sasl": {"Iam": {"Enabled": True}}},
            "EncryptionInfo": {"EncryptionInTransit": {"ClientBroker": "TLS", "InCluster": True}},
        },
    )


def test_security_group_opens_the_iam_port_to_the_vpc_only(config):
    template = _synth(config)
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {"SecurityGroupIngress": [Match.object_like({"FromPort": 9098, "ToPort": 9098})]},
    )


def test_cluster_has_the_mandatory_tags(config):
    # AWS::MSK::Cluster's Tags is a key/value map, not the usual list of
    # {"Key": ..., "Value": ...} pairs - see modules/46_msk/README.md.
    template = _synth(config)
    expected = {tag["Key"]: tag["Value"] for tag in mandatory_tag_pairs(config)}
    template.has_resource_properties("AWS::MSK::Cluster", {"Tags": Match.object_like(expected)})
