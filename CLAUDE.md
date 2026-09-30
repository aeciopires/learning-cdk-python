<!-- TOC -->

- [CLAUDE.md](#claudemd)
  - [1. About this repository](#1-about-this-repository)
  - [2. Directory and file structure](#2-directory-and-file-structure)
  - [3. The module contract](#3-the-module-contract)
  - [4. Do not invent things: the core guardrail](#4-do-not-invent-things-the-core-guardrail)
  - [5. Tagging and naming (non-negotiable)](#5-tagging-and-naming-non-negotiable)
  - [6. Account/region flexibility (non-negotiable)](#6-accountregion-flexibility-non-negotiable)
  - [7. Markdown formatting conventions](#7-markdown-formatting-conventions)
  - [8. Internal anchor links and TOC](#8-internal-anchor-links-and-toc)
  - [9. Python/CDK conventions](#9-pythoncdk-conventions)
  - [10. Workflow when adding or changing a module](#10-workflow-when-adding-or-changing-a-module)
  - [11. What not to do](#11-what-not-to-do)
  - [12. Environment notes](#12-environment-notes)

<!-- TOC -->

# CLAUDE.md

Guide for anyone - human or an AI coding assistant like Claude Code -
maintaining or extending this repository. Read this before adding or
editing a module.

## 1. About this repository

`learning-cdk-python` is a **public, beginner-oriented** learning path for
managing AWS resources with the [AWS Cloud Development Kit (CDK) v2](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
in Python, using [uv](https://docs.astral.sh/uv/) as the package/venv
manager. It is 44 small, independent modules (`modules/NN_service/`), each
teaching one AWS service through a minimal, deployable CDK stack plus a
README that explains it. Every module is meant to be deployed first against
[floci](https://floci.io), a local AWS emulator run via `docker-compose.yml`
(or `floci-cli`) - see [`REQUIREMENTS.md`](REQUIREMENTS.md) - so the whole
path can be completed without an AWS account or any cost. It is **not**
tied to any company or private context: every resource name, tag value, and
example uses the generic `learning-cdk-python` product name and
placeholder team/environment values, never a real company's internals.

**Root meta files stay English-only.** `CLAUDE.md`, `CONTRIBUTING.md`,
`CHANGELOG.md`, and `REQUIREMENTS.md` are English only, by the maintainer's
explicit choice. This repository has no bilingual *documentation* tree to
keep in parity - unlike some sibling repositories, module READMEs and the
`docs/` guides are English only. The one bilingual pair is
`docs/slides/SLIDES-en-US.md` / `docs/slides/SLIDES-pt-BR.md` (see
[section 2](#2-directory-and-file-structure)) - keep both decks in sync
whenever one is edited.

## 2. Directory and file structure

```
.
├── README.md              # landing page: what this is, quickstart, links
├── LICENSE                # GPLv3 - do not modify without being asked
├── REQUIREMENTS.md        # software/hardware prerequisites, floci setup, tagging/naming policy
├── CONTRIBUTING.md        # how to propose a change or a new module
├── CHANGELOG.md           # Keep a Changelog style
├── CLAUDE.md              # this file
├── pyproject.toml         # uv-managed dependencies (aws-cdk-lib, constructs, boto3, dev tools)
├── .python-version        # the Python version uv builds .venv/ with
├── mise.toml               # Python, Node.js 26, npm 11, and the AWS CLI v2, for mise (recommended - REQUIREMENTS.md section 3.3)
├── cdk.json                # "app": "uv run python app.py" - see section 9
├── app.py                  # discovers and instantiates every module's stack - see section 3
├── docker-compose.yml      # floci (local AWS emulator + floci-ui/floci-dash consoles)
├── .env.example             # every CDK_*/AWS_* variable a module reads, with comments
├── Makefile                 # `make check` (scripts/check-deps.sh, REQUIREMENTS.md section 3.4) and `make typecheck` (mypy)
├── scripts/
│   └── check-deps.sh          # what `make check` runs - OS + every tool in REQUIREMENTS.md section 3
├── shared/                  # tagging.py, naming.py, config.py - see section 5 and 6
├── docs/
│   ├── LEARNING-PATH.md    # the full 44-module table, grouped into 11 phases
│   ├── TESTING.md           # how CDK unit tests work here, and how to write one - see section 3, point 7
│   ├── ARCHITECTURE.md      # diagrams: CDK workflow, floci environment, module wiring, VPC resources
│   ├── IMPORTING-EXISTING-RESOURCES.md  # from_* references vs. cdk import vs. cdk migrate
│   ├── diagrams/             # Mermaid (.mmd) source for every diagram in ARCHITECTURE.md
│   ├── images/               # rendered .svg for every diagram - see ARCHITECTURE.md section 5
│   │   └── tools/             # official floci/AWS CDK logos + live floci/floci-dash screenshots - maintained originals; SLIDES-*.md embeds them as base64 data URIs, see REQUIREMENTS.md section 11.2
│   └── slides/               # Marp slide decks (en-US/pt-BR) - see REQUIREMENTS.md section 11
├── modules/
│   └── NN_service/          # one per AWS service - see section 3 for the exact contract
│       ├── __init__.py
│       ├── stack.py
│       └── README.md
├── examples/
│   └── enterprise_stack/    # a separate, combined SOLID/builder-pattern CDK app - NOT bound by
│                             # the module contract below, not auto-discovered by the root app.py,
│                             # and not part of docs/LEARNING-PATH.md - see its own README.md
└── tests/
    ├── conftest.py            # the shared `config` pytest fixture
    ├── _helpers.py             # stack_class() / mandatory_tag_pairs() - see docs/TESTING.md
    └── unit/
        └── test_NN_service.py  # one per module with a stack.py - mandatory, see section 3 point 7
```

See [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md) for the full list of
44 modules, their stack ids, and which of the 11 phases each belongs to.
`modules/03_vpc/` is the reference module every other module was written to
match - read it before writing or editing any other module. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for diagrams of the CDK
workflow, the floci local environment, the config/tagging/naming wiring
described in this section, and how `modules/03_vpc`'s own resources relate
to each other.

## 3. The module contract

`app.py` discovers modules dynamically (`pkgutil.iter_modules` over
`modules/`) instead of importing each one by name, so adding a module never
requires editing `app.py`. This only works because every `modules/NN_service/stack.py`
follows the same contract:

**This contract applies only to `modules/NN_service/`.** `examples/enterprise_stack/`
is a deliberately different shape (one combined stack assembling several
AWS services, not one lesson per service) with its own `app.py`, its own
tests, and its own README - see
[`examples/enterprise_stack/README.md`, section 1](examples/enterprise_stack/README.md#1-what-this-is-and-why-it-lives-outside-modules)
for why it is not a 45th module.

1. A `Stack` subclass whose `__init__` signature is exactly
   `(self, scope: Construct, construct_id: str, *, config: AppConfig, **kwargs) -> None`
   (`config` is a `shared.config.AppConfig`; `env` arrives through `**kwargs`).
2. A module-level `STACK_ID: str` - the CloudFormation/CDK stack id, e.g.
   `"VpcStack"` (PascalCase, no separators, matching the service name used
   in `docs/LEARNING-PATH.md`).
3. A module-level `STACK_CLASS` pointing at the class from point 1.
4. `apply_standard_tags(self, tags=config.to_standard_tags())` called once,
   immediately after `super().__init__(...)`.
5. `apply_name_tag(<construct>, <name>)` called once per significant
   resource created in the stack (see [section 5](#5-tagging-and-naming-non-negotiable)).
6. A `README.md` in the same directory, matching the section structure of
   `modules/03_vpc/README.md` (Overview, What you will learn, AWS services
   and CDK constructs used, Prerequisites, Tests, Deploy with floci, Deploy
   to real AWS, Verify, Clean up, Notes and cautions, References).
7. A `tests/unit/test_NN_service.py` file (same numbering as the module
   directory) that builds the stack with the shared `config` fixture and
   asserts on its synthesized template via `aws_cdk.assertions` - see
   [`docs/TESTING.md`](docs/TESTING.md) and
   `tests/unit/test_03_vpc.py` for the pattern every test file follows,
   and `tests/_helpers.py` for the `stack_class()`/`mandatory_tag_pairs()`
   helpers every test file uses. At minimum, assert the mandatory tags
   are present (`mandatory_tag_pairs()`) and the module's one or two most
   important resource-level facts (a count, a key property) - not every
   property of every resource.

A module with **no deployable CDK resource** (there is exactly one: `44_resource_quotas`
- Service Quotas has no CloudFormation resource type at all) has no
`stack.py`; `app.py` skips any `modules/*/` directory that lacks one, and
it has no `tests/unit/test_44_...py` either - see that module's README for
how it's checked instead. Do not invent a fake CDK construct to avoid this
- document the gap instead (see [section 4](#4-do-not-invent-things-the-core-guardrail))
and, if a `boto3`/AWS CLI example is the only honest way to show the
service, put it in that module's README and an optional `script.py`.

## 4. Do not invent things: the core guardrail

This is the most important rule in this repository:

1. **Every CDK construct name, property, and AWS behavior claim must come
   from a source that was actually consulted** - the
   [AWS CDK API Reference (Python)](https://docs.aws.amazon.com/cdk/api/v2/python/),
   the [AWS CDK v2 Developer Guide](https://docs.aws.amazon.com/cdk/v2/guide/home.html),
   or the relevant AWS service's own documentation - not recalled from
   memory. If a construct's exact name or required properties aren't
   certain, look them up before writing the line of code.
2. **Prefer the L2 (curated) construct** for a service when one exists
   (e.g. `aws_cdk.aws_s3.Bucket`, `aws_cdk.aws_sqs.Queue`). **When no L2
   construct exists** (true for several services in this path - WAFv2,
   GuardDuty, Athena, ElastiCache, Resource Groups, Cost Explorer's
   anomaly-detection resources, among others), **use the L1 `Cfn*`
   construct** (a 1:1 mapping to the CloudFormation resource type) and say
   so explicitly in the module's README, with a link to that `Cfn*`
   construct's API reference page.
3. **Never use an alpha/experimental package** (any PyPI package name
   ending in `-alpha`, e.g. `aws-cdk.aws-apigatewayv2-integrations-alpha`).
   This path only uses modules shipped inside the stable `aws-cdk-lib`
   package - pick the stable construct that covers the same service even if
   it's a slightly different API shape (for example, API Gateway REST APIs
   - `aws_cdk.aws_apigateway` - instead of the HTTP API integrations that
   have lived in alpha packages).
4. **A service with genuinely no CloudFormation/CDK resource** (Service
   Quotas is the only one in this path) gets a documented gap, not a
   fabricated construct - see point 6 of [section 3](#3-the-module-contract).
5. **Numbers and version-specific details are the highest-risk content** (a
   default retention period, a current stable image tag, a package's latest
   version). Always check current documentation rather than a remembered
   value, and say so in the text when a number can change over time (e.g.
   "re-check the current docs/tags before relying on this").
6. **If a primary source won't load**, try an alternate URL from the same
   official source before falling back to unverified memory, and be
   explicit in the text about what couldn't be verified live.

## 5. Tagging and naming (non-negotiable)

Every module applies the exact same 7 tags via [`shared/tagging.py`](shared/tagging.py)
and builds physical resource names via [`shared/naming.py`](shared/naming.py)
- see [`REQUIREMENTS.md`, sections 7 and 8](REQUIREMENTS.md#7-tagging-policy)
for the human-readable policy these two files encode. In code:

```python
from shared.naming import resource_name
from shared.tagging import apply_name_tag, apply_standard_tags

# once, right after super().__init__(...):
apply_standard_tags(self, tags=config.to_standard_tags())

# once per significant resource:
queue_name = resource_name(config.product, config.environment, "sqs", "orders")
queue = sqs.Queue(self, "OrdersQueue", queue_name=queue_name)
apply_name_tag(queue, queue_name)
```

The environment is always one of three short names - `dev`, `stg`
(staging), `prd` (production) - never `staging`/`prod`/`production`:
`shared/config.py` (`ENVIRONMENTS`, `validate_environment()`) rejects
anything else when reading `CDK_ENVIRONMENT`, and the enterprise example's
`ENTERPRISE_ENVIRONMENT` and `environments/*.json` file names follow the
same rule.

Never hardcode a tag value, a product name, an environment name, or a team
name in a module - every one of those comes from `config` (a
`shared.config.AppConfig`, built from environment variables - see
`shared/config.py`). The only values a module invents on its own are the
*resource purpose* segment of a name (`"orders"`, `"app"`, `"main"`, ...)
and example data (bucket contents, queue messages, etc.) - this is the
"tag and resource values" exception mentioned in this repository's founding
brief.

## 6. Account/region flexibility (non-negotiable)

No module hardcodes an AWS account ID, region, or Availability Zone name.
`app.py` resolves `env=` once via `shared/config.get_environment()` and
passes it to every stack; a module that needs an AZ count uses `max_azs=`
(as `modules/03_vpc` does), never a literal AZ string. See
[`REQUIREMENTS.md`, section 9](REQUIREMENTS.md#9-flexible-account-and-region).

## 7. Markdown formatting conventions

- **Manual TOC** at the top of any file with more than ~3 sections,
  delimited by a `<!-- TOC -->` ... `<!-- TOC -->` comment pair, one list
  entry per `##`/`###` heading, linking to the matching anchor. Update the
  TOC whenever you add/rename/remove a heading.
- Every module README ends with a `## References` section listing every
  official source used (AWS service docs + the specific CDK API reference
  page(s) for the constructs used).
- Markdown tables for comparisons (e.g. "AWS service | CDK construct |
  Level") - preferred over prose whenever there are 2+ comparison columns.
- Internal links are always relative (`[text](../other/file.md)`) and
  internal anchors are always relative to the file itself
  (`[text](#anchor)`) - never an absolute GitHub URL.
- **Diagrams** live as a `.mmd` [Mermaid](https://mermaid.js.org/) source
  file under [`docs/diagrams/`](docs/diagrams/) and a rendered `.svg` under
  [`docs/images/`](docs/images/), embedded in the relevant doc with a plain
  markdown image (`![alt text](images/name.svg)` from `docs/ARCHITECTURE.md`)
  - never a raw ```` ```mermaid ```` fenced block, so the diagram renders
  the same in every viewer, not only ones with Mermaid support. See
  [`docs/ARCHITECTURE.md` section 5](docs/ARCHITECTURE.md#5-regenerating-these-diagrams)
  for the exact `mmdc` command to regenerate an `.svg` after editing its
  `.mmd` source, and for what "validating" a diagram means here (`mmdc`
  exits non-zero on a syntax error instead of writing a file).

## 8. Internal anchor links and TOC

The TOCs and cross-references only work if the slug matches what
GitHub/GitLab generates from the heading exactly. Slug rule: lowercase,
remove any character that isn't a letter/number/space/hyphen/underscore
(this removes `:`, `,`, `()`, `/` - it does not replace them with a hyphen),
then turn each remaining space into a hyphen. Whenever a heading is added,
renamed, or removed, re-check every anchor link in that file.

## 9. Python/CDK conventions

- Import CDK modules the way the
  [official Python guide](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html#python-cdk-idioms)
  recommends: `import aws_cdk as cdk` for the core module, individual
  `from aws_cdk import Stack` for frequently used top-level names, and
  short namespace aliases per service, e.g. `from aws_cdk import aws_s3 as s3`.
- `lambda` is a Python keyword; the Lambda module (`17_lambda`) follows the
  documented convention of aliasing its import (`from aws_cdk import aws_lambda as lambda_`).
- `scope` and `id`/`construct_id` are always positional, never keyword
  arguments (see the official guide, same section, on why).
- Every module runs through `uv run` - see `cdk.json`'s `"app"` entry. Do
  not add a module that requires activating `.venv` manually to work; `uv
  run cdk ...` (or a bare `cdk ...` once `.venv` is active) must be enough.
- Type hints are used throughout (`from __future__ import annotations` at
  the top of every `stack.py`) so editors and `mypy` can catch the
  Python-side type mistakes the
  [official guide's "type pitfalls" section](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html#python-type-pitfalls)
  warns about.

## 10. Workflow when adding or changing a module

1. **Read `modules/03_vpc/` first** (both `stack.py` and `README.md`) -
   every new module should look like it was written by the same person.
2. **Look up the exact CDK constructs before writing code** - see
   [section 4](#4-do-not-invent-things-the-core-guardrail).
3. **Follow the module contract exactly** - see [section 3](#3-the-module-contract).
4. **Validate it actually synthesizes**: `uv run cdk synth <StackId>` must
   succeed with no errors. Where Docker is available, `docker compose up -d
   floci` then `uv run cdk deploy <StackId> --require-approval never`
   followed by `uv run cdk destroy <StackId> -f` is the full round-trip
   check.
5. **Write and run its unit tests**: `uv run pytest tests/unit/test_NN_service.py -v`
   must pass - see point 7 of [section 3](#3-the-module-contract) and
   [`docs/TESTING.md`](docs/TESTING.md). Write the test *before* declaring
   the module done, not after, and confirm it actually fails if you break
   the thing it's testing (comment out a property, change a value) - a
   test that can't fail isn't testing anything.
6. **Update `docs/LEARNING-PATH.md`** if you added, renamed, or
   reordered a module.
7. **Git:** default branch is `main`; do not commit or push without an
   explicit request from whoever you're working with.

## 11. What not to do

- Don't invent a CDK construct, property name, or AWS behavior without
  checking the current official source first.
- Don't use an alpha/experimental CDK package.
- Don't hardcode a tag value, product/team/environment name, AWS account
  ID, region, or Availability Zone - see sections 5 and 6.
- Don't skip a module's `README.md`, or let it drift from the section
  structure in `modules/03_vpc/README.md`.
- Don't skip a module's unit test, and don't write one that can't fail
  (see point 5 of [section 10](#10-workflow-when-adding-or-changing-a-module)).
- Don't leave a broken anchor link or a stale TOC after editing headings.
- Don't commit or push without being explicitly asked to.

## 12. Environment notes

This repository has no CI pipeline defined yet. Every module's "Deploy with
floci" instructions need Docker + Docker Compose v2 (or `floci-cli`) - see
[`REQUIREMENTS.md`](REQUIREMENTS.md) for the full prerequisite list and
per-OS install commands. `uv sync` needs network access to PyPI the first
time it runs; afterward it works from its local cache.
