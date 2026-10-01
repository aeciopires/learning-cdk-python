<!-- TOC -->

- [Contributing](#contributing)
  - [Ground rules](#ground-rules)
  - [Development workflow](#development-workflow)
  - [Adding a new module](#adding-a-new-module)
  - [Opening a pull request](#opening-a-pull-request)
  - [Reporting issues](#reporting-issues)

<!-- TOC -->

# Contributing

Thanks for your interest in this project! This is a beginner-oriented
learning path for AWS CDK with Python - contributions of all sizes are
welcome: typo fixes, a clearer explanation in a README, a new module for an
AWS service not covered yet, or a fix to an existing module's CDK code.

## Ground rules

1. **Deploy against floci by default.** Every module's primary "Deploy"
   instructions target the [floci](https://floci.io) local emulator, not a
   real AWS account - see [`REQUIREMENTS.md`](REQUIREMENTS.md). A "Deploy to
   real AWS (optional)" section may follow, clearly marked, with any cost
   caution the module needs.
2. **Don't invent facts.** Any CDK construct name, property, or AWS
   behavior claim must come from a source you actually consulted - see
   [`CLAUDE.md`](CLAUDE.md#4-do-not-invent-things-the-core-guardrail) for
   the full guardrail this repository follows. If you're not sure an API
   detail is still accurate, look it up instead of guessing.
3. **Follow the tagging and naming policy exactly.** Every resource gets
   the 7 mandatory tags via `shared/tagging.py` and a name built by
   `shared/naming.py` - see
   [`REQUIREMENTS.md`, sections 7-8](REQUIREMENTS.md#7-tagging-policy) and
   [`CLAUDE.md`, section 5](CLAUDE.md#5-tagging-and-naming-non-negotiable).
4. **Keep every stack account/region-agnostic.** No hardcoded account ID,
   region, or Availability Zone name - see
   [`CLAUDE.md`, section 6](CLAUDE.md#6-accountregion-flexibility-non-negotiable).
5. **Match the module contract.** `app.py` discovers every module
   automatically based on a fixed convention (`STACK_ID`, `STACK_CLASS`,
   `README.md` section structure) - see
   [`CLAUDE.md`, section 3](CLAUDE.md#3-the-module-contract) before adding
   or restructuring a module.

## Development workflow

See [`REQUIREMENTS.md`](REQUIREMENTS.md) for the full list of software
prerequisites and the zero-to-first-deploy walkthrough.

```bash
make check                       # confirms your OS + every tool below is actually installed
uv sync                          # installs aws-cdk-lib, constructs, boto3, and dev tools
docker compose up -d floci       # local AWS emulator
uv run ruff check .              # lint
make typecheck                   # type-check (mypy) - see the Makefile for why it's not a single mypy call
uv run cdk synth <StackId>       # validate a specific module synthesizes
uv run cdk diff <StackId>        # what a deploy would change - changes nothing (REQUIREMENTS.md 5.11)
uv run cdk deploy <StackId> --require-approval never --method=direct  # deploy it to floci (REQUIREMENTS.md 5.8)
make cdk-resources STACK=<StackId>  # every resource it created, via the README's AWS CLI commands (REQUIREMENTS.md 5.10)
uv run cdk destroy <StackId>     # clean up
uv run pytest tests/unit/test_NN_service.py -v  # that module's unit tests
uv run pytest                    # every unit test in the repository
make coverage                    # every test (repository + examples) with a coverage report - must pass (>= 80%)
```

Once the commands above are familiar, `make cdk-synth STACK=<StackId>` /
`make cdk-deploy STACK=<StackId>` (and `make floci-start`/`floci-stop`/
`floci-status`/`floci-destroy`) are optional shortcuts for them - see
[`REQUIREMENTS.md`, section 5.6](REQUIREMENTS.md#56---optional-make-shortcuts-for-floci-and-the-cdk).
Documentation keeps showing the long `uv run ...` form.

**Test coverage:** every change must keep `make coverage` passing - aim for
100% of the code you add or change, never below the 80% repository minimum.
`make coverage SKIP_COVERAGE_CHECK=1` reports without enforcing the
minimum, for work in progress only. See
[`docs/TESTING.md`, "Test coverage"](docs/TESTING.md#test-coverage).

`uv run pytest` runs the unit tests in `tests/unit/` - one file per module
with a `stack.py` - against the synthesized CloudFormation template, using
`aws_cdk.assertions`. See [`docs/TESTING.md`](docs/TESTING.md) for a full,
from-zero explanation of how these work and how to write one; every module
has one (see [`CLAUDE.md`, section 3, point 7](CLAUDE.md#3-the-module-contract)).

## Adding a new module

1. Read [`CLAUDE.md`, sections 2-6](CLAUDE.md#2-directory-and-file-structure)
   for the exact directory layout and module contract, and read
   `modules/03_vpc/` (both files, plus `tests/unit/test_03_vpc.py`) as the
   module every other one should resemble.
2. Look up the CDK constructs you plan to use in the
   [AWS CDK API Reference (Python)](https://docs.aws.amazon.com/cdk/api/v2/python/)
   before writing code - see the guardrail linked above.
3. Create `modules/NN_service/` (next free number, zero-padded 2 digits) with
   `__init__.py`, `stack.py`, and `README.md`.
4. Run `uv run cdk synth <StackId>` until it succeeds with no errors, then
   `uv run cdk diff <StackId>` (what the deploy will create) and
   `uv run cdk deploy <StackId> --require-approval never --method=direct` against floci.
   Generate the README's "List every resource with the AWS CLI" section
   with `scripts/resource_commands.py --markdown` (see
   [`REQUIREMENTS.md`, section 5.10](REQUIREMENTS.md#510---listing-every-resource-a-stack-created)
   and [`CLAUDE.md`, section 3](CLAUDE.md#3-the-module-contract), point 6),
   and confirm every resource actually exists by running those commands
   (or `make cdk-resources STACK=<StackId>`), then `uv run cdk destroy
   <StackId>` and, if the stack has a VPC, `uv run python scripts/floci_prune.py --apply`.
5. Write `tests/unit/test_NN_service.py` (see
   [`docs/TESTING.md`](docs/TESTING.md)) and a matching "Tests" section in
   the module's `README.md`, and confirm `uv run pytest tests/unit/test_NN_service.py -v`
   passes.
6. Add the module to the table in
   [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md), in the phase that fits
   it best.
7. Add an entry to [`CHANGELOG.md`](CHANGELOG.md) under "Unreleased".

## Opening a pull request

1. Fork the repository and create a branch from `main`.
2. Make your change, following the ground rules above.
3. Run the checks in [Development workflow](#development-workflow) for
   every module you touched.
4. Open a pull request describing *why* the change is useful, not just what
   changed. Link any official source you relied on for a technical claim
   (a specific CDK API reference page, an AWS service doc page).
5. Be responsive to review feedback - this is a small project maintained on
   a best-effort basis, so review may take a few days.

## Reporting issues

Open a GitHub issue. For a bug in a module, include: the module directory
(e.g. `modules/15_ecs`), the exact `cdk synth`/`cdk deploy` command you
ran, and the full error output. For a documentation issue, link the
specific file and section.
