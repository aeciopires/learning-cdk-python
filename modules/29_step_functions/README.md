<!-- TOC -->

- [Module 29 - Step Functions (a small state machine)](#module-29---step-functions-a-small-state-machine)
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

# Module 29 - Step Functions (a small state machine)

## Overview

AWS Step Functions lets you describe a multi-step workflow - a **state
machine** - as data (JSON, following the Amazon States Language) instead of
writing the orchestration code (retries, branching, waiting) yourself. Each
step is a **state**. This module builds a 4-state order-shipping workflow
using only Step Functions' own built-in states - no Lambda function or other
service is called - so the whole module has no external dependency.

## What you will learn

- How a chain of states (`Pass -> Wait -> Choice -> Pass`) becomes a state
  machine definition in CDK, using `.next(...)` to link states together.
- `sfn.Pass` - a state that does nothing but pass its input through (useful
  as a placeholder, or to inject/reshape data).
- `sfn.Wait` with `sfn.WaitTime.duration(...)` - a state that pauses the
  execution for a fixed amount of time.
- `sfn.Choice` + `sfn.Condition` - branching to a different next state based
  on a field of the execution's input.
- Why this module uses `definition_body=sfn.DefinitionBody.from_chainable(...)`
  and not the older `definition=` prop (see [Notes and cautions](#notes-and-cautions)).

## AWS services and CDK constructs used

| AWS service | CDK construct (Python) | Level |
|---|---|---|
| AWS Step Functions | `aws_cdk.aws_stepfunctions.StateMachine` | L2 |
| AWS Step Functions | `aws_cdk.aws_stepfunctions.DefinitionBody` | L2 |
| AWS Step Functions | `aws_cdk.aws_stepfunctions.Pass` | L2 |
| AWS Step Functions | `aws_cdk.aws_stepfunctions.Wait`, `aws_cdk.aws_stepfunctions.WaitTime` | L2 |
| AWS Step Functions | `aws_cdk.aws_stepfunctions.Choice`, `aws_cdk.aws_stepfunctions.Condition` | L2 |

## Prerequisites

- Repository-wide setup done once: see [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md)
  (uv, Node.js + AWS CDK Toolkit, Docker, floci).
- From the repository root: `uv sync` and `docker compose up -d floci`.

## Tests

See [`../../docs/TESTING.md`](../../docs/TESTING.md) for how these work if
you haven't read it yet.

This module's tests
([`../../tests/unit/test_29_step_functions.py`](../../tests/unit/test_29_step_functions.py))
check that: exactly one state machine is created, its `DefinitionString`
contains the `IsExpressShipping` Choice state and branches on
`$.shippingType` equalling `"express"` (this module's whole point), and
every mandatory tag (see
[`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) section 7) is present. No
Docker, floci, or AWS credentials needed:

```bash
# From the repository root:
uv run pytest tests/unit/test_29_step_functions.py -v
```

## Deploy with floci (local, free)

```bash
# From the repository root - see ../../REQUIREMENTS.md for eval $(floci env)
eval $(floci env)
uv run cdk synth StepFunctionsStack
uv run cdk deploy StepFunctionsStack --require-approval never
```

## Deploy to real AWS (optional)

Only do this if you understand the resources being created and their cost
(see [Notes and cautions](#notes-and-cautions) - Step Functions has no hourly
charge, only per-state-transition pricing).

```bash
unset AWS_ENDPOINT_URL   # stop pointing the AWS CLI/SDK at floci
uv run cdk deploy StepFunctionsStack --profile <your-aws-cli-profile>
```

## Verify

```bash
aws stepfunctions list-state-machines

# Run it once with an express order...
aws stepfunctions start-execution \
  --state-machine-arn <arn-from-above> \
  --input '{"shippingType": "express"}'

# ...and once with anything else, to take the other Choice branch:
aws stepfunctions start-execution \
  --state-machine-arn <arn-from-above> \
  --input '{"shippingType": "standard"}'

# Inspect an execution's result (the Wait state means it takes ~5s to finish):
aws stepfunctions describe-execution --execution-arn <execution-arn-from-above>
```

Or open the floci UI at `http://localhost:4566/_floci/ui` and browse the
state machine and its executions visually.

## Clean up

```bash
uv run cdk destroy StepFunctionsStack
```

## Notes and cautions

- **`definition_body=` vs the older `definition=` prop.** aws-cdk-lib
  2.271.0's `StateMachine` constructor still accepts both, but its own API
  reference marks `definition` "(deprecated)" and documents `definition_body`
  as the current property - confirmed by inspecting the installed
  `aws_cdk.aws_stepfunctions.StateMachine.__init__` signature and parameter
  docs before writing this module. This module uses `definition_body=
  sfn.DefinitionBody.from_chainable(chain)`.
- This state machine is `state_machine_type=StateMachineType.STANDARD` (the
  default) - Standard workflows keep a full execution history and are billed
  per state transition; **Express** workflows (`StateMachineType.EXPRESS`)
  are billed per execution duration instead and suit high-volume, short-lived
  workflows. This module uses Standard because its execution history is
  easier to inspect while learning.
- Step Functions has no hourly charge - you pay per state transition beyond
  a monthly free tier. See the pricing reference below, and re-check current
  numbers before relying on them.

## References

- [AWS Step Functions - Amazon States Language](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-amazon-states-language.html)
- [AWS Step Functions - Standard vs. Express workflows](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html)
- [AWS Step Functions pricing](https://aws.amazon.com/step-functions/pricing/)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_stepfunctions.StateMachine`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_stepfunctions/StateMachine.html)
- [AWS CDK API Reference (Python) - `aws_cdk.aws_stepfunctions.DefinitionBody`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_stepfunctions/DefinitionBody.html)
