"""Unit tests for modules/16_eks. See docs/TESTING.md for how these work."""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

EksStack = stack_class("16_eks")


def _synth(config):
    app = cdk.App()
    stack = EksStack(app, "TestEksStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_cluster(config):
    """The EKS control plane is provisioned through a CDK custom resource, not a
    native `AWS::EKS::Cluster` CloudFormation resource - see the CDK API docs."""
    template = _synth(config)
    template.resource_count_is("Custom::AWSCDK-EKS-Cluster", 1)


def test_cluster_runs_kubernetes_1_36_with_no_managed_node_group(config):
    """The whole point of this module: a control-plane-only cluster
    (`default_capacity=0`), so it never bills for EC2 worker nodes."""
    template = _synth(config)
    template.has_resource_properties(
        "Custom::AWSCDK-EKS-Cluster",
        {"Config": Match.object_like({"version": "1.36"})},
    )
    # No managed node group / Auto Scaling Group of worker nodes exists.
    template.resource_count_is("AWS::AutoScaling::AutoScalingGroup", 0)


def test_cluster_vpc_spans_two_availability_zones(config):
    """EKS requires subnets in at least 2 AZs - this module's VPC provides
    exactly that, with public subnets only (no NAT Gateway cost)."""
    template = _synth(config)
    template.resource_count_is("AWS::EC2::Subnet", 2)


def test_control_plane_security_group_has_the_mandatory_tags(config):
    """The `Custom::AWSCDK-EKS-Cluster` resource itself has no CloudFormation
    `Tags` property (custom resources only get one when their schema declares
    it), so the mandatory tags are checked here instead, on the cluster's own
    control-plane security group - a child resource that inherits the tags
    applied to the `eks.Cluster` construct, including the `Name` tag."""
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup", {"Tags": Match.array_with([tag])}
        )
