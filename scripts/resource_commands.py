#!/usr/bin/env python3
"""AWS CLI commands that list every resource a CDK stack created.

One source of truth for two uses:

* **README sections** - `--markdown` prints, for one stack's template, a
  bash block with one `aws ...` command per resource. Every module README's
  "List every resource with the AWS CLI" section (and the enterprise
  example's) was generated this way; a new module's is too - see CLAUDE.md
  section 3, point 6.
* **`make cdk-resources`** - without `--markdown`, it reads each deployed
  stack's template from CloudFormation and *runs* those same commands
  (read-only, so it is safe to repeat), printing what each one finds.

The commands are parametrized the way the docs ask: `$PRODUCT`/`$ENV` for
names built by `shared/naming.py`, `$REGION` on every call, `$ACCOUNT` where
an ARN must be built. A resource without a name of its own (a VPC, a
subnet, a KMS key, ...) is looked up by its *logical id* in the stack
(`pid <LogicalId>`), which is identical in every environment. EC2 resources
are never filtered by tag, because floci does not keep EC2 tags.

Usage, from the repository root with .env loaded:

    uv run python scripts/resource_commands.py --markdown VpcStack --template cdk.out/VpcStack.template.json
    uv run python scripts/resource_commands.py VpcStack          # run against the deployed stack
    uv run python scripts/resource_commands.py --all             # every deployed stack in $REGION
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import boto3  # type: ignore[import-untyped]

PREAMBLE = """\
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV={environment} REGION={region}
STACK={stack}{account}
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() {{ aws cloudformation describe-stack-resource --stack-name "${{2:-$STACK}}" \\
  --logical-resource-id "$1" --region "$REGION" \\
  --query StackResourceDetail.PhysicalResourceId --output text; }}

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \\
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \\
  --output table
"""
ACCOUNT_LINE = '\nACCOUNT=$(aws sts get-caller-identity --query Account --output text)'

# Resource types with no "list/describe" of their own: the command for the
# resource they belong to (in parentheses) already shows them.
SHOWN_BY_PARENT = {
    "AWS::ApiGateway::Method": "its REST API resource",
    "AWS::Backup::BackupSelection": "its backup plan",
    "AWS::EC2::Route": "its route table",
    "AWS::EC2::SubnetRouteTableAssociation": "its route table",
    "AWS::EC2::VPCGatewayAttachment": "its internet gateway",
    "AWS::EC2::SecurityGroupIngress": "its security group",
    "AWS::EC2::SecurityGroupEgress": "its security group",
    "AWS::EC2::TransitGatewayRoute": "its transit gateway route table",
    "AWS::EC2::TransitGatewayRouteTableAssociation": "its transit gateway route table",
    "AWS::S3::BucketPolicy": "its bucket",
    "AWS::SQS::QueuePolicy": "its queue",
    "AWS::IAM::Policy": "its IAM role",
    "AWS::Lambda::Permission": "its Lambda function",
    "Custom::S3AutoDeleteObjects": "the provider Lambda function and role listed here",
    "Custom::CloudwatchLogResourcePolicy": "the provider Lambda function and role listed here",
}
SKIPPED_TYPES = {"AWS::CDK::Metadata"}

# Types floci 2.1.0's CloudFormation accepts and reports as CREATE_COMPLETE
# without creating anything (it logs each as unsupported), so their commands
# find nothing on floci - they work on real AWS. Re-check with newer floci
# releases: its unreleased main branch already provisions more types. See
# REQUIREMENTS.md section 10.
FLOCI_NOT_CREATED = {
    "AWS::ApplicationAutoScaling::ScalableTarget",
    "AWS::ApplicationAutoScaling::ScalingPolicy",
    "AWS::Athena::WorkGroup",
    "AWS::Backup::BackupPlan",
    "AWS::CE::AnomalyMonitor",
    "AWS::CE::AnomalySubscription",
    "AWS::DocDB::DBCluster",
    "AWS::DocDB::DBInstance",
    "AWS::DocDB::DBSubnetGroup",
    "AWS::EC2::TransitGateway",
    "AWS::EC2::TransitGatewayRouteTable",
    "AWS::EC2::TransitGatewayVpcAttachment",
    "AWS::EC2::VPCPeeringConnection",
    "AWS::ElastiCache::ReplicationGroup",
    "AWS::ElastiCache::SubnetGroup",
    "AWS::GuardDuty::Detector",
    "AWS::MSK::Cluster",
    "AWS::OpenSearchService::Domain",
    "AWS::ResourceGroups::Group",
    "AWS::Route53::RecordSet",
    "AWS::SES::EmailIdentity",
}
# Created on floci, but floci 2.1.0 doesn't implement the API call that
# lists it.
FLOCI_NOT_LISTABLE = {"AWS::Logs::MetricFilter"}


@dataclass(frozen=True)
class ResourceCommand:
    resource_type: str
    logical_id: str
    command: str


@dataclass
class TemplateContext:
    """A stack template plus the values used to parametrize its names."""

    template: dict[str, Any]
    product: str
    environment: str

    @property
    def resources(self) -> dict[str, Any]:
        resources: dict[str, Any] = self.template.get("Resources", {})
        return resources

    def props(self, logical_id: str) -> dict[str, Any]:
        props: dict[str, Any] = self.resources[logical_id].get("Properties") or {}
        return props

    def parametrize(self, value: str) -> str:
        """Replace this deployment's product/environment with $PRODUCT/$ENV."""
        prefix = f"{self.product}-{self.environment}"
        value = value.replace(prefix, "${PRODUCT}-${ENV}")
        value = value.replace(f"/{self.product}/{self.environment}/", "/${PRODUCT}/${ENV}/")
        return value.replace(self.product, "${PRODUCT}")

    def name(self, logical_id: str, prop: str) -> str | None:
        """The resource's own name from `prop`, parametrized, if it is a plain string."""
        value = self.props(logical_id).get(prop)
        return self.parametrize(value) if isinstance(value, str) else None

    def ident(self, logical_id: str, prop: str | None = None) -> str:
        """Its name (when `prop` holds one) or, failing that, `$(pid LogicalId)`."""
        named = self.name(logical_id, prop) if prop else None
        return named if named is not None else f"$(pid {logical_id})"

    def ref(self, value: Any, prop: str | None = None) -> str:
        """Identify the resource a property points at (Ref / Fn::GetAtt / literal)."""
        if isinstance(value, dict) and "Ref" in value:
            return self.ident(value["Ref"], prop)
        if isinstance(value, dict) and "Fn::GetAtt" in value:
            return f"$(pid {value['Fn::GetAtt'][0]})"
        if isinstance(value, list) and value:
            return self.ref(value[0], prop)
        return self.parametrize(str(value))


def _q(query: str) -> str:
    return f'--query "{query}" --output table'


# One function per resource type: (context, logical id) -> the command's
# service and arguments, without `aws` and `--region` (added by the caller).
Handler = Callable[[TemplateContext, str], str]

HANDLERS: dict[str, Handler] = {
    "AWS::ApiGateway::RestApi": lambda c, l: f'apigateway get-rest-api --rest-api-id "{c.ident(l)}" {_q("[id,name]")}',
    "AWS::ApiGateway::Resource": lambda c, l: (
        f'apigateway get-resource --rest-api-id "{c.ref(c.props(l)["RestApiId"])}" '
        f'--resource-id "{c.ident(l)}" {_q("[path,id]")}'
    ),
    "AWS::ApiGateway::Deployment": lambda c, l: (
        f'apigateway get-deployment --rest-api-id "{c.ref(c.props(l)["RestApiId"])}" '
        f'--deployment-id "{c.ident(l)}" {_q("[id,createdDate]")}'
    ),
    "AWS::ApiGateway::Stage": lambda c, l: (
        f'apigateway get-stage --rest-api-id "{c.ref(c.props(l)["RestApiId"])}" '
        f'--stage-name "{c.ident(l, "StageName")}" {_q("[stageName,deploymentId]")}'
    ),
    "AWS::ApiGateway::Account": lambda c, l: f'apigateway get-account {_q("cloudwatchRoleArn")}',
    "AWS::ApplicationAutoScaling::ScalableTarget": lambda c, l: (
        "application-autoscaling describe-scalable-targets --service-namespace ecs "
        + _q(f"ScalableTargets[?contains(ResourceId, '{_ecs_cluster(c)}')].[ResourceId,MinCapacity,MaxCapacity]")
    ),
    "AWS::ApplicationAutoScaling::ScalingPolicy": lambda c, l: (
        "application-autoscaling describe-scaling-policies --service-namespace ecs "
        + _q(f"ScalingPolicies[?contains(ResourceId, '{_ecs_cluster(c)}')].[PolicyName,PolicyType]")
    ),
    "AWS::Athena::WorkGroup": lambda c, l: f'athena get-work-group --work-group "{c.ident(l, "Name")}" {_q("WorkGroup.[Name,State]")}',
    "AWS::Backup::BackupVault": lambda c, l: (
        f'backup describe-backup-vault --backup-vault-name "{c.ident(l, "BackupVaultName")}" '
        + _q("[BackupVaultName,BackupVaultArn]")
    ),
    "AWS::Backup::BackupPlan": lambda c, l: (
        "backup list-backup-plans "
        + _q(f"BackupPlansList[?BackupPlanName=='{c.parametrize(str(c.props(l)['BackupPlan']['BackupPlanName']))}'].[BackupPlanName,BackupPlanId]")
    ),
    "AWS::CE::AnomalyMonitor": lambda c, l: (
        "ce get-anomaly-monitors " + _q(f"AnomalyMonitors[?MonitorName=='{c.name(l, 'MonitorName')}'].[MonitorName,MonitorArn]")
    ),
    "AWS::CE::AnomalySubscription": lambda c, l: (
        "ce get-anomaly-subscriptions "
        + _q(f"AnomalySubscriptions[?SubscriptionName=='{c.name(l, 'SubscriptionName')}'].[SubscriptionName,Frequency]")
    ),
    "AWS::CertificateManager::Certificate": lambda c, l: (
        "acm list-certificates "
        + _q(f"CertificateSummaryList[?DomainName=='{c.name(l, 'DomainName')}'].[DomainName,Status,CertificateArn]")
    ),
    "AWS::CloudFormation::Stack": lambda c, l: f'cloudformation describe-stacks --stack-name "{c.ident(l)}" {_q("Stacks[].[StackName,StackStatus]")}',
    "AWS::CloudFront::Distribution": lambda c, l: f'cloudfront get-distribution --id "{c.ident(l)}" {_q("Distribution.[Id,DomainName,Status]")}',
    "AWS::CloudFront::OriginAccessControl": lambda c, l: (
        f'cloudfront get-origin-access-control --id "{c.ident(l)}" {_q("OriginAccessControl.[Id,OriginAccessControlConfig.Name]")}'
    ),
    "AWS::CloudTrail::Trail": lambda c, l: f'cloudtrail describe-trails --trail-name-list "{c.ident(l, "TrailName")}" {_q("trailList[].[Name,S3BucketName]")}',
    "AWS::CloudWatch::Alarm": lambda c, l: f'cloudwatch describe-alarms --alarm-names "{c.ident(l, "AlarmName")}" {_q("MetricAlarms[].[AlarmName,StateValue]")}',
    "AWS::CloudWatch::Dashboard": lambda c, l: f'cloudwatch get-dashboard --dashboard-name "{c.ident(l, "DashboardName")}" {_q("DashboardName")}',
    "AWS::Cognito::UserPool": lambda c, l: f'cognito-idp describe-user-pool --user-pool-id "{c.ident(l)}" {_q("UserPool.[Id,Name]")}',
    "AWS::Cognito::UserPoolClient": lambda c, l: (
        f'cognito-idp describe-user-pool-client --user-pool-id "{c.ref(c.props(l)["UserPoolId"])}" '
        f'--client-id "{c.ident(l)}" {_q("UserPoolClient.[ClientId,ClientName]")}'
    ),
    "AWS::DocDB::DBCluster": lambda c, l: (
        f'docdb describe-db-clusters --db-cluster-identifier "{c.ident(l, "DBClusterIdentifier")}" '
        + _q("DBClusters[].[DBClusterIdentifier,Status,EngineVersion]")
    ),
    "AWS::DocDB::DBInstance": lambda c, l: (
        f'docdb describe-db-instances --db-instance-identifier "{c.ident(l, "DBInstanceIdentifier")}" '
        + _q("DBInstances[].[DBInstanceIdentifier,DBInstanceClass,DBInstanceStatus]")
    ),
    "AWS::DocDB::DBSubnetGroup": lambda c, l: f'docdb describe-db-subnet-groups --db-subnet-group-name "{c.ident(l)}" {_q("DBSubnetGroups[].DBSubnetGroupName")}',
    "AWS::DynamoDB::Table": lambda c, l: f'dynamodb describe-table --table-name "{c.ident(l, "TableName")}" {_q("Table.[TableName,TableStatus]")}',
    "AWS::EC2::EIP": lambda c, l: f'ec2 describe-addresses --public-ips "{c.ident(l)}" {_q("Addresses[].[PublicIp,AllocationId]")}',
    "AWS::EC2::Instance": lambda c, l: (
        f'ec2 describe-instances --instance-ids "{c.ident(l)}" {_q("Reservations[].Instances[].[InstanceId,InstanceType,State.Name]")}'
    ),
    "AWS::EC2::InternetGateway": lambda c, l: (
        f'ec2 describe-internet-gateways --internet-gateway-ids "{c.ident(l)}" '
        + _q("InternetGateways[].[InternetGatewayId,Attachments[0].VpcId]")
    ),
    "AWS::EC2::NatGateway": lambda c, l: f'ec2 describe-nat-gateways --nat-gateway-ids "{c.ident(l)}" {_q("NatGateways[].[NatGatewayId,State,SubnetId]")}',
    "AWS::EC2::RouteTable": lambda c, l: (
        f'ec2 describe-route-tables --route-table-ids "{c.ident(l)}" '
        + _q("RouteTables[].[RouteTableId,length(Routes),length(Associations)]")
    ),
    "AWS::EC2::SecurityGroup": lambda c, l: (
        f'ec2 describe-security-groups --group-ids "{c.ident(l)}" {_q("SecurityGroups[].[GroupId,GroupName,VpcId]")}'
    ),
    "AWS::EC2::Subnet": lambda c, l: f'ec2 describe-subnets --subnet-ids "{c.ident(l)}" {_q("Subnets[].[SubnetId,CidrBlock,AvailabilityZone]")}',
    "AWS::EC2::TransitGateway": lambda c, l: (
        f'ec2 describe-transit-gateways --transit-gateway-ids "{c.ident(l)}" {_q("TransitGateways[].[TransitGatewayId,State]")}'
    ),
    "AWS::EC2::TransitGatewayRouteTable": lambda c, l: (
        f'ec2 describe-transit-gateway-route-tables --transit-gateway-route-table-ids "{c.ident(l)}" '
        + _q("TransitGatewayRouteTables[].[TransitGatewayRouteTableId,State]")
    ),
    "AWS::EC2::TransitGatewayVpcAttachment": lambda c, l: (
        f'ec2 describe-transit-gateway-vpc-attachments --transit-gateway-attachment-ids "{c.ident(l)}" '
        + _q("TransitGatewayVpcAttachments[].[TransitGatewayAttachmentId,VpcId,State]")
    ),
    "AWS::EC2::VPC": lambda c, l: f'ec2 describe-vpcs --vpc-ids "{c.ident(l)}" {_q("Vpcs[].[VpcId,CidrBlock,State]")}',
    "AWS::EC2::VPCPeeringConnection": lambda c, l: (
        f'ec2 describe-vpc-peering-connections --vpc-peering-connection-ids "{c.ident(l)}" '
        + _q("VpcPeeringConnections[].[VpcPeeringConnectionId,Status.Code]")
    ),
    "AWS::ECR::Repository": lambda c, l: (
        f'ecr describe-repositories --repository-names "{c.ident(l, "RepositoryName")}" '
        + _q("repositories[].[repositoryName,repositoryUri]")
    ),
    "AWS::ECS::Cluster": lambda c, l: f'ecs describe-clusters --clusters "{c.ident(l, "ClusterName")}" {_q("clusters[].[clusterName,status]")}',
    "AWS::ECS::Service": lambda c, l: (
        f'ecs describe-services --cluster "{c.ref(c.props(l)["Cluster"], "ClusterName")}" '
        f'--services "{c.ident(l, "ServiceName")}" {_q("services[].[serviceName,status,desiredCount]")}'
    ),
    "AWS::ECS::TaskDefinition": lambda c, l: (
        f'ecs describe-task-definition --task-definition "{c.ident(l, "Family")}" {_q("taskDefinition.[family,revision,status]")}'
    ),
    "AWS::ElastiCache::ReplicationGroup": lambda c, l: (
        f'elasticache describe-replication-groups --replication-group-id "{c.ident(l, "ReplicationGroupId")}" '
        + _q("ReplicationGroups[].[ReplicationGroupId,Engine,Status]")
    ),
    "AWS::ElastiCache::SubnetGroup": lambda c, l: (
        f'elasticache describe-cache-subnet-groups --cache-subnet-group-name "{c.ident(l, "CacheSubnetGroupName")}" '
        + _q("CacheSubnetGroups[].CacheSubnetGroupName")
    ),
    "AWS::ElasticLoadBalancingV2::LoadBalancer": lambda c, l: (
        f'elbv2 describe-load-balancers --load-balancer-arns "{c.ident(l)}" {_q("LoadBalancers[].[LoadBalancerName,Type,State.Code]")}'
    ),
    "AWS::ElasticLoadBalancingV2::Listener": lambda c, l: f'elbv2 describe-listeners --listener-arns "{c.ident(l)}" {_q("Listeners[].[Port,Protocol]")}',
    "AWS::ElasticLoadBalancingV2::TargetGroup": lambda c, l: (
        f'elbv2 describe-target-groups --target-group-arns "{c.ident(l)}" {_q("TargetGroups[].[TargetGroupName,Port,TargetType]")}'
    ),
    "AWS::Events::Rule": lambda c, l: f'events describe-rule --name "{c.ident(l, "Name")}" {_q("[Name,State]")}',
    "AWS::GuardDuty::Detector": lambda c, l: f'guardduty get-detector --detector-id "{c.ident(l)}" {_q("Status")}',
    "AWS::IAM::InstanceProfile": lambda c, l: (
        f'iam get-instance-profile --instance-profile-name "{c.ident(l)}" {_q("InstanceProfile.[InstanceProfileName,Arn]")}'
    ),
    "AWS::IAM::ManagedPolicy": lambda c, l: (
        "iam list-policies --scope Local " + _q(f"Policies[?PolicyName=='{c.ident(l, 'ManagedPolicyName')}'].[PolicyName,Arn]")
    ),
    "AWS::IAM::Role": lambda c, l: f'iam get-role --role-name "{c.ident(l, "RoleName")}" {_q("Role.[RoleName,Arn]")}',
    "AWS::KMS::Key": lambda c, l: f'kms describe-key --key-id "{c.ident(l)}" {_q("KeyMetadata.[KeyId,KeyState]")}',
    "AWS::KMS::Alias": lambda c, l: "kms list-aliases " + _q(f"Aliases[?AliasName=='{c.ident(l, 'AliasName')}'].[AliasName,TargetKeyId]"),
    "AWS::Kinesis::Stream": lambda c, l: (
        f'kinesis describe-stream-summary --stream-name "{c.ident(l, "Name")}" '
        + _q("StreamDescriptionSummary.[StreamName,StreamStatus]")
    ),
    "AWS::Lambda::Function": lambda c, l: (
        f'lambda get-function --function-name "{c.ident(l, "FunctionName")}" {_q("Configuration.[FunctionName,Runtime,State]")}'
    ),
    # A layer version's physical id is its ARN; field 7 is the layer's name.
    "AWS::Lambda::LayerVersion": lambda c, l: (
        f'lambda list-layer-versions --layer-name "$(pid {l} | cut -d: -f7)" {_q("LayerVersions[].[LayerVersionArn,Version]")}'
    ),
    "AWS::Logs::LogGroup": lambda c, l: (
        f'logs describe-log-groups --log-group-name-prefix "{c.ident(l, "LogGroupName")}" '
        + _q("logGroups[].[logGroupName,retentionInDays]")
    ),
    "AWS::Logs::MetricFilter": lambda c, l: (
        f'logs describe-metric-filters --log-group-name "{c.ref(c.props(l)["LogGroupName"], "LogGroupName")}" '
        + _q("metricFilters[].[filterName,filterPattern]")
    ),
    "AWS::MSK::Cluster": lambda c, l: (
        f'kafka list-clusters-v2 --cluster-name-filter "{c.ident(l, "ClusterName")}" {_q("ClusterInfoList[].[ClusterName,State]")}'
    ),
    "AWS::OpenSearchService::Domain": lambda c, l: (
        f'opensearch describe-domain --domain-name "{c.ident(l)}" {_q("DomainStatus.[DomainName,EngineVersion]")}'
    ),
    "AWS::RDS::DBCluster": lambda c, l: (
        f'rds describe-db-clusters --db-cluster-identifier "{c.ident(l, "DBClusterIdentifier")}" '
        + _q("DBClusters[].[DBClusterIdentifier,Engine,Status]")
    ),
    "AWS::RDS::DBInstance": lambda c, l: (
        f'rds describe-db-instances --db-instance-identifier "{c.ident(l, "DBInstanceIdentifier")}" '
        + _q("DBInstances[].[DBInstanceIdentifier,Engine,DBInstanceStatus]")
    ),
    "AWS::RDS::DBSubnetGroup": lambda c, l: f'rds describe-db-subnet-groups --db-subnet-group-name "{c.ident(l)}" {_q("DBSubnetGroups[].DBSubnetGroupName")}',
    "AWS::ResourceGroups::Group": lambda c, l: f'resource-groups get-group --group-name "{c.ident(l, "Name")}" {_q("Group.[Name,GroupArn]")}',
    "AWS::Route53::HostedZone": lambda c, l: f'route53 get-hosted-zone --id "{c.ident(l)}" {_q("HostedZone.[Id,Name]")}',
    "AWS::Route53::RecordSet": lambda c, l: (
        f'route53 list-resource-record-sets --hosted-zone-id "{c.ref(c.props(l)["HostedZoneId"])}" '
        + _q(f"ResourceRecordSets[?Name=='{c.name(l, 'Name')}'].[Name,Type]")
    ),
    "AWS::S3::Bucket": lambda c, l: "s3api list-buckets " + _q(f"Buckets[?Name=='{c.ident(l, 'BucketName')}'].[Name,CreationDate]"),
    "AWS::SES::EmailIdentity": lambda c, l: (
        f'sesv2 get-email-identity --email-identity "{c.ident(l, "EmailIdentity")}" '
        + _q("[IdentityType,VerifiedForSendingStatus]")
    ),
    "AWS::SNS::Subscription": lambda c, l: (
        f'sns list-subscriptions-by-topic --topic-arn "{c.ref(c.props(l)["TopicArn"])}" '
        + _q("Subscriptions[].[Protocol,Endpoint]")
    ),
    "AWS::SNS::Topic": lambda c, l: (
        f'sns get-topic-attributes --topic-arn "arn:aws:sns:${{REGION}}:${{ACCOUNT}}:{c.ident(l, "TopicName")}" '
        + _q("Attributes.TopicArn")
    ),
    "AWS::SQS::Queue": lambda c, l: f'sqs get-queue-url --queue-name "{c.ident(l, "QueueName")}" {_q("QueueUrl")}',
    "AWS::SSM::Parameter": lambda c, l: f'ssm get-parameter --name "{c.ident(l, "Name")}" {_q("Parameter.[Name,Type]")}',
    "AWS::SecretsManager::Secret": lambda c, l: f'secretsmanager describe-secret --secret-id "{c.ident(l, "Name")}" {_q("[Name,ARN]")}',
    "AWS::StepFunctions::StateMachine": lambda c, l: (
        f'stepfunctions describe-state-machine --state-machine-arn "{_state_machine_arn(c, l)}" {_q("[name,status]")}'
    ),
    "AWS::WAFv2::WebACL": lambda c, l: (
        f'wafv2 list-web-acls --scope {c.props(l).get("Scope", "REGIONAL")} '
        + _q(f"WebACLs[?Name=='{c.ident(l, 'Name')}'].[Name,Id]")
    ),
    "Custom::AWSCDK-EKS-Cluster": lambda c, l: f'eks describe-cluster --name "{c.ident(l)}" {_q("cluster.[name,status,version]")}',
}


def _ecs_cluster(context: TemplateContext) -> str:
    """The stack's ECS cluster name (autoscaling ResourceIds embed it)."""
    for logical_id, resource in context.resources.items():
        if resource["Type"] == "AWS::ECS::Cluster":
            return context.ident(logical_id, "ClusterName")
    return "${PRODUCT}-${ENV}"


def _state_machine_arn(context: TemplateContext, logical_id: str) -> str:
    name = context.name(logical_id, "StateMachineName")
    if name is None:
        return f"$(pid {logical_id})"
    return f"arn:aws:states:${{REGION}}:${{ACCOUNT}}:stateMachine:{name}"


def build_commands(context: TemplateContext) -> tuple[list[ResourceCommand], list[str]]:
    """Every resource's command, plus the "shown by its parent" notes."""
    commands: list[ResourceCommand] = []
    notes: list[str] = []
    for logical_id, resource in context.resources.items():
        resource_type = resource["Type"]
        if resource_type in SKIPPED_TYPES:
            continue
        handler = HANDLERS.get(resource_type)
        if handler is None:
            parent = SHOWN_BY_PARENT.get(resource_type, "the table above")
            notes.append(f"{resource_type} {logical_id} - shown by {parent}")
            continue
        aws_command = f'aws {handler(context, logical_id)} --region "$REGION"'
        commands.append(ResourceCommand(resource_type, logical_id, aws_command))
    return commands, notes


def render_markdown(stack: str, context: TemplateContext, region: str = "us-east-1") -> str:
    """The README section body: one bash block for `stack`, plus floci notes."""
    commands, notes = build_commands(context)
    uses_account = any("${ACCOUNT}" in c.command for c in commands)
    lines = [
        PREAMBLE.format(
            stack=stack,
            environment=context.environment,
            region=region,
            account=ACCOUNT_LINE if uses_account else "",
        )
    ]
    for command in commands:
        lines.append(f"# {command.resource_type} ({command.logical_id})")
        lines.append(command.command)
    if notes:
        lines.append("# Also created - listed in the table above:")
        lines.extend(f"#   {note}" for note in notes)
    block = "```bash\n" + "\n".join(lines).rstrip() + "\n```\n"
    not_created = sorted({c.resource_type for c in commands if c.resource_type in FLOCI_NOT_CREATED})
    not_listable = sorted({c.resource_type for c in commands if c.resource_type in FLOCI_NOT_LISTABLE})
    if not_created:
        block += (
            "\n**On floci** (2.1.0), CloudFormation records "
            + ", ".join(f"`{t}`" for t in not_created)
            + " without creating it, so those commands find nothing there - they"
            " work on real AWS. See [`REQUIREMENTS.md`, section 10]"
            "(../../REQUIREMENTS.md#10-observations-and-limitations).\n"
        )
    if not_listable:
        block += (
            "\n**On floci** (2.1.0), "
            + ", ".join(f"`{t}`" for t in not_listable)
            + " is created, but floci doesn't implement the API call that lists it.\n"
        )
    return block


# --- running the commands against deployed stacks ----------------------------


def _shell_prelude(stack: str, product: str, environment: str, region: str) -> str:
    return (
        f"PRODUCT={product} ENV={environment} REGION={region} STACK={stack}\n"
        'ACCOUNT=$(aws sts get-caller-identity --query Account --output text)\n'
        'pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" '
        '--logical-resource-id "$1" --region "$REGION" '
        "--query StackResourceDetail.PhysicalResourceId --output text; }\n"
    )


def environment_of(template: dict[str, Any], default: str) -> str:
    """The `environment` tag value the stack's resources carry (or `default`)."""
    for resource in template.get("Resources", {}).values():
        tags = (resource.get("Properties") or {}).get("Tags")
        if isinstance(tags, dict) and isinstance(tags.get("environment"), str):
            return str(tags["environment"])
        for tag in tags if isinstance(tags, list) else []:
            if isinstance(tag, dict) and tag.get("Key") == "environment" and isinstance(tag.get("Value"), str):
                return str(tag["Value"])
    return default


def run_stack(stack: str, template: dict[str, Any], *, product: str, environment: str, region: str) -> int:
    """Run every command for one deployed stack; return how many found nothing."""
    environment = environment_of(template, environment)
    commands, _ = build_commands(TemplateContext(template, product, environment))
    prelude = _shell_prelude(stack, product, environment, region)
    empty = 0
    print(f"=== {stack} ({region}): {len(commands)} resource commands")
    for command in commands:
        result = subprocess.run(
            ["bash", "-c", prelude + command.command], capture_output=True, text=True, check=False
        )
        output = (result.stdout or result.stderr).strip()
        found = result.returncode == 0 and bool(output) and output != "None"
        expected_gap = command.resource_type in FLOCI_NOT_CREATED | FLOCI_NOT_LISTABLE
        empty += 0 if found or expected_gap else 1
        status = "ok " if found else ("~~ " if expected_gap else "-- ")
        print(f"{status}{command.resource_type} {command.logical_id}")
        if output:
            print("\n".join(f"     {line}" for line in output.splitlines()))
    return empty


def deployed_stacks(cloudformation: Any) -> list[str]:
    names = []
    for page in cloudformation.get_paginator("list_stacks").paginate():
        for summary in page["StackSummaries"]:
            if summary["StackStatus"] != "DELETE_COMPLETE" and not summary.get("ParentId"):
                names.append(summary["StackName"])
    return sorted(n for n in names if n != "CDKToolkit")


def deployed_template(cloudformation: Any, stack: str) -> dict[str, Any]:
    body = cloudformation.get_template(StackName=stack)["TemplateBody"]
    template: dict[str, Any] = body if isinstance(body, dict) else json.loads(body)
    return template


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("stacks", nargs="*", help="stack name(s)")
    parser.add_argument("--all", action="store_true", help="every deployed stack in the region")
    parser.add_argument("--markdown", action="store_true", help="print the README section instead")
    parser.add_argument("--template", type=Path, help="(--markdown) synthesized template file")
    parser.add_argument("--region", action="append", dest="regions",
                        help="region to look in (repeatable; default: AWS_DEFAULT_REGION)")
    parser.add_argument("--prefix", default="", help="(--all) only stacks whose name starts with this")
    parser.add_argument("--environment", help="(--markdown) environment the template was synthesized for")
    parser.add_argument("--check", action="store_true", help="exit 1 if any resource is not found")
    args = parser.parse_args(argv)

    regions = args.regions or [os.getenv("AWS_DEFAULT_REGION") or "us-east-1"]
    product = os.getenv("CDK_PRODUCT", "learning-cdk-python")
    environment = os.getenv("ENTERPRISE_ENVIRONMENT") or os.getenv("CDK_ENVIRONMENT") or "dev"

    if args.markdown:
        if len(args.stacks) != 1 or args.template is None:
            parser.error("--markdown needs exactly one stack name and --template")
        template = json.loads(args.template.read_text())
        environment = args.environment or environment_of(template, environment)
        context = TemplateContext(template, product, environment)
        print(render_markdown(args.stacks[0], context, regions[0]), end="")
        return 0

    if not args.all and not args.stacks:
        parser.error("name a stack, or pass --all")
    missing = 0
    stacks: list[str] = []
    for region in regions:
        cloudformation = boto3.client("cloudformation", region_name=region)
        names = deployed_stacks(cloudformation) if args.all else args.stacks
        for stack in (n for n in names if n.startswith(args.prefix)):
            template = deployed_template(cloudformation, stack)
            missing += run_stack(stack, template, product=product, environment=environment, region=region)
            stacks.append(stack)
    print(
        f"\n{len(stacks)} stack(s); {missing} resource command(s) found nothing"
        " (lines marked ~~ are known floci gaps - see REQUIREMENTS.md section 10)."
    )
    return 1 if (args.check and missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
