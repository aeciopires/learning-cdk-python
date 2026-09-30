<!-- TOC -->

- [Testing](#testing)
  - [Why test infrastructure code at all?](#why-test-infrastructure-code-at-all)
  - [How CDK unit tests work, in one paragraph](#how-cdk-unit-tests-work-in-one-paragraph)
  - [Running the tests](#running-the-tests)
  - [Where tests live](#where-tests-live)
  - [Reading your first test, line by line](#reading-your-first-test-line-by-line)
  - [The `config` fixture](#the-config-fixture)
  - [The assertion toolbox](#the-assertion-toolbox)
  - [Writing your own test, step by step](#writing-your-own-test-step-by-step)
  - [Common mistakes when you're new to this](#common-mistakes-when-youre-new-to-this)
  - [What these tests do *not* check](#what-these-tests-do-not-check)
  - [Test coverage](#test-coverage)
    - [What coverage measures, in plain words](#what-coverage-measures-in-plain-words)
    - [Running it](#running-it)
    - [Reading the report](#reading-the-report)
    - [The rules: aim for 100%, never below 80%](#the-rules-aim-for-100-never-below-80)
    - [Closing a coverage gap, step by step](#closing-a-coverage-gap-step-by-step)
    - [What coverage does *not* tell you](#what-coverage-does-not-tell-you)
  - [Testing examples/enterprise_stack (a different shape of test)](#testing-examplesenterprise_stack-a-different-shape-of-test)
    - [Why it's a separate test suite](#why-its-a-separate-test-suite)
    - [Two kinds of test, and why both exist](#two-kinds-of-test-and-why-both-exist)
    - [How to test a new builder, step by step](#how-to-test-a-new-builder-step-by-step)
  - [References](#references)

<!-- TOC -->

# Testing

This page explains, from zero, how the tests in this repository work and how
to write your own. If you've never written a test before - CDK or otherwise
- start at the top and read straight through once; after that, use it as a
reference.

## Why test infrastructure code at all?

`stack.py` is Python code, and Python code has bugs like any other: a typo
in a property name, a tag you forgot to apply, a resource you meant to make
private that's actually public. Normally you'd only find that out by running
`cdk deploy` and looking at what actually got created - slow, and on real
AWS, sometimes costly. A **unit test** catches the same mistake in
milliseconds, without creating anything, by inspecting the CloudFormation
template your code *would* produce.

## How CDK unit tests work, in one paragraph

Every module's test file does three things: (1) build the stack in memory,
the same way `app.py` does, but with a small, fixed, fake configuration
instead of real environment variables; (2) ask the AWS CDK's own
[`aws_cdk.assertions`](https://docs.aws.amazon.com/cdk/v2/guide/testing.html)
module to turn that stack into its CloudFormation template, still entirely
in memory; (3) assert things about that template - "there is exactly one
S3 bucket," "that bucket has encryption enabled," "every resource carries
the `product` tag." No AWS credentials, no Docker, no floci, and no network
access are needed to run these tests - that's what makes them fast enough
to run on every save.

## Running the tests

```bash
uv run pytest                          # every test in the repository
uv run pytest tests/unit/test_03_vpc.py           # just one module's tests
uv run pytest -k vpc                    # every test whose name/file matches "vpc"
uv run pytest -v                        # verbose: prints every test's name and result
uv run pytest -x                        # stop at the first failure, instead of running all of them
```

If a test fails, pytest prints the exact assertion that failed and the
values it compared - read that message first, it almost always tells you
exactly what's wrong without needing to add print statements.

## Where tests live

```
tests/
├── conftest.py             # shared pytest fixtures - see "The config fixture" below
└── unit/
    ├── test_01_iam.py       # one file per module, same NN_service numbering
    ├── test_02_sts.py
    ├── test_03_vpc.py
    ├── ...                  # test_04_internet_gateway.py, ..., test_43_resource_group_tagging.py
    ├── test_44_resource_quotas.py  # module 44's boto3 script.py - see below
    ├── test_app.py          # the root app.py: finds every module's stack
    └── test_shared_*.py     # shared/config.py, naming.py, tagging.py
```

`modules/44_resource_quotas` has no CDK stack (see its own README), so its
test file is different: instead of a synthesized template, it tests
`script.py`'s `boto3` calls with botocore's
[`Stubber`](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.html),
which answers each AWS API call with a canned response - nothing is sent
over the network, not even to floci.

## Reading your first test, line by line

This is `tests/unit/test_03_vpc.py` in full - open the real file alongside
this explanation:

```python
import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from tests._helpers import mandatory_tag_pairs, stack_class

VpcStack = stack_class("03_vpc")


def _synth(config):
    app = cdk.App()
    stack = VpcStack(app, "TestVpcStack", config=config)
    return Template.from_stack(stack)


def test_creates_exactly_one_vpc(config):
    template = _synth(config)
    template.resource_count_is("AWS::EC2::VPC", 1)


def test_vpc_has_the_mandatory_tags(config):
    template = _synth(config)
    for tag in mandatory_tag_pairs(config):
        template.has_resource_properties(
            "AWS::EC2::VPC", {"Tags": Match.array_with([tag])}
        )
```

- **`stack_class("03_vpc")` instead of a normal `import`.** Every
  `modules/NN_service/` directory name starts with a digit (`03_vpc`,
  `12_s3`, ...), which is not a legal Python identifier - literally writing
  `from modules.03_vpc.stack import VpcStack` is a `SyntaxError`. `app.py`
  works around this with `importlib.import_module()` on a plain string
  instead of `import` syntax; `tests/_helpers.stack_class()` does the same
  thing so every test file can stay a one-liner - see that file's
  docstring for the full explanation.
- `_synth(config)` is a small helper, private to this file (the leading
  `_` is a Python convention meaning "not meant to be imported elsewhere"):
  it creates a fresh `cdk.App()`, instantiates the module's real
  `VpcStack` exactly like `app.py` would, and turns it into a `Template` -
  every test in the file starts from this.
- Every test function's name starts with `test_` - that's how pytest finds
  them; it collects every function named like that in every file named
  `test_*.py`.
- `config` is a **fixture** - see the next section.
- `template.resource_count_is("AWS::EC2::VPC", 1)` asserts the template
  contains exactly one resource of that CloudFormation type. `"AWS::EC2::VPC"`
  is the same CloudFormation resource type name you'd see in the AWS
  Console or in `cdk synth`'s raw output - not a CDK/Python class name.
- `template.has_resource_properties(type, properties)` asserts at least one
  resource of that type has properties matching what you pass - `Match.array_with([...])`
  means "this list contains at least these elements, in any order, possibly
  with others too" (the VPC has more tags than just these two - the test
  only checks the ones it cares about).

## The `config` fixture

Every test function above takes `config` as a parameter, without importing
it - that's pytest's **fixture** system. `tests/conftest.py` defines it
once:

```python
@pytest.fixture
def config() -> AppConfig:
    return AppConfig(
        product="learning-cdk-python",
        environment="test",
        team_owner="platform-engineering",
        pci=False,
        cell_based=False,
        cell_id=None,
    )
```

pytest sees any test function argument named `config` and automatically
calls this function to produce the value, fresh for every test - so every
test in the whole repository builds its stack against the exact same,
predictable tag values, regardless of what's in your shell's environment
variables (contrast with `shared/config.load_app_config()`, which `app.py`
uses instead, and which *does* read `CDK_*` environment variables - see
`REQUIREMENTS.md` section 9).

## The assertion toolbox

The handful of `Template`/`Match` methods used throughout this repository:

| Call | Checks |
|---|---|
| `template.resource_count_is(type, n)` | exactly `n` resources of that CloudFormation type exist |
| `template.has_resource_properties(type, props)` | at least one resource of that type has these properties (a subset match by default) |
| `Match.array_with([...])` | a list contains at least these elements |
| `Match.object_like({...})` | a dict/object contains at least these key/value pairs |
| `template.find_resources(type)` | returns every matching resource as a dict, for a manual assertion when the two helpers above aren't precise enough |

The full list lives in the official
[`aws_cdk.assertions` API reference](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.assertions/) -
look there before assuming a method exists.

## Writing your own test, step by step

Say you want to check that `modules/26_sqs`'s queue has a redrive policy
(a dead-letter queue configured). In `tests/unit/test_26_sqs.py`:

1. **Synthesize the stack** (every file already has a `_synth(config)`
   helper at the top - reuse it):
   ```python
   def test_queue_has_a_redrive_policy(config):
       template = _synth(config)
   ```
2. **Decide the CloudFormation resource type** you're asserting on. For
   SQS, that's `"AWS::SQS::Queue"` - the fastest way to find the exact
   string for any resource is `uv run cdk synth SqsStack` and reading the
   `"Type"` field of the resource you care about in `cdk.out/SqsStack.template.json`.
3. **Assert the property**:
   ```python
       template.has_resource_properties(
           "AWS::SQS::Queue",
           {"RedrivePolicy": Match.object_like({"maxReceiveCount": 3})},
       )
   ```
4. **Run just that test** and check it actually fails if you comment out
   the redrive policy in `stack.py` - this "watch it fail first" step is
   how you find out whether your test is really testing anything, and is
   worth doing every time you write a new one:
   ```bash
   uv run pytest tests/unit/test_26_sqs.py -v
   ```

## Common mistakes when you're new to this

- **Asserting on the Python construct instead of the template.** These
  tests never check `queue.queue_name` or similar Python-side properties -
  that would only prove your code passed a value to the construct, not that
  the resulting CloudFormation is correct. Always assert on `template`.
- **Over-specifying with `has_resource_properties`.** Passing every single
  property (including ones you don't care about, like a machine-generated
  `LogicalId`) makes the test brittle - it breaks the next time an
  unrelated property changes. Assert only what the test is actually about.
- **Forgetting `config` in the test function's parameter list.** Without
  it, pytest won't inject the fixture and you'll get a `NameError` for
  `config` inside the function body.

## What these tests do *not* check

These are **unit tests against a synthesized template** - they do not
deploy anything, so they cannot catch: an AWS API rejecting a value at
deploy time (for example, an OpenSearch domain name over 28 characters -
see `modules/23_opensearch/README.md`), IAM permissions that are too
narrow for the resource to actually work, or floci/real-AWS service
behavior differences. Each module's README "Deploy with floci" section is
how you check those - unit tests and an actual deploy answer different
questions, and this repository uses both.

## Test coverage

### What coverage measures, in plain words

A test suite can pass while large parts of the code never run at all - a
test only proves something about the lines it actually executes.
**Coverage** answers "which lines did my tests run?". While the tests run,
the [`coverage.py`](https://coverage.readthedocs.io/) tool (used here
through the [`pytest-cov`](https://pytest-cov.readthedocs.io/) plugin)
records every line Python executes; afterwards it compares that to every
line in the code and reports the percentage that ran.

This repository also measures **branch coverage**: an `if` only counts as
fully covered when *both* its "true" and "false" paths ran. For example,
in `shared/tagging.py`:

```python
if tags.cell_based and tags.cell_id:
    Tags.of(scope).add("cell-id", tags.cell_id)
```

every module's test runs this `if` - but with the shared `config` fixture,
which is never cell-based, the line inside it never runs. Line coverage
would miss that half; branch coverage flags it, and
`tests/unit/test_shared_tagging.py` exists to cover it.

### Running it

```bash
make coverage                          # both test suites + report; fails below 80%
make coverage SKIP_COVERAGE_CHECK=1    # same report, but never fails on the minimum
```

`make coverage` is a shortcut for this command, which you can also run
directly (see the [`Makefile`](../Makefile)):

```bash
uv run pytest tests examples/enterprise_stack/tests --cov --cov-report=term-missing --cov-report=html
```

- `tests examples/enterprise_stack/tests` runs **both** test suites in one
  go (the second one normally runs separately - see
  [Why it's a separate test suite](#why-its-a-separate-test-suite)), so one
  report covers the whole repository.
- `--cov` turns coverage on; *what* is measured, and the 80% minimum, come
  from the `[tool.coverage.*]` sections of
  [`pyproject.toml`](../pyproject.toml).
- `--cov-report=term-missing` prints the table below;
  `--cov-report=html` also writes a browsable report to `htmlcov/` - open
  `htmlcov/index.html` and click a file to see every line highlighted green
  (ran), red (never ran), or yellow (a branch that only went one way).

`SKIP_COVERAGE_CHECK=1` is for work in progress - for example, while you're
still writing the tests for a new module. The report still prints; only the
"fail below 80%" check is switched off. A finished change must pass
`make coverage` **without** it.

### Reading the report

```
Name                        Stmts   Miss Branch BrPart  Cover   Missing
-----------------------------------------------------------------------
modules/03_vpc/stack.py        33      0      0      0   100%
shared/config.py               33      5      4      0    81%   65-69
-----------------------------------------------------------------------
TOTAL                        1413      5     50      0    99%
Required test coverage of 80.0% reached. Total coverage: 99.00%
```

| Column | Meaning |
|---|---|
| `Stmts` | lines of code that can run (comments and blank lines don't count) |
| `Miss` | of those, lines no test ran |
| `Branch` | number of possible paths out of `if`/`for`/`while` statements |
| `BrPart` | branches where only one of the paths ever ran |
| `Cover` | the percentage covered, lines and branches combined |
| `Missing` | exactly which lines (`65-69`) or branches (`44->46`, "line 44 never jumped to line 46") to write a test for |

The last line is the verdict: the total is compared to the minimum, and
`make coverage` exits with an error if it's lower.

### The rules: aim for 100%, never below 80%

- **The goal is 100%** for every module's `stack.py`, `shared/`, the root
  `app.py`, `modules/44_resource_quotas/script.py`, and
  `examples/enterprise_stack/` - and today, every one of them is at 100%.
- **The minimum accepted is 80%** of the whole repository - set as
  `fail_under = 80` in `pyproject.toml`, so `make coverage` fails below it.
  Anything between 80% and 100% needs a reason, not just a shrug: some code
  genuinely can't run in a unit test.
- **"Genuinely can't run" is a short, explicit list** in `pyproject.toml`'s
  `exclude_also`: the `if __name__ == "__main__":` line (only runs when a
  file is executed as a script, never when a test imports it) and
  `raise NotImplementedError` (the body of an abstract method, which is
  never called by design). Code that *could* be tested but isn't yet is not
  on this list - it's a gap to close, not to exclude.

A module's `stack.py` usually reaches 100% for free - building the stack
runs every line - so for modules, coverage mostly catches `if`/`else`
branches nobody exercised. What your test *asserts* still matters more; see
[What coverage does *not* tell you](#what-coverage-does-not-tell-you).

### Closing a coverage gap, step by step

1. Run `make coverage` and find the file in the `Missing` column (or open
   `htmlcov/index.html` and look for red and yellow lines).
2. Open that file at those line numbers and ask: *what input would make
   this line run?* Usually it's a value your tests never use - a
   cell-based config, an environment variable that's set, an error case.
3. Write a test that provides exactly that input, in the matching test file
   (`tests/unit/test_NN_service.py` for a module, `test_shared_*.py` for
   `shared/`, `examples/enterprise_stack/tests/` for the example). Make it
   assert on the result - not just run the code.
4. Run `make coverage` again and confirm the lines disappeared from
   `Missing`.
5. Break the code on purpose (change a value, comment out the line) and
   confirm your new test fails - then undo it. A test that passes no matter
   what adds coverage without adding any protection.

Some patterns used in this repository's tests, for code that doesn't fit
the usual "synthesize a stack" shape:

| Code to cover | Technique | Example |
|---|---|---|
| Behavior driven by environment variables | pytest's `monkeypatch.setenv()`/`delenv()` (undone after each test) | `tests/unit/test_shared_config.py` |
| An error that should be raised | `with pytest.raises(ValueError, match="..."):` | `tests/unit/test_shared_tagging.py` |
| A whole CDK app (`app.py`) | call `main()` with `cdk.App` pointed at a temporary folder, then read the stacks back with `cx_api.CloudAssembly` | `tests/unit/test_app.py` |
| `boto3` calls | botocore's `Stubber`: canned responses, no network | `tests/unit/test_44_resource_quotas.py` |
| Printed output | pytest's `capsys` fixture | `tests/unit/test_44_resource_quotas.py` |

### What coverage does *not* tell you

100% coverage means every line *ran* during a test - not that every line
was *checked*. A test that builds a stack and asserts nothing reaches the
same coverage as one that checks every property. Coverage finds code no
test touches; it can't tell you whether your assertions are the right ones.
That's why every module's test still asserts its mandatory tags and its
one or two most important resource facts (see
[Writing your own test, step by step](#writing-your-own-test-step-by-step)),
and why step 5 above matters.

## Testing examples/enterprise_stack (a different shape of test)

[`examples/enterprise_stack/`](../examples/enterprise_stack/README.md) - the
SOLID/builder-pattern combined-stack example, see its own README for what
it is - has its own tests, in
[`examples/enterprise_stack/tests/`](../examples/enterprise_stack/tests/),
written in the same `aws_cdk.assertions` style this page has explained so
far, plus one kind of test the 44 modules above never need. This section
covers only what's *different* there - everything above still applies.

### Why it's a separate test suite

Two concrete differences from every `tests/unit/test_NN_service.py` file:

- **It isn't discovered by a bare `uv run pytest`.** This repository's
  `pyproject.toml` sets `testpaths = ["tests"]`, so pytest never looks
  inside `examples/` unless told to. Run these explicitly:
  ```bash
  uv run pytest examples/enterprise_stack/tests/ -v
  ```
- **No `stack_class()`, no shared `config` fixture.** Those two helpers
  (`tests/_helpers.py`, `tests/conftest.py`) exist specifically to import
  a `modules/NN_service/stack.py` (whose directory name starts with a
  digit - see [Reading your first test, line by line](#reading-your-first-test-line-by-line))
  and to hand every module test the same fixed `AppConfig`.
  `examples/enterprise_stack/stack.py` is an ordinary, digit-free import
  (`from examples.enterprise_stack.stack import EnterpriseCellStack`), and
  its tests build their own `AppConfig` directly with a small local
  `_config()` helper (each test file defines its own copy - there's no
  shared `examples/enterprise_stack/tests/conftest.py`, since only two
  files need it so far).

### Two kinds of test, and why both exist

- **Synth-level tests** (`test_stack_synth.py`, `test_ecs_ecr_load_balancing.py`) -
  the same technique as every module test above: build a real
  `EnterpriseCellStack` with `aws_cdk.assertions`, assert on the
  synthesized template. These catch anything a module test would: a
  missing tag, a wrong property, the wrong number of resources for a given
  `enabled_keys` set.
- **Pure-Python precedence tests** (`test_registry.py`) - these test
  `core/resource_registry.py`'s topological-sort/validation logic using
  tiny fake `ResourceBuilder` subclasses that don't touch AWS CDK
  *at all* - no `cdk.App()`, no `Template.from_stack()`, no CloudFormation
  anywhere. This is only possible because of how the example is designed
  (see `examples/enterprise_stack/README.md`,
  [section 2.1](../examples/enterprise_stack/README.md#21---s-single-responsibility-principle)
  and [2.5](../examples/enterprise_stack/README.md#25---d-dependency-inversion-principle)):
  `ResourceRegistry.ordered()` only ever calls `.key` and `.depends_on` on
  whatever it's given - it has no idea a real `ResourceBuilder` eventually
  calls into `aws_cdk`, so a test can hand it a fake one instead and the
  ordering/validation logic runs exactly the same, in well under a
  millisecond. This is a concrete example of *designing for testability*:
  splitting "decide the order" from "actually build AWS resources" into
  separate objects is what makes the first half testable without the
  second half existing at all.

### How to test a new builder, step by step

Adding builder #15 (see `examples/enterprise_stack/README.md`,
[section 11](../examples/enterprise_stack/README.md#11-extending-it-adding-resource-15))?
Write its test the same way `test_ecs_ecr_load_balancing.py` tests `ecr`:

1. **Build only what you need enabled.** Reuse or copy the `_build(enabled_keys)`
   helper pattern - it constructs a fresh `cdk.App()` and
   `EnterpriseCellStack` for exactly the `enabled_keys` set your test
   cares about, nothing more:
   ```python
   def test_my_new_resource_has_the_property_i_expect():
       template = _build({"vpc", "my_new_key"})
       template.has_resource_properties("AWS::Some::Type", {...})
   ```
2. **If your builder has a `depends_on`, test that it's enforced** - enable
   it *without* its dependency and confirm `MissingDependencyError` is
   raised before any CDK construct is even created:
   ```python
   def test_my_new_resource_depends_on_vpc():
       with pytest.raises(MissingDependencyError):
           _build({"my_new_key"})
   ```
3. **If your builder reads `context.shared`**, add a test confirming it
   uses the *shared* construct rather than creating its own (the same
   shape as `test_lambda_reuses_the_iam_builders_role_not_its_own` in
   `test_stack_synth.py`, or `test_ecs_task_uses_the_ecr_repository_not_a_public_image`
   in `test_ecs_ecr_load_balancing.py`) - assert a resource count of `1`
   where a bug would produce `2`, or inspect the actual rendered property
   (an ARN reference, an image URI) to confirm it points at the shared
   construct and not a hardcoded fallback.
4. **Run it and watch it fail first**, the same discipline as every module
   test above:
   ```bash
   uv run pytest examples/enterprise_stack/tests/ -v
   ```

## References

- [AWS CDK v2 Developer Guide - Testing constructs](https://docs.aws.amazon.com/cdk/v2/guide/testing.html)
- [AWS CDK API Reference (Python) - `aws_cdk.assertions`](https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.assertions/)
- [pytest documentation - fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [coverage.py documentation](https://coverage.readthedocs.io/) · [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [botocore - Stubber reference](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/stubber.html)
- [`examples/enterprise_stack/README.md`](../examples/enterprise_stack/README.md) -
  what the example is, and section 2 for the SOLID principles its
  testability rests on.
