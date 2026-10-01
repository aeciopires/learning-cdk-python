"""EC2: same `ec2.Instance`/role calls verified in modules/13_ec2/stack.py
- except the VPC. modules/13_ec2 creates its own (`max_azs=1`); here,
`depends_on = ("vpc",)` and the instance is placed in the cell's one shared
VPC instead.
"""

from __future__ import annotations

from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from constructs import Construct

from examples.enterprise_stack.core.resource_builder import ResourceBuilder, ResourceContext
from shared.naming import resource_name
from shared.tagging import apply_name_tag

AL2023_AMI_PARAMETER = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-6.1-x86_64"


class Ec2ResourceBuilder(ResourceBuilder):
    key = "ec2"
    depends_on = ("vpc",)

    def build(self, scope: Construct, context: ResourceContext) -> None:
        config = context.config
        cell = config.cell_id or ""
        vpc = context.shared["vpc"]

        sg_name = resource_name(config.product, config.environment, cell, "sg", "ec2-app")
        security_group = ec2.SecurityGroup(
            scope,
            "InstanceSecurityGroup",
            vpc=vpc,
            security_group_name=sg_name,
            description="No inbound rules - reach the instance via SSM Session Manager, not SSH.",
            allow_all_outbound=True,
        )
        apply_name_tag(security_group, sg_name)

        role_name = resource_name(config.product, config.environment, cell, "role", "ec2-instance")
        role = iam.Role(
            scope,
            "InstanceRole",
            role_name=role_name,
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="EC2 instance role - SSM Session Manager access only, no other permissions.",
        )
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        apply_name_tag(role, role_name)

        instance_name = resource_name(config.product, config.environment, cell, "ec2", "app")
        instance = ec2.Instance(
            scope,
            "AppInstance",
            instance_name=instance_name,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            # Resolved by EC2 at launch, not via an SSM CloudFormation
            # parameter, so an unchanged stack is skipped on re-deploy - see
            # modules/13_ec2/stack.py for why.
            machine_image=ec2.MachineImage.resolve_ssm_parameter_at_launch(
                AL2023_AMI_PARAMETER, os=ec2.OperatingSystemType.LINUX
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=security_group,
            role=role,
            associate_public_ip_address=True,
        )
        apply_name_tag(instance, instance_name)

        context.shared["ec2_instance"] = instance
