<!-- TOC -->

- [Module 39 - CloudWatch (log -> metric -> alarm -> dashboard)](#module-39---cloudwatch-log---metric---alarm---dashboard)
  - [Overview](#overview)
  - [What you will learn](#what-you-will-learn)
  - [AWS services and CDK constructs used](#aws-services-and-cdk-constructs-used)
  - [Prerequisites](#prerequisites)
  - [Tests](#tests)
  - [Deploy with floci (local, free)](#deploy-with-floci-local-free)
  - [Deploy to real AWS (optional)](#deploy-to-real-aws-optional)
  - [Verify](#verify)
  - [Clean up](#clean-up)
  - [Notes and cautions](#notes-and-cautions)
  - [References](#references)

<!-- TOC -->

# Module 39 - CloudWatch (log -> metric -> alarm -> dashboard)

## Overview

Amazon CloudWatch is where AWS resources' logs, metrics, and alarms live.
This module builds the full, small pipeline a real application's error
monitoring usually follows: a **log group** receives log lines, a **metric
filter** turns any line containing `"ERROR"` into a custom metric data
point, an **alarm** watches that metric, and a **dashboard** graphs it -
four resources, one pipeline, no compute needed to demonstrate it.

## What you will learn

- How `logs.MetricFilter` converts unstructured log text into a numeric
  CloudWatch metric, using a filter pattern (`FilterPattern.literal(...)`).
- How to go from a metric filter straight to a bound `Metric` object
  (`metric_filter.metric(...)`) without repeating the namespace/name by
  hand, then hand that `Metric` to both an `Alarm` and a `GraphWidget`.
- Why `treat_missing_data=NOT_BREACHING` matters: an application that logs
  nothing for five minutes is not the same as an application in error, and
  the alarm should not fire just because there is no data.
- How a `Dashboard` + `GraphWidget` plot the same metric an alarm watches,
  side by side.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon CloudWatch Logs | `aws_cdk.aws_logs.LogGroup` | L2 |
| Amazon CloudWatch Logs | `aws_cdk.aws_logs.MetricFilter` | L2 |
| Amazon CloudWatch Logs | `aws_cdk.aws_logs.FilterPattern` | L2 (helper) |
| Amazon CloudWatch | `aws_cdk.aws_cloudwatch.Alarm` | L2 |
| Amazon CloudWatch | `aws_cdk.aws_cloudwatch.Dashboard` | L2 |
| Amazon CloudWatch | `aws_cdk.aws_cloudwatch.GraphWidget` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_39_cloudwatch.py`](../../tests/unit/test_39_cloudwatch.py))
check that: exactly one log group, metric filter, alarm, and dashboard are
created, the metric filter's pattern and transformation actually count
`"ERROR"` lines into the `ErrorCount` metric, the alarm fires on at least
one error within a 5-minute period, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the log group, alarm, and dashboard (`AWS::Logs::MetricFilter` has no
tagging property of its own, so it has no equivalent check). No Docker,
floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_39_cloudwatch.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth CloudWatchStack
uv run cdk deploy CloudWatchStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created. A log group,
metric filter, alarm, and dashboard all have small, usage-based costs
(log ingestion/storage, custom metrics, alarms, dashboards past a free
tier) - see [Reference 5](#references).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy CloudWatchStack --profile <your-aws-cli-profile>
```

## Verify

Put a sample log line containing `"ERROR"` into the log group and watch the
metric filter and alarm react:

```bash
LOG_GROUP=$(aws logs describe-log-groups --log-group-name-prefix learning-cdk-python \
  --query "logGroups[?contains(logGroupName, 'app')].logGroupName | [0]" --output text)

STREAM=demo-stream
aws logs create-log-stream --log-group-name "$LOG_GROUP" --log-stream-name "$STREAM"
aws logs put-log-events --log-group-name "$LOG_GROUP" --log-stream-name "$STREAM" \
  --log-events "timestamp=$(date +%s000),message='ERROR: something went wrong'"

aws cloudwatch get-metric-statistics \
  --namespace learning-cdk-python-dev-app \
  --metric-name ErrorCount \
  --start-time "$(date -u -d '-10 min' +%Y-%m-%dT%H:%M:%S)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
  --period 300 --statistics Sum

aws cloudwatch describe-alarms --alarm-names <alarm-name>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
log group, metric, alarm, and dashboard visually.

## Clean up

```bash
uv run cdk destroy CloudWatchStack
```

## Notes and cautions

- `retention=logs.RetentionDays.ONE_WEEK` is deliberate: the L2
  `LogGroup` construct's own default is to keep logs **forever**, which is
  rarely what you want (and costs more over time) - see
  [Reference 4](#references) for the full range of retention options.
- The alarm has no action attached (no SNS topic, no auto-scaling policy) -
  see [`../27_sns`](../27_sns/README.md) for how a real alarm would notify
  someone; this module only shows the metric -> alarm wiring itself.
- The metric filter here only counts matching lines (`metric_value="1"`);
  a real filter can also *extract* a number from a structured log line
  (e.g. a response time) - see [Reference 3](#references) for the fuller
  filter pattern syntax.

## References

- [Amazon CloudWatch - What is Amazon CloudWatch?](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/WhatIsCloudWatch.html)
- [Amazon CloudWatch Logs - Creating metrics from log events using filters](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html)
- [Amazon CloudWatch Logs - Filter and pattern syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/FilterAndPatternSyntax.html)
- [Amazon CloudWatch Logs - Change log data retention](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Working-with-log-groups-and-streams.html)
- [Amazon CloudWatch pricing](https://aws.amazon.com/cloudwatch/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_logs.MetricFilter`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_logs/MetricFilter.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_cloudwatch.Alarm`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Alarm.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_cloudwatch.Dashboard`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_cloudwatch/Dashboard.html)
