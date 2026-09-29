"""Module 16 - EKS: a control-plane-only cluster (no managed node group).

AWS docs used while writing this module:
- Cluster construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_eks/Cluster.html
- KubernetesVersion: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_eks/KubernetesVersion.html
- Amazon EKS - What is Amazon EKS: https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html
- Amazon EKS Kubernetes version support (1.36 is current standard support
  as of the time this module was written - re-check before relying on it):
  https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions-standard.html
- aws_cdk.lambda_layer_kubectl_v36 (the extra, stable, non-alpha package this
  module depends on - see README.md "Notes and cautions" for why):
  https://pypi.org/project/aws-cdk.lambda-layer-kubectl-v36/
- cdklabs/awscdk-asset-kubectl (the project that publishes one
  lambda-layer-kubectl-vNN package per supported Kubernetes minor version):
  https://github.com/cdklabs/awscdk-asset-kubectl

See README.md in this directory for the full explanation, a very explicit
cost warning, and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_eks as eks
from aws_cdk import lambda_layer_kubectl_v36 as kubectl_layer
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "EksStack"


class EksStack(Stack):
    """One EKS control plane, no worker nodes - the most expensive module here.

    `default_capacity=0` means no managed node group is created: this stack
    provisions only the EKS control plane (billed hourly the moment it
    exists, regardless of whether any node ever joins it - see the very
    explicit cost warning in README.md) and skips all the EC2/IAM complexity
    a real worker-node setup needs, which would be out of scope for a
    beginner module.

    The VPC below (`max_azs=2` - EKS requires subnets across at least 2
    Availability Zones) uses `PUBLIC` subnets only, with `nat_gateways=0`, to
    avoid layering a NAT Gateway's hourly cost on top of the control plane's.
    A real production EKS VPC would normally also have private subnets with
    a NAT Gateway for worker nodes - this module skips that entirely, since
    it creates no nodes to put in them.

    `kubectl_layer` is a **required** constructor argument on the installed
    `aws-cdk-lib==2.271.0` `eks.Cluster` (confirmed by inspecting
    `inspect.signature(eks.Cluster.__init__)` directly against the installed
    package - it has no default value). `aws-cdk-lib` no longer bundles a
    default kubectl/helm Lambda layer inside the stable package; the current
    mechanism is one small, separate, per-Kubernetes-version package from
    the `cdklabs/awscdk-asset-kubectl` project -
    `aws-cdk.lambda-layer-kubectl-v36`, matching `KubernetesVersion.V1_36`
    below. It was added to `pyproject.toml` via
    `uv add aws-cdk.lambda-layer-kubectl-v36` for this reason: without it,
    this stack cannot synthesize at all. It is a regular, versioned PyPI
    package (not an "-alpha" package, and published by the same
    `aws-cdk`/`cdklabs` maintainers as `aws-cdk-lib` itself), so it does not
    violate this repository's alpha-package rule (CLAUDE.md section 4).
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "eks")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
        )
        apply_name_tag(self.vpc, vpc_name)

        cluster_name = resource_name(config.product, config.environment, "eks", "main")
        self.cluster = eks.Cluster(
            self,
            "Cluster",
            cluster_name=cluster_name,
            vpc=self.vpc,
            # This VPC has no private subnet group (see above) - eks.Cluster
            # otherwise defaults to looking for one, so the public group has
            # to be selected explicitly.
            vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)],
            version=eks.KubernetesVersion.V1_36,
            default_capacity=0,
            kubectl_layer=kubectl_layer.KubectlV36Layer(self, "KubectlLayer"),
        )
        apply_name_tag(self.cluster, cluster_name)


STACK_CLASS = EksStack
