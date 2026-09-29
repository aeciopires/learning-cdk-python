"""Module 13 - EC2: one t3.micro instance in a dedicated, minimal VPC.

AWS docs used while writing this module:
- Instance construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Instance.html
- MachineImage: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/MachineImage.html
- Vpc construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/Vpc.html
- SecurityGroup construct: https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ec2/SecurityGroup.html
- AWS Systems Manager Session Manager: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html
- AmazonSSMManagedInstanceCore managed policy (instance profile setup): https://docs.aws.amazon.com/systems-manager/latest/userguide/setup-instance-profile.html
- Amazon EC2 instance types: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-types.html

See README.md in this directory for the full explanation and deploy steps.
"""

from __future__ import annotations

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct

from shared.config import AppConfig
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

STACK_ID = "Ec2Stack"


class Ec2Stack(Stack):
    """One t3.micro EC2 instance, its own minimal VPC, and an SSM-only IAM role.

    This module's VPC (`max_azs=1`, one `PUBLIC` subnet, `nat_gateways=0`) is
    intentionally smaller than module 03's - this module is about the EC2
    instance itself, not about VPC design, so it borrows just enough network
    to run one instance.

    The security group deliberately has **no inbound rule at all** - not even
    SSH on port 22. AWS recommends reaching an instance through AWS Systems
    Manager Session Manager instead of opening an SSH port (see the "Session
    Manager" link above): Session Manager needs no inbound port, no bastion
    host, and no distributed SSH key, and every session is logged in
    CloudTrail. The IAM role attaches the AWS-managed
    `AmazonSSMManagedInstanceCore` policy so Session Manager works once this
    is deployed to a real account (the SSM Agent ships preinstalled on
    Amazon Linux 2023) - wiring up the agent/role in more detail is out of
    scope for this module, which stays focused on EC2 itself.
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

        vpc_name = resource_name(config.product, config.environment, "vpc", "ec2")
        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=vpc_name,
            max_azs=1,
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

        security_group_name = resource_name(config.product, config.environment, "sg", "ec2-app")
        self.security_group = ec2.SecurityGroup(
            self,
            "InstanceSecurityGroup",
            vpc=self.vpc,
            security_group_name=security_group_name,
            description="No inbound rules - reach the instance via SSM Session Manager, not SSH.",
            allow_all_outbound=True,
        )
        apply_name_tag(self.security_group, security_group_name)

        role_name = resource_name(config.product, config.environment, "role", "ec2-instance")
        self.instance_role = iam.Role(
            self,
            "InstanceRole",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="EC2 instance role - SSM Session Manager access only, no other permissions.",
        )
        self.instance_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )
        apply_name_tag(self.instance_role, role_name)

        instance_name = resource_name(config.product, config.environment, "ec2", "app")
        self.instance = ec2.Instance(
            self,
            "AppInstance",
            instance_name=instance_name,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=self.security_group,
            role=self.instance_role,
            # No NAT Gateway in this minimal VPC - a public IP is what lets
            # the instance (and the SSM Agent on it) reach the internet.
            associate_public_ip_address=True,
        )
        apply_name_tag(self.instance, instance_name)


STACK_CLASS = Ec2Stack
