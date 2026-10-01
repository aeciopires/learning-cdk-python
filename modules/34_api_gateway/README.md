<!-- TOC -->

- [Module 34 - API Gateway (REST, a backend-free API)](#module-34---api-gateway-rest-a-backend-free-api)
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

# Module 34 - API Gateway (REST, a backend-free API)

## Overview

Amazon API Gateway lets you expose an HTTP API without running your own web
server. This module uses API Gateway's **REST API** (the stable,
full-featured API type - see [Notes and cautions](#notes-and-cautions) for
why not the newer "HTTP API" type) and gives it one `GET /demo` method
backed by a **Mock integration** - API Gateway itself returns a canned
response, with no Lambda function, container, or any other backend
involved.

## What you will learn

- How `apigateway.RestApi` (the CDK L2 construct) creates an API Gateway
  REST API, complete with a deployed stage.
- What a Mock integration is: a real, AWS-documented way to test a REST
  API's routing and request/response shape before any backend exists, using
  `apigateway.MockIntegration` with `request_templates` (what the "backend"
  pretends to receive) and `integration_responses` (what it sends back).
- How a method's `method_responses` (what API Gateway promises callers) and
  an integration's `integration_responses` (what the integration actually
  returns) are matched up by `status_code`.

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| Amazon API Gateway | `aws_cdk.aws_apigateway.RestApi` | L2 |
| Amazon API Gateway | `aws_cdk.aws_apigateway.MockIntegration` | L2 |
| Amazon API Gateway | `aws_cdk.aws_apigateway.IntegrationResponse` | L2 (props) |
| Amazon API Gateway | `aws_cdk.aws_apigateway.MethodResponse` | L2 (props) |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_34_api_gateway.py`](../../tests/unit/test_34_api_gateway.py))
check that: exactly one REST API is created, exactly one method exists with
`HttpMethod: GET` and an `Integration.Type: MOCK` (no backend, the whole
point of this module), the method's `MethodResponses` include status code
`"200"`, and every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present on
the REST API. No Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_34_api_gateway.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk bootstrap   # once per floci instance - safe to re-run; see REQUIREMENTS.md section 5.7
uv run cdk synth ApiGatewayStack
uv run cdk deploy ApiGatewayStack --require-approval never --method=direct
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(see [Notes and cautions](#notes-and-cautions) - API Gateway has no hourly
charge, only usage-based pricing).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk bootstrap --profile <your-aws-cli-profile>   # once per AWS account/region
uv run cdk deploy ApiGatewayStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws apigateway get-rest-apis
aws apigateway get-resources --rest-api-id <rest-api-id-from-above>

# Test the mock method without a real HTTP call:
aws apigateway test-invoke-method \
  --rest-api-id <rest-api-id-from-above> \
  --resource-id <demo-resource-id-from-above> \
  --http-method GET
```

`test-invoke-method` should return HTTP 200 with the canned JSON body from
this module's `MockIntegration`.

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
API, its resources, and its deployed stage visually.

## Clean up

```bash
uv run cdk destroy ApiGatewayStack
```

## Notes and cautions

- **REST API, not HTTP API - deliberately.** This module uses
  `aws_cdk.aws_apigateway` (REST APIs), the module fully covered by stable
  `aws-cdk-lib`. `aws_cdk.aws_apigatewayv2` (HTTP APIs) is also stable for
  the core API/route/stage constructs, but several of its integration
  helpers (notably Lambda/HTTP proxy integrations) have historically shipped
  in separate alpha (`-alpha`) packages - this repository never uses an
  alpha/experimental package (see `CLAUDE.md`, section 4), so every API
  Gateway module in this learning path uses the REST API surface instead.
- A Mock integration is a genuine testing technique, not a placeholder hack
  - it is documented by AWS for exactly this purpose: verifying an API's
  request/response contract before wiring up a real backend. A later,
  richer module could add a Lambda-backed integration alongside it.
- API Gateway REST APIs have no hourly charge - you pay per API call/data
  transfer beyond a monthly free tier - see the pricing reference below,
  and re-check current numbers before relying on them.

## References

- [Amazon API Gateway - Set up a mock integration](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-create-api-as-simple-proxy-for-lambda.html)
- [Amazon API Gateway - REST APIs vs. HTTP APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)
- [Amazon API Gateway pricing](https://aws.amazon.com/api-gateway/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_apigateway.RestApi`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/RestApi.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_apigateway.MockIntegration`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/MockIntegration.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_apigateway.IntegrationResponse`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/IntegrationResponse.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_apigateway.MethodResponse`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_apigateway/MethodResponse.html)
