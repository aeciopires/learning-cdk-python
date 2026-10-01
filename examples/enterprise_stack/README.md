<!-- TOC -->

- [enterprise_stack: a SOLID, builder-based combined stack](#enterprise_stack-a-solid-builder-based-combined-stack)
  - [1. What this is, and why it lives outside modules/](#1-what-this-is-and-why-it-lives-outside-modules)
  - [2. SOLID, explained for beginners](#2-solid-explained-for-beginners)
    - [2.1 - S: Single Responsibility Principle](#21---s-single-responsibility-principle)
    - [2.2 - O: Open/Closed Principle](#22---o-openclosed-principle)
    - [2.3 - L: Liskov Substitution Principle](#23---l-liskov-substitution-principle)
    - [2.4 - I: Interface Segregation Principle](#24---i-interface-segregation-principle)
    - [2.5 - D: Dependency Inversion Principle](#25---d-dependency-inversion-principle)
  - [3. Without SOLID: what a "just make it work" version looks like](#3-without-solid-what-a-just-make-it-work-version-looks-like)
  - [4. Two more concepts this example leans on](#4-two-more-concepts-this-example-leans-on)
    - [4.1 - The Builder pattern](#41---the-builder-pattern)
    - [4.2 - What a "construct" is (CDK-specific)](#42---what-a-construct-is-cdk-specific)
  - [5. Conditional resources and precedence, explained](#5-conditional-resources-and-precedence-explained)
  - [6. Cells: replicating the same stack across environments, accounts, and regions](#6-cells-replicating-the-same-stack-across-environments-accounts-and-regions)
  - [7. Directory layout](#7-directory-layout)
  - [8. The 14 resources included](#8-the-14-resources-included)
    - [8.1 - The ecr resource: copying an image in](#81---the-ecr-resource-copying-an-image-in)
    - [8.2 - Scaling: 1 to 3 tasks, driven by CPU](#82---scaling-1-to-3-tasks-driven-by-cpu)
  - [9. Running it](#9-running-it)
    - [9.1 - List every resource with the AWS CLI](#91---list-every-resource-with-the-aws-cli)
  - [10. Tests](#10-tests)
  - [11. Extending it: adding resource #15](#11-extending-it-adding-resource-15)
  - [12. Known limitations and honest scope](#12-known-limitations-and-honest-scope)
  - [13. Alternative: one git repository (and one release cadence) per builder](#13-alternative-one-git-repository-and-one-release-cadence-per-builder)
    - [13.1 - Why you'd want this](#131---why-youd-want-this)
    - [13.2 - Where the seam already is](#132---where-the-seam-already-is)
    - [13.3 - Semantic Versioning for a builder package](#133---semantic-versioning-for-a-builder-package)
    - [13.4 - Declaring a builder as a versioned dependency](#134---declaring-a-builder-as-a-versioned-dependency)
    - [13.5 - Or a private package index, instead of git URLs directly](#135---or-a-private-package-index-instead-of-git-urls-directly)
  - [References](#references)

<!-- TOC -->

# enterprise_stack: a SOLID, builder-based combined stack

This is a **single, combined AWS CDK application** - one CDK app that can
create any subset of 14 AWS resources in one deployable unit, following
the [SOLID](https://en.wikipedia.org/wiki/SOLID) object-oriented design
principles, the [Builder design pattern](https://en.wikipedia.org/wiki/Builder_pattern),
and a config-driven "cell" model for deploying the same code to different
environments, AWS accounts, and regions. It reuses the exact, verified CDK
construct calls already checked into `modules/01_iam`, `modules/03_vpc`,
`modules/08_kms`, `modules/11_acm`, `modules/12_s3`, `modules/13_ec2`,
`modules/14_ecr`, `modules/15_ecs`, `modules/17_lambda`,
`modules/21_dynamodb`, `modules/26_sqs`, `modules/27_sns`,
`modules/30_alb`, and `modules/31_nlb` elsewhere in this repository - see
[section 8](#8-the-14-resources-included). One resource, `ecs`, deploys a
real, running application: a copy of
[`aeciopires/mytoolkit`](https://hub.docker.com/r/aeciopires/mytoolkit)
stored in this cell's own `ecr` repository, run as a Fargate service that
scales 1 to 3 tasks by CPU utilization and is exposed through both the
`alb` and `nlb` resources when they're enabled - see
[section 8.2](#82---scaling-1-to-3-tasks-driven-by-cpu).

## 1. What this is, and why it lives outside modules/

The rest of this repository is **46 small, independent modules** - the
whole point, explained in [`../../CLAUDE.md`](../../CLAUDE.md), is that
each one teaches *one* AWS service in isolation, with its own stack, its
own README, and its own unit test. `app.py` at the repository root
auto-discovers and deploys every one that has a `stack.py` (45 of them) as
**separate** CloudFormation stacks.

This example answers a different, later question: *"now that I understand
each service on its own, how would a real team combine several of them
into one cohesive, production-style application - enabled/disabled per
environment, reused across accounts and regions, without a 500-line
`if/elif` chain?"* That's a fundamentally different shape (one Stack class,
many optional resources, real inter-resource dependencies) from "46
independent lessons," so it gets its own folder, its own `app.py`, and its
own tests, entirely separate from the repository's main learning path and
its `cdk.json`. Nothing here is registered in the root `app.py` - running
`uv run cdk list` from the repository root will **not** show any of this
example's stacks; see [section 9](#9-running-it) for the separate command
that does.

## 2. SOLID, explained for beginners

SOLID is five design principles for object-oriented code, one per letter,
first collected under that acronym by Robert C. Martin ("Uncle Bob"). They
are not AWS- or CDK-specific - they apply to any object-oriented
codebase - but they map onto this example very concretely, one Python
class per principle's main example. Each subsection below explains the
principle, then exactly where this example follows it.

### 2.1 - S: Single Responsibility Principle

**The idea:** a class (or function, or module) should have one reason to
change - one job. If a class does three unrelated things, a change to any
one of those three things risks breaking the other two, and nobody can
understand the class without understanding all three jobs at once.

**Here:** every file in [`builders/`](builders/) is one class that does
exactly one thing - `S3ResourceBuilder` only knows how to create an S3
bucket; it has no idea what a VPC or a Lambda function is, and no opinion
about which resources are enabled this month. If AWS changes how S3
buckets should be encrypted, exactly one file changes.

### 2.2 - O: Open/Closed Principle

**The idea:** you should be able to *add new behavior* without *editing
existing, already-working code*. "Open" for extension (new code is
welcome), "closed" for modification (old code stays untouched, and
therefore stays trustworthy).

**Here:** [`builders/__init__.py`](builders/__init__.py)'s
`build_default_registry()` is the only place that lists every resource
this example knows about. Adding a 14th resource means writing one new
file and adding one line there - see
[section 11](#11-extending-it-adding-resource-15). `stack.py` and
`core/resource_registry.py` do not change size or shape no matter how many
resources exist; they only ever call the same three methods
(`register`/`ordered`/`build`) on whatever is registered.

### 2.3 - L: Liskov Substitution Principle

**The idea:** if code is written to work with a general type (an
"interface"), it must keep working correctly no matter *which* specific
subtype it's actually handed - a caller should never need to check "which
one is this, really?" before it can trust the result.

**Here:** `EnterpriseCellStack.__init__` (see [`stack.py`](stack.py)) does
this:

```python
for builder in registry.ordered(enabled_keys):
    builder.build(self, context)
```

`builder` might be an `IamResourceBuilder`, an `Ec2ResourceBuilder`, or any
of the other 11 - the loop body is identical either way, and it is
*correct* either way, because every one of them honors the same contract
declared in `ResourceBuilder.build()` (see
[`core/resource_builder.py`](core/resource_builder.py)): "create your
resource under `scope`, publish anything shareable on `context.shared`."
None of them does something surprising, like requiring an extra method
call first, or returning a different type than the others - that's what
makes them freely substitutable for one another.

### 2.4 - I: Interface Segregation Principle

**The idea:** don't force a class to depend on methods or data it never
uses. A "fat" interface with 20 methods, where every implementer only
really needs 3 of them, forces pointless boilerplate (or worse, broken
stub methods) on every single implementer.

**Here:** `ResourceContext` (in `core/resource_builder.py`) carries just
two things - `config` (the shared product/environment/team/cell values
every builder needs, exactly like every `modules/NN_service/stack.py`
already receives) and `shared` (a small dict, populated lazily). A builder
that needs nothing from another resource - `S3ResourceBuilder`, say - never
even looks at `shared`. Compare that to a design where every builder was
handed one giant object with a field for "the VPC," "the KMS key," "the
IAM role," and ten other things whether it needed them or not - the object
`S3ResourceBuilder` receives would then depend on (and need to be
rebuilt/re-tested whenever the shape of) 12 other resources it has nothing
to do with.

### 2.5 - D: Dependency Inversion Principle

**The idea:** high-level code (the parts that make the important
decisions) should depend on *abstractions*, not on the concrete, low-level
details of how any one piece of work gets done - and low-level code should
implement those abstractions, not the other way around. In plain terms:
"depend on an interface, not on a specific class."

**Here, twice:**

- `EnterpriseCellStack` (high-level: "assemble a cell") depends only on
  the abstract `ResourceBuilder` interface - it never imports
  `S3ResourceBuilder` or any other concrete builder by name. Which
  concrete builders exist is decided entirely in `builders/__init__.py`,
  far away from `stack.py`.
- `LambdaResourceBuilder` (see `builders/lambda_builder.py`) needs an IAM
  execution role, but it doesn't create one and it doesn't import
  `IamResourceBuilder`. It declares `depends_on = ("iam",)` (an
  abstraction: "something must have already run and left an
  `iam_role` in `context.shared`") and reads
  `context.shared["iam_role"]`. Any builder that publishes an `iam_role`
  under that key would work here - `LambdaResourceBuilder` is inverted
  away from depending on the concrete `IamResourceBuilder` class.

## 3. Without SOLID: what a "just make it work" version looks like

No code here on purpose - this section is a description, not a sample to
copy.

Picture a single, very long Python function - `build_everything(app,
config)` - that a team adds to, resource by resource, over a year of
sprints, always under deadline pressure to ship the next feature rather
than to keep the file clean:

- It starts with a VPC, then EC2, then an ALB, all created inline, one
  after another, with `if config.enable_ec2:` and `if config.enable_alb:`
  guards sprinkled directly in the middle of construct calls. Six months
  later someone needs an ECS cluster too, so they copy the EC2 block,
  paste it lower down, and change the names by hand - now there are two
  near-identical VPC-consuming blocks that both have to be remembered and
  kept in sync by hand whenever, say, the CIDR range needs to change.
- Whether the ALB block runs *before* or *after* the EC2 block depends on
  where, physically, someone happened to paste it in the file - nothing
  enforces that a resource needing the VPC only runs once the VPC actually
  exists. The day someone reorders two `if` blocks while cleaning up
  formatting, a deploy starts failing for reasons that only show up as a
  cryptic CloudFormation error, not a Python error caught before deploy.
- Every new resource needs the function's signature, and its giant pile of
  `if` conditions, edited again - there is no "add a file, change nothing
  else" option, so touching this function is everyone's least favorite
  task, and every change to it risks breaking a resource type the change
  had nothing to do with.
- Wanting a KMS-encrypted version of the S3 bucket for just the `prd`
  environment means adding an `if config.environment == "prd":` branch
  *inside* the S3-creation code, so the S3 logic now also has to know
  about environment names, deployment tiers, and eventually - as more
  special cases accumulate - almost everything else in the system.
- Testing any single piece (`"does the S3 bucket get versioning turned
  on?"`) means running the *entire* function, with a full fake config
  covering all 13+ resources' options, because none of the logic is
  separable - there is no small, focused unit to test in isolation the way
  `examples/enterprise_stack/tests/test_registry.py` tests just the
  ordering logic, with no CDK, no AWS, and no other resource involved at
  all.

Every one of those pains maps to one of the five letters above being
absent: no Single Responsibility (one function does everything), no
Open/Closed (every change edits the same function), no reliable ordering
because nothing plays the Liskov-substitutable-interface role the
`ResourceBuilder` abstraction plays here, no Interface Segregation (one
config object with every option, used by every branch), and no Dependency
Inversion (the S3 logic reaches out and *knows about* the environment
concept directly, instead of being handed what it needs).

None of this makes the "without SOLID" version *wrong* - it will create
the same AWS resources, and for a one-off script with three resources that
never grows, it may honestly be less ceremony than this example's
14-file, 4-directory structure. SOLID is a trade: more files and more
indirection *up front*, in exchange for a codebase where new resources are
additive instead of invasive, and where the order and configuration of
each piece can be tested without spinning up all the others - a trade that
tends to pay off as the count of resources (and the number of people
editing them) grows, which is exactly why it is demonstrated here at 14
resources rather than at 2 or 3.

## 4. Two more concepts this example leans on

### 4.1 - The Builder pattern

**The idea (a classic [Gang of Four](https://en.wikipedia.org/wiki/Design_Patterns)
pattern, unrelated to AWS CDK's own use of the word "construct"):**
separate *how a complex object gets assembled, step by step* from *what
the finished object is used for*. A "builder" object collects
configuration and, only when asked, produces the finished product.

**Here, in a beginner-friendly form:** each `*ResourceBuilder` class *is*
a builder in this sense - it collects everything needed to know how to
construct one resource (the CDK calls, the naming, the tagging) behind one
method, `build()`, and produces the finished CDK construct(s) only when
the registry calls that method, in the right order, with the right
context. A fuller, more advanced version of this pattern often also adds
fluent `.with_x()` configuration methods (e.g.
`S3ResourceBuilder().with_versioning(False).with_encryption(kms_key)`) so
a caller can override defaults before calling `.build()` - this example
keeps each builder's configuration fixed (matching its source module
exactly, per [`../../CLAUDE.md`](../../CLAUDE.md)'s "do not invent
things" guardrail) and leaves fluent overrides as a natural next step for
anyone extending it.

### 4.2 - What a "construct" is (CDK-specific)

A **construct** is the AWS CDK's own term (not a general programming
concept) for a building block in a CDK app - it can be as small as one
CloudFormation resource (an `s3.Bucket`) or as large as an entire
multi-resource pattern. Every `scope.SomeConstruct(self, "Id", ...)` call
in this example's builders is creating a construct; a `Stack` (like
`EnterpriseCellStack`) is itself a construct, and a construct tree is what
`cdk synth` walks to produce a CloudFormation template. See
[AWS CDK Constructs](https://docs.aws.amazon.com/cdk/v2/guide/constructs.html)
for the official, fuller explanation - this example does not change or
extend how CDK constructs work, it only organizes *which* constructs get
created and *when*, using the SOLID/Builder ideas above.

## 5. Conditional resources and precedence, explained

Every builder has a `key` (a short string like `"vpc"` or `"lambda"`) and
an optional `depends_on` (a tuple of other builders' keys). Turning a
resource on or off is just listing its key (or not) in an environment
file's `enabled_resources` array - see
[`environments/dev.json`](environments/dev.json).

"Managing precedence" - making sure the VPC is always created before the
EC2 instance that lives inside it, no matter which order someone lists
them in a JSON file - is handled by
[`core/resource_registry.py`](core/resource_registry.py) with a
**topological sort** (specifically,
[Kahn's algorithm](https://en.wikipedia.org/wiki/Topological_sorting#Kahn's_algorithm)).
In plain language: a topological sort takes a list of tasks where some
tasks require other tasks to be finished first, and produces a valid
order to do them in - the same kind of ordering problem as "put on socks
before shoes," done automatically for any number of resources and
dependencies instead of by a person double-checking a checklist. If two
resources have no dependency relationship to each other at all (say `s3`
and `dynamodb`), their relative order doesn't matter for correctness, so
the registry just picks a consistent one (alphabetical) so the same
configuration always produces the exact same output.

### Why a missing dependency is an error, not a fix-it

If an environment file enables `"ec2"` but not `"vpc"`,
`ResourceRegistry.ordered()` raises `MissingDependencyError` immediately,
**before any CDK construct is created** - it does not silently add `"vpc"`
for you. This is a deliberate design choice: silently enabling something
the config didn't ask for could enable an unexpectedly expensive or
security-relevant resource (a whole VPC!) without whoever wrote the config
file realizing it happened. An explicit, readable error that names exactly
which key to add is safer than a "helpful" auto-fix - see
`tests/test_registry.py::test_missing_dependency_raises_instead_of_auto_enabling`
for this behavior, tested.

If `depends_on` values ever formed a cycle (`"a"` depends on `"b"` and
`"b"` depends on `"a"` - which can only happen if a builder's own
`depends_on` is wrong, since none of the 13 real builders in this example
do this), `CircularDependencyError` is raised instead, with the offending
keys named.

## 6. Cells: replicating the same stack across environments, accounts, and regions

This repository already has a tagging concept for exactly this shape -
[`shared/tagging.py`](../../shared/tagging.py)'s `cell_based`/`cell_id`
fields (see [`REQUIREMENTS.md`, section 7](../../REQUIREMENTS.md#7-tagging-policy))
- borrowed from the
[cell-based architecture](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/cell-based-architecture.html)
pattern in the AWS Well-Architected Framework: instead of one big shared
system, you run several smaller, identical, independent copies ("cells"),
each serving its own slice of traffic/tenants/regions. A failure in one
cell never spreads to another, because a cell shares nothing with the
others.

This example takes that idea literally: `EnterpriseCellStack` is designed
to be instantiated more than once - each instantiation is one cell, with
its own `cell_id`, its own physical resource names (every builder mixes
`config.cell_id` into `resource_name(...)`, so two cells never collide),
and optionally its own AWS account and/or region. `app.py` reads
`environments/<name>.json` - see
[`environments/prd.json`](environments/prd.json) - and creates one
`EnterpriseCellStack` per entry in its `"cells"` array. That file currently
lists two cells, `cell-01` in `us-east-1` and `cell-02` in `us-west-2`,
both built from the exact same Python code, with the exact same 14
resources enabled - proof that "the same resources, applied to different
environments/accounts/regions by changing values, not code" isn't just a
slogan here, it's `git diff`-able: the only difference between the two
cells is 4 lines of JSON (`cell_id`, `account`, `region`) - each cell gets
its own ECR repository, its own copy of the application image, and its
own independently-scaling ECS service.

Switching between `dev`, `stg`, and `prd` (see
[section 9](#9-running-it)) reads a different JSON file - again, no Python
changes - and each file lists a different `enabled_resources` set per
cell, so `dev` can stay cheap and minimal (6 resources, one cell) while
`stg` runs the full container/load-balancing chain
(`ecr`/`ecs`/`alb`/`nlb`, see [section 8.2](#82---scaling-1-to-3-tasks-driven-by-cpu))
with no live AWS account needed, and `prd` runs the complete 14-resource
catalog, including `ec2`, across two cells. The name you pick
(`ENTERPRISE_ENVIRONMENT`, one of the short names `dev`/`stg`/`prd` - see
[`../../REQUIREMENTS.md`, section 7](../../REQUIREMENTS.md#7-tagging-policy))
is also every cell's `environment` tag and the environment segment of every
resource name, overriding `CDK_ENVIRONMENT` - so a `stg` cell's resources are
always `learning-cdk-python-stg-cell-01-...`, never `...-dev-...`.

## 7. Directory layout

```
examples/enterprise_stack/
├── README.md                  # this file
├── app.py                     # entry point - see section 9
├── stack.py                   # EnterpriseCellStack - the only Stack class here
├── core/
│   ├── resource_builder.py     # the ResourceBuilder interface + ResourceContext
│   ├── resource_registry.py    # the catalog + topological-sort precedence engine
│   └── environment_config.py   # loads environments/<name>.json into CellConfig objects
├── builders/
│   ├── __init__.py              # build_default_registry() - the one place every builder is listed
│   ├── iam_builder.py, vpc_builder.py, ecr_builder.py, kms_builder.py, s3_builder.py,
│   │   sqs_builder.py, sns_builder.py, dynamodb_builder.py, lambda_builder.py,
│   │   ec2_builder.py, acm_builder.py, ecs_builder.py, alb_builder.py, nlb_builder.py
├── environments/
│   ├── dev.json                 # 1 cell, 6 resources, no explicit account/region
│   ├── stg.json                 # 1 cell, 13 resources (everything but ec2)
│   └── prd.json                 # 2 cells (different regions), all 14 resources each
└── tests/
    ├── test_registry.py                    # precedence/validation logic - pure Python, no CDK
    ├── test_stack_synth.py                 # aws_cdk.assertions-based synth tests
    └── test_ecs_ecr_load_balancing.py      # the ecr -> ecs (autoscaling) -> alb/nlb chain
```

## 8. The 14 resources included

| Key | AWS service | Based on | `depends_on` |
|---|---|---|---|
| `iam` | IAM | `modules/01_iam` | - |
| `vpc` | VPC | `modules/03_vpc` | - |
| `ecr` | ECR | `modules/14_ecr` | - |
| `kms` | KMS | `modules/08_kms` | - |
| `s3` | S3 | `modules/12_s3` | - |
| `sqs` | SQS | `modules/26_sqs` | - |
| `sns` | SNS | `modules/27_sns` | - |
| `dynamodb` | DynamoDB | `modules/21_dynamodb` | - |
| `lambda` | Lambda | `modules/17_lambda` | `iam` (reuses its role) |
| `ec2` | EC2 | `modules/13_ec2` | `vpc` (reuses it) |
| `acm` | ACM | `modules/11_acm` | - |
| `ecs` | ECS (Fargate) | `modules/15_ecs` | `vpc`, `ecr` (runs its image, reuses the VPC) |
| `alb` | Application Load Balancer | `modules/30_alb` | `vpc`, `ecs` (exposes its service) |
| `nlb` | Network Load Balancer | `modules/31_nlb` | `vpc`, `ecs` (exposes its service) |

Every construct call is the exact one already verified in the listed
module - see [`../../CLAUDE.md`, section 4](../../CLAUDE.md#4-do-not-invent-things-the-core-guardrail).
The only differences from the standalone module are: (a) resource names
include `config.cell_id`, (b) `lambda`/`ec2`/`ecs`/`alb`/`nlb` reuse a
shared IAM role, VPC, or ECS service instead of each creating/exposing
their own (see [section 2.5](#25---d-dependency-inversion-principle)),
(c) `alb`/`nlb`'s load-balancer/target-group *physical* names use a
shorter naming scheme than the tag - see the comment in
`builders/alb_builder.py` for why (a real, AWS-enforced 32-character
limit this example's own `prd.json` hit and fixed during development),
and (d) `ecs` runs a real application image from `ecr` instead of the
public `nginx:alpine` image `modules/15_ecs` uses - see
[section 8.1](#81---the-ecr-resource-copying-an-image-in).

### 8.1 - The ecr resource: copying an image in

`ecr` (`builders/ecr_builder.py`) creates one private ECR repository,
meant to hold a copy of the public
[`aeciopires/mytoolkit`](https://hub.docker.com/r/aeciopires/mytoolkit)
image - the same `ecr.Repository` call verified in
[`modules/14_ecr/stack.py`](../../modules/14_ecr/stack.py). `ecs` then
points its task definition's container at that repository with
`ecs.ContainerImage.from_ecr_repository(repository, "latest")` (verified
against the `aws-cdk-lib` source: `ContainerImage.fromEcrRepository` in
`aws-ecs/lib/container-image.ts`), instead of pulling a public image
directly.

**CDK/CloudFormation cannot copy a Docker Hub image into ECR for you** -
that is a `docker pull`/`docker push` operation, not an infrastructure
one, the same reason [`modules/14_ecr/README.md`](../../modules/14_ecr/README.md)
documents its own image push as a manual step. After deploying the `ecr`
resource once, copy the image in yourself:

```bash
aws ecr get-login-password --region <region> | \
    docker login --username AWS --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
docker pull docker.io/aeciopires/mytoolkit:latest
docker tag docker.io/aeciopires/mytoolkit:latest <account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest
docker push <account-id>.dkr.ecr.<region>.amazonaws.com/<repository-name>:latest
```

`<repository-name>` is printed by `cdk deploy`'s stack outputs, or found
with `aws ecr describe-repositories` - it follows this cell's usual naming
convention, e.g. `learning-cdk-python-stg-cell-01-ecr-mytoolkit`. Until
an image is actually pushed, `cdk synth`/`cdk deploy` for `ecs` still
succeed (CloudFormation does not validate that an ECR repository is
non-empty when creating a task definition that references it), but any
task the service tries to launch will fail to start, the same way it would
against a real, empty ECR repository - see
[section 12](#12-known-limitations-and-honest-scope).

### 8.2 - Scaling: 1 to 3 tasks, driven by CPU

`ecs` (`builders/ecs_builder.py`) enables
[Application Auto Scaling](https://docs.aws.amazon.com/autoscaling/application/userguide/what-is-application-auto-scaling.html)
on its Fargate service with two calls, both verified directly against the
`aws-cdk-lib` TypeScript source (`aws-ecs/lib/base/base-service.ts` and
`aws-ecs/lib/base/scalable-task-count.ts`, since the rendered API
reference website did not load as static HTML for this session - see
[`../../CLAUDE.md`, section 4, point 6](../../CLAUDE.md#4-do-not-invent-things-the-core-guardrail)):

```python
scaling = service.auto_scale_task_count(min_capacity=1, max_capacity=3)
scaling.scale_on_cpu_utilization(
    "CpuScaling",
    target_utilization_percent=70,
    scale_in_cooldown=Duration.seconds(60),
    scale_out_cooldown=Duration.seconds(60),
)
```

`auto_scale_task_count()` creates an `AWS::ApplicationAutoScaling::ScalableTarget`
capped between `EcsResourceBuilder.MIN_TASK_COUNT` (1) and
`EcsResourceBuilder.MAX_TASK_COUNT` (3) tasks.
`scale_on_cpu_utilization()` then creates a target-tracking
`AWS::ApplicationAutoScaling::ScalingPolicy` using the predefined
`ECSServiceAverageCPUUtilization` metric: whenever the service's average
CPU utilization across all running tasks is above 70%, Application Auto
Scaling adds tasks (up to the maximum of 3); when it's comfortably below,
it removes them (down to the minimum of 1) - the 60-second cooldowns keep
it from reacting to every brief spike or dip. `alb`/`nlb`, when enabled,
each register this exact service (not a fixed task count) in their target
group via `target_group.add_target(service)` - AWS keeps each target
group's registered targets in sync as the service scales, so no
autoscaling-specific code is needed on the load-balancer side at all.

## 9. Running it

```bash
# from the repository root
export ENTERPRISE_ENVIRONMENT=dev              # or stg, or prd (short names only)

uv run cdk list  --app "uv run python examples/enterprise_stack/app.py"
uv run cdk synth --app "uv run python examples/enterprise_stack/app.py"
uv run cdk diff  --app "uv run python examples/enterprise_stack/app.py"   # what a deploy would change - creates nothing

# against floci (see ../../REQUIREMENTS.md section 5), same as any module:
docker compose up -d floci
cp .env.example .env; set -a; source .env; set +a   # or export the 4 AWS_* vars by hand
uv run cdk bootstrap   # once per floci instance - see ../../REQUIREMENTS.md section 5.7
uv run cdk deploy --all --app "uv run python examples/enterprise_stack/app.py" --require-approval never --method=direct
uv run cdk destroy --all --app "uv run python examples/enterprise_stack/app.py"
uv run python scripts/floci_prune.py --apply   # floci only: deletes the VPC floci leaves behind (../../REQUIREMENTS.md section 5.9)
```

Each environment's cells are separate stacks, named
`Enterprise<Environment><Cell>Stack`:

| `ENTERPRISE_ENVIRONMENT` | Stacks | Account / region |
|---|---|---|
| `dev` | `EnterpriseDevCell01Stack` | whatever your credentials point at (environment-agnostic) |
| `stg` | `EnterpriseStgCell01Stack` | whatever your credentials point at (environment-agnostic) |
| `prd` | `EnterprisePrdCell01Stack`, `EnterprisePrdCell02Stack` | `111111111111` / `us-east-1` and `us-west-2` (from `prd.json`) |

The environment is part of the stack id on purpose: with the cell id
alone, `dev`'s and `stg`'s `cell-01` would be the *same* CloudFormation
stack, and deploying one environment would replace the other's resources
instead of adding its own.

**`prd` on floci.** `prd.json` pins its cells to account `111111111111` in
two regions. floci treats an access key id of exactly 12 digits as the
account id ([floci - Multi-Account Isolation](https://floci.io/floci/configuration/multi-account/)),
so using `111111111111` as the access key makes every call act as that
account - fully isolated from the default `000000000000` one - and each
region needs its own bootstrap:

```bash
export ENTERPRISE_ENVIRONMENT=prd AWS_ACCESS_KEY_ID=111111111111
uv run cdk bootstrap aws://111111111111/us-east-1 aws://111111111111/us-west-2
uv run cdk deploy --all --app "uv run python examples/enterprise_stack/app.py" --require-approval never --method=direct
# to remove it again - prd's VPCs live in two regions:
uv run cdk destroy --all --app "uv run python examples/enterprise_stack/app.py"
uv run python scripts/floci_prune.py --region us-east-1 --region us-west-2 --apply
```

(On real AWS, replace the placeholder account in `prd.json` with yours and
use real credentials for it instead.)

**Re-running a deploy is safe.** With `--method=direct`, deploying an
unchanged environment again reports `(no changes)` for every cell and
creates nothing new - see
[`../../REQUIREMENTS.md`, section 5.8](../../REQUIREMENTS.md#58---re-running-cdk-deploy-on-floci-without-duplicating-resources)
for why the flag matters on floci.

Once these commands are familiar, `make cdk-synth EXAMPLE=enterprise
ENV=stg` and `make cdk-deploy EXAMPLE=enterprise ENV=stg` are optional
shortcuts for them (they also start floci first, if it isn't running, and
for `ENV=prd` they act as `prd.json`'s account and bootstrap its regions
for you) - see
[`../../REQUIREMENTS.md`, section 5.6](../../REQUIREMENTS.md#56---optional-make-shortcuts-for-floci-and-the-cdk).

All three environments synthesize with no AWS credentials at all. `dev`
and `stg` are environment-agnostic, exactly like every
`modules/NN_service` stack (see
[`../../REQUIREMENTS.md`, section 9](../../REQUIREMENTS.md#9-flexible-account-and-region)),
and `stg` in particular exercises the full `ecr` → `ecs` (autoscaling) →
`alb`/`nlb` chain. `prd` names explicit accounts and regions, but nothing
in it needs a synth-time lookup: the `ec2` builder's AMI is resolved by
EC2 at launch (`resolve:ssm:`), not looked up while synthesizing - see
[section 12](#12-known-limitations-and-honest-scope).

<!-- BEGIN resource-commands (generated by scripts/resource_commands.py) -->
### 9.1 - List every resource with the AWS CLI

Every resource each cell creates, one `aws` command each, parametrized by
environment (`ENV`), region (`REGION`) and - where a command builds an ARN -
account (`ACCOUNT`). Each cell is its own stack (`STACK`), so there's one
block per environment and cell. A resource without a name of its own is
looked up through the stack by its *logical id* (`pid <LogicalId>`), which
is the same in every environment. These blocks are generated from each
stack's template by
[`../../scripts/resource_commands.py`](../../scripts/resource_commands.py) -
see [`../../REQUIREMENTS.md`, section 5.10](../../REQUIREMENTS.md#510---listing-every-resource-a-stack-created);
`make cdk-resources EXAMPLE=enterprise ENV=<dev|stg|prd>` runs the same
commands for you.

**`dev`** - `EnterpriseDevCell01Stack`:

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=dev REGION=us-east-1
STACK=EnterpriseDevCell01Stack
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::DynamoDB::Table (TableCD117FA1)
aws dynamodb describe-table --table-name "${PRODUCT}-${ENV}-cell-01-ddb-items" --query "Table.[TableName,TableStatus]" --output table --region "$REGION"
# AWS::IAM::Role (AppRoleDC883459)
aws iam get-role --role-name "${PRODUCT}-${ENV}-cell-01-role-app-task" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::IAM::ManagedPolicy (S3ReadOnlyPolicyE083D854)
aws iam list-policies --scope Local --query "Policies[?PolicyName=='${PRODUCT}-${ENV}-cell-01-policy-s3-read-only'].[PolicyName,Arn]" --output table --region "$REGION"
# AWS::S3::Bucket (AppDataBucket857FA106)
aws s3api list-buckets --query "Buckets[?Name=='${PRODUCT}-${ENV}-cell-01-s3-app-data'].[Name,CreationDate]" --output table --region "$REGION"
# AWS::IAM::Role (CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)
aws iam get-role --role-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::Lambda::Function (CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)
aws lambda get-function --function-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# AWS::SQS::Queue (OrdersDeadLetterQueue91101596)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-01-sqs-orders-dlq" --query "QueueUrl" --output table --region "$REGION"
# AWS::SQS::Queue (OrdersQueue3DFA1D51)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-01-sqs-orders" --query "QueueUrl" --output table --region "$REGION"
# AWS::EC2::VPC (Vpc8378EB38)
aws ec2 describe-vpcs --vpc-ids "$(pid Vpc8378EB38)" --query "Vpcs[].[VpcId,CidrBlock,State]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet1Subnet2BB74ED7)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet1Subnet2BB74ED7)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet1RouteTable15C15F8E)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet1RouteTable15C15F8E)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet2SubnetE34B022A)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet2SubnetE34B022A)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet2RouteTableC5A6DF77)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet2RouteTableC5A6DF77)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcprivateSubnet1SubnetCEAD3716)
aws ec2 describe-subnets --subnet-ids "$(pid VpcprivateSubnet1SubnetCEAD3716)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcprivateSubnet1RouteTable1979EACB)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcprivateSubnet1RouteTable1979EACB)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcprivateSubnet2Subnet2DE7549C)
aws ec2 describe-subnets --subnet-ids "$(pid VpcprivateSubnet2Subnet2DE7549C)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcprivateSubnet2RouteTable4D0FFC8C)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcprivateSubnet2RouteTable4D0FFC8C)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::InternetGateway (VpcIGWD7BA715C)
aws ec2 describe-internet-gateways --internet-gateway-ids "$(pid VpcIGWD7BA715C)" --query "InternetGateways[].[InternetGatewayId,Attachments[0].VpcId]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AppSecurityGroupC396D536)
aws ec2 describe-security-groups --group-ids "$(pid AppSecurityGroupC396D536)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::Lambda::Function (HelloFunctionD909AE8C)
aws lambda get-function --function-name "${PRODUCT}-${ENV}-cell-01-lambda-hello" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::S3::BucketPolicy AppDataBucketPolicyE31553DB - shown by its bucket
#   Custom::S3AutoDeleteObjects AppDataBucketAutoDeleteObjectsCustomResourceD2BD59B3 - shown by the provider Lambda function and role listed here
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet1RouteTableAssociation4E83B6E4 - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet1DefaultRouteB88F9E93 - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet2RouteTableAssociationCCE257FF - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet2DefaultRoute732F0BEB - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcprivateSubnet1RouteTableAssociationEEBD93CE - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcprivateSubnet2RouteTableAssociationB691E645 - shown by its route table
#   AWS::EC2::VPCGatewayAttachment VpcVPCGWBF912B6E - shown by its internet gateway
```

**`stg`** - `EnterpriseStgCell01Stack`:

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=stg REGION=us-east-1
STACK=EnterpriseStgCell01Stack
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::CertificateManager::Certificate (AppCertificateE0EB6E86)
aws acm list-certificates --query "CertificateSummaryList[?DomainName=='${PRODUCT}.example.com'].[DomainName,Status,CertificateArn]" --output table --region "$REGION"
# AWS::DynamoDB::Table (TableCD117FA1)
aws dynamodb describe-table --table-name "${PRODUCT}-${ENV}-cell-01-ddb-items" --query "Table.[TableName,TableStatus]" --output table --region "$REGION"
# AWS::ECR::Repository (AppRepositoryB584A693)
aws ecr describe-repositories --repository-names "${PRODUCT}-${ENV}-cell-01-ecr-mytoolkit" --query "repositories[].[repositoryName,repositoryUri]" --output table --region "$REGION"
# AWS::IAM::Role (AppRoleDC883459)
aws iam get-role --role-name "${PRODUCT}-${ENV}-cell-01-role-app-task" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::IAM::ManagedPolicy (S3ReadOnlyPolicyE083D854)
aws iam list-policies --scope Local --query "Policies[?PolicyName=='${PRODUCT}-${ENV}-cell-01-policy-s3-read-only'].[PolicyName,Arn]" --output table --region "$REGION"
# AWS::KMS::Key (AppKey51DFC408)
aws kms describe-key --key-id "$(pid AppKey51DFC408)" --query "KeyMetadata.[KeyId,KeyState]" --output table --region "$REGION"
# AWS::KMS::Alias (AppKeyAliasDEC3B4C2)
aws kms list-aliases --query "Aliases[?AliasName=='alias/${PRODUCT}-${ENV}-cell-01-kms-app'].[AliasName,TargetKeyId]" --output table --region "$REGION"
# AWS::S3::Bucket (AppDataBucket857FA106)
aws s3api list-buckets --query "Buckets[?Name=='${PRODUCT}-${ENV}-cell-01-s3-app-data'].[Name,CreationDate]" --output table --region "$REGION"
# AWS::IAM::Role (CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)
aws iam get-role --role-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::Lambda::Function (CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)
aws lambda get-function --function-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# AWS::SQS::Queue (NotificationsQueue3B766469)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-01-sqs-notifications" --query "QueueUrl" --output table --region "$REGION"
# AWS::SNS::Subscription (NotificationsQueueEnterpriseStgCell01StackNotificationsTopic205590202AEFF35B)
aws sns list-subscriptions-by-topic --topic-arn "$(pid NotificationsTopicE4AF40A8)" --query "Subscriptions[].[Protocol,Endpoint]" --output table --region "$REGION"
# AWS::SNS::Topic (NotificationsTopicE4AF40A8)
aws sns get-topic-attributes --topic-arn "arn:aws:sns:${REGION}:${ACCOUNT}:${PRODUCT}-${ENV}-cell-01-sns-notifications" --query "Attributes.TopicArn" --output table --region "$REGION"
# AWS::SQS::Queue (OrdersDeadLetterQueue91101596)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-01-sqs-orders-dlq" --query "QueueUrl" --output table --region "$REGION"
# AWS::SQS::Queue (OrdersQueue3DFA1D51)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-01-sqs-orders" --query "QueueUrl" --output table --region "$REGION"
# AWS::EC2::VPC (Vpc8378EB38)
aws ec2 describe-vpcs --vpc-ids "$(pid Vpc8378EB38)" --query "Vpcs[].[VpcId,CidrBlock,State]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet1Subnet2BB74ED7)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet1Subnet2BB74ED7)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet1RouteTable15C15F8E)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet1RouteTable15C15F8E)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet2SubnetE34B022A)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet2SubnetE34B022A)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet2RouteTableC5A6DF77)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet2RouteTableC5A6DF77)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcprivateSubnet1SubnetCEAD3716)
aws ec2 describe-subnets --subnet-ids "$(pid VpcprivateSubnet1SubnetCEAD3716)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcprivateSubnet1RouteTable1979EACB)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcprivateSubnet1RouteTable1979EACB)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcprivateSubnet2Subnet2DE7549C)
aws ec2 describe-subnets --subnet-ids "$(pid VpcprivateSubnet2Subnet2DE7549C)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcprivateSubnet2RouteTable4D0FFC8C)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcprivateSubnet2RouteTable4D0FFC8C)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::InternetGateway (VpcIGWD7BA715C)
aws ec2 describe-internet-gateways --internet-gateway-ids "$(pid VpcIGWD7BA715C)" --query "InternetGateways[].[InternetGatewayId,Attachments[0].VpcId]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AppSecurityGroupC396D536)
aws ec2 describe-security-groups --group-ids "$(pid AppSecurityGroupC396D536)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::ECS::Cluster (ClusterEB0386A7)
aws ecs describe-clusters --clusters "${PRODUCT}-${ENV}-cell-01-ecs-cluster" --query "clusters[].[clusterName,status]" --output table --region "$REGION"
# AWS::IAM::Role (AppTaskDefinitionTaskRole96BC2009)
aws iam get-role --role-name "$(pid AppTaskDefinitionTaskRole96BC2009)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::ECS::TaskDefinition (AppTaskDefinitionCBC902A9)
aws ecs describe-task-definition --task-definition "${PRODUCT}-${ENV}-cell-01-ecs-app-task" --query "taskDefinition.[family,revision,status]" --output table --region "$REGION"
# AWS::IAM::Role (AppTaskDefinitionExecutionRoleE1F9B422)
aws iam get-role --role-name "$(pid AppTaskDefinitionExecutionRoleE1F9B422)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::ECS::Service (AppServiceA2F9036C)
aws ecs describe-services --cluster "${PRODUCT}-${ENV}-cell-01-ecs-cluster" --services "${PRODUCT}-${ENV}-cell-01-ecs-app-service" --query "services[].[serviceName,status,desiredCount]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AppServiceSecurityGroupCD648D82)
aws ec2 describe-security-groups --group-ids "$(pid AppServiceSecurityGroupCD648D82)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::ApplicationAutoScaling::ScalableTarget (AppServiceTaskCountTarget8D11C093)
aws application-autoscaling describe-scalable-targets --service-namespace ecs --query "ScalableTargets[?contains(ResourceId, '${PRODUCT}-${ENV}-cell-01-ecs-cluster')].[ResourceId,MinCapacity,MaxCapacity]" --output table --region "$REGION"
# AWS::ApplicationAutoScaling::ScalingPolicy (AppServiceTaskCountTargetCpuScaling8D6A969B)
aws application-autoscaling describe-scaling-policies --service-namespace ecs --query "ScalingPolicies[?contains(ResourceId, '${PRODUCT}-${ENV}-cell-01-ecs-cluster')].[PolicyName,PolicyType]" --output table --region "$REGION"
# AWS::Lambda::Function (HelloFunctionD909AE8C)
aws lambda get-function --function-name "${PRODUCT}-${ENV}-cell-01-lambda-hello" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::LoadBalancer (Alb16C2F182)
aws elbv2 describe-load-balancers --load-balancer-arns "$(pid Alb16C2F182)" --query "LoadBalancers[].[LoadBalancerName,Type,State.Code]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AlbSecurityGroup580F65A6)
aws ec2 describe-security-groups --group-ids "$(pid AlbSecurityGroup580F65A6)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::TargetGroup (AlbTargetGroup40F9FCBA)
aws elbv2 describe-target-groups --target-group-arns "$(pid AlbTargetGroup40F9FCBA)" --query "TargetGroups[].[TargetGroupName,Port,TargetType]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::Listener (AlbListenerDFCDF14C)
aws elbv2 describe-listeners --listener-arns "$(pid AlbListenerDFCDF14C)" --query "Listeners[].[Port,Protocol]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::LoadBalancer (NlbBCDB97FE)
aws elbv2 describe-load-balancers --load-balancer-arns "$(pid NlbBCDB97FE)" --query "LoadBalancers[].[LoadBalancerName,Type,State.Code]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::TargetGroup (NlbTargetGroupB5099BEB)
aws elbv2 describe-target-groups --target-group-arns "$(pid NlbTargetGroupB5099BEB)" --query "TargetGroups[].[TargetGroupName,Port,TargetType]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::Listener (NlbListenerA43610D3)
aws elbv2 describe-listeners --listener-arns "$(pid NlbListenerA43610D3)" --query "Listeners[].[Port,Protocol]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::S3::BucketPolicy AppDataBucketPolicyE31553DB - shown by its bucket
#   Custom::S3AutoDeleteObjects AppDataBucketAutoDeleteObjectsCustomResourceD2BD59B3 - shown by the provider Lambda function and role listed here
#   AWS::SQS::QueuePolicy NotificationsQueuePolicy71DD684A - shown by its queue
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet1RouteTableAssociation4E83B6E4 - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet1DefaultRouteB88F9E93 - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet2RouteTableAssociationCCE257FF - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet2DefaultRoute732F0BEB - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcprivateSubnet1RouteTableAssociationEEBD93CE - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcprivateSubnet2RouteTableAssociationB691E645 - shown by its route table
#   AWS::EC2::VPCGatewayAttachment VpcVPCGWBF912B6E - shown by its internet gateway
#   AWS::IAM::Policy AppTaskDefinitionExecutionRoleDefaultPolicyA9233178 - shown by its IAM role
#   AWS::EC2::SecurityGroupIngress AppServiceSecurityGroupfromEnterpriseStgCell01StackAlbSecurityGroup2464592A80A338C1F7 - shown by its security group
#   AWS::EC2::SecurityGroupEgress AlbSecurityGrouptoEnterpriseStgCell01StackAppServiceSecurityGroupCCE4B47080AC0270B0 - shown by its security group
```

**On floci** (2.1.0), CloudFormation records `AWS::ApplicationAutoScaling::ScalableTarget`, `AWS::ApplicationAutoScaling::ScalingPolicy` without creating it, so those commands find nothing there - they work on real AWS. See [`REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).

**`prd`** - on floci, act as `prd.json`'s account first (see above):
`export AWS_ACCESS_KEY_ID=111111111111`. Cell 01, `EnterprisePrdCell01Stack`
in `us-east-1`:

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=prd REGION=us-east-1
STACK=EnterprisePrdCell01Stack
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::CertificateManager::Certificate (AppCertificateE0EB6E86)
aws acm list-certificates --query "CertificateSummaryList[?DomainName=='${PRODUCT}.example.com'].[DomainName,Status,CertificateArn]" --output table --region "$REGION"
# AWS::DynamoDB::Table (TableCD117FA1)
aws dynamodb describe-table --table-name "${PRODUCT}-${ENV}-cell-01-ddb-items" --query "Table.[TableName,TableStatus]" --output table --region "$REGION"
# AWS::ECR::Repository (AppRepositoryB584A693)
aws ecr describe-repositories --repository-names "${PRODUCT}-${ENV}-cell-01-ecr-mytoolkit" --query "repositories[].[repositoryName,repositoryUri]" --output table --region "$REGION"
# AWS::IAM::Role (AppRoleDC883459)
aws iam get-role --role-name "${PRODUCT}-${ENV}-cell-01-role-app-task" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::IAM::ManagedPolicy (S3ReadOnlyPolicyE083D854)
aws iam list-policies --scope Local --query "Policies[?PolicyName=='${PRODUCT}-${ENV}-cell-01-policy-s3-read-only'].[PolicyName,Arn]" --output table --region "$REGION"
# AWS::KMS::Key (AppKey51DFC408)
aws kms describe-key --key-id "$(pid AppKey51DFC408)" --query "KeyMetadata.[KeyId,KeyState]" --output table --region "$REGION"
# AWS::KMS::Alias (AppKeyAliasDEC3B4C2)
aws kms list-aliases --query "Aliases[?AliasName=='alias/${PRODUCT}-${ENV}-cell-01-kms-app'].[AliasName,TargetKeyId]" --output table --region "$REGION"
# AWS::S3::Bucket (AppDataBucket857FA106)
aws s3api list-buckets --query "Buckets[?Name=='${PRODUCT}-${ENV}-cell-01-s3-app-data'].[Name,CreationDate]" --output table --region "$REGION"
# AWS::IAM::Role (CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)
aws iam get-role --role-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::Lambda::Function (CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)
aws lambda get-function --function-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# AWS::SQS::Queue (NotificationsQueue3B766469)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-01-sqs-notifications" --query "QueueUrl" --output table --region "$REGION"
# AWS::SNS::Subscription (NotificationsQueueEnterprisePrdCell01StackNotificationsTopic1E64E687696575D6)
aws sns list-subscriptions-by-topic --topic-arn "$(pid NotificationsTopicE4AF40A8)" --query "Subscriptions[].[Protocol,Endpoint]" --output table --region "$REGION"
# AWS::SNS::Topic (NotificationsTopicE4AF40A8)
aws sns get-topic-attributes --topic-arn "arn:aws:sns:${REGION}:${ACCOUNT}:${PRODUCT}-${ENV}-cell-01-sns-notifications" --query "Attributes.TopicArn" --output table --region "$REGION"
# AWS::SQS::Queue (OrdersDeadLetterQueue91101596)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-01-sqs-orders-dlq" --query "QueueUrl" --output table --region "$REGION"
# AWS::SQS::Queue (OrdersQueue3DFA1D51)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-01-sqs-orders" --query "QueueUrl" --output table --region "$REGION"
# AWS::EC2::VPC (Vpc8378EB38)
aws ec2 describe-vpcs --vpc-ids "$(pid Vpc8378EB38)" --query "Vpcs[].[VpcId,CidrBlock,State]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet1Subnet2BB74ED7)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet1Subnet2BB74ED7)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet1RouteTable15C15F8E)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet1RouteTable15C15F8E)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet2SubnetE34B022A)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet2SubnetE34B022A)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet2RouteTableC5A6DF77)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet2RouteTableC5A6DF77)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcprivateSubnet1SubnetCEAD3716)
aws ec2 describe-subnets --subnet-ids "$(pid VpcprivateSubnet1SubnetCEAD3716)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcprivateSubnet1RouteTable1979EACB)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcprivateSubnet1RouteTable1979EACB)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcprivateSubnet2Subnet2DE7549C)
aws ec2 describe-subnets --subnet-ids "$(pid VpcprivateSubnet2Subnet2DE7549C)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcprivateSubnet2RouteTable4D0FFC8C)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcprivateSubnet2RouteTable4D0FFC8C)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::InternetGateway (VpcIGWD7BA715C)
aws ec2 describe-internet-gateways --internet-gateway-ids "$(pid VpcIGWD7BA715C)" --query "InternetGateways[].[InternetGatewayId,Attachments[0].VpcId]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AppSecurityGroupC396D536)
aws ec2 describe-security-groups --group-ids "$(pid AppSecurityGroupC396D536)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (InstanceSecurityGroup896E10BF)
aws ec2 describe-security-groups --group-ids "$(pid InstanceSecurityGroup896E10BF)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::IAM::Role (InstanceRole3CCE2F1D)
aws iam get-role --role-name "${PRODUCT}-${ENV}-cell-01-role-ec2-instance" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::IAM::InstanceProfile (AppInstanceInstanceProfileC6B6EFAA)
aws iam get-instance-profile --instance-profile-name "$(pid AppInstanceInstanceProfileC6B6EFAA)" --query "InstanceProfile.[InstanceProfileName,Arn]" --output table --region "$REGION"
# AWS::EC2::Instance (AppInstance13C82D50)
aws ec2 describe-instances --instance-ids "$(pid AppInstance13C82D50)" --query "Reservations[].Instances[].[InstanceId,InstanceType,State.Name]" --output table --region "$REGION"
# AWS::ECS::Cluster (ClusterEB0386A7)
aws ecs describe-clusters --clusters "${PRODUCT}-${ENV}-cell-01-ecs-cluster" --query "clusters[].[clusterName,status]" --output table --region "$REGION"
# AWS::IAM::Role (AppTaskDefinitionTaskRole96BC2009)
aws iam get-role --role-name "$(pid AppTaskDefinitionTaskRole96BC2009)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::ECS::TaskDefinition (AppTaskDefinitionCBC902A9)
aws ecs describe-task-definition --task-definition "${PRODUCT}-${ENV}-cell-01-ecs-app-task" --query "taskDefinition.[family,revision,status]" --output table --region "$REGION"
# AWS::IAM::Role (AppTaskDefinitionExecutionRoleE1F9B422)
aws iam get-role --role-name "$(pid AppTaskDefinitionExecutionRoleE1F9B422)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::ECS::Service (AppServiceA2F9036C)
aws ecs describe-services --cluster "${PRODUCT}-${ENV}-cell-01-ecs-cluster" --services "${PRODUCT}-${ENV}-cell-01-ecs-app-service" --query "services[].[serviceName,status,desiredCount]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AppServiceSecurityGroupCD648D82)
aws ec2 describe-security-groups --group-ids "$(pid AppServiceSecurityGroupCD648D82)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::ApplicationAutoScaling::ScalableTarget (AppServiceTaskCountTarget8D11C093)
aws application-autoscaling describe-scalable-targets --service-namespace ecs --query "ScalableTargets[?contains(ResourceId, '${PRODUCT}-${ENV}-cell-01-ecs-cluster')].[ResourceId,MinCapacity,MaxCapacity]" --output table --region "$REGION"
# AWS::ApplicationAutoScaling::ScalingPolicy (AppServiceTaskCountTargetCpuScaling8D6A969B)
aws application-autoscaling describe-scaling-policies --service-namespace ecs --query "ScalingPolicies[?contains(ResourceId, '${PRODUCT}-${ENV}-cell-01-ecs-cluster')].[PolicyName,PolicyType]" --output table --region "$REGION"
# AWS::Lambda::Function (HelloFunctionD909AE8C)
aws lambda get-function --function-name "${PRODUCT}-${ENV}-cell-01-lambda-hello" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::LoadBalancer (Alb16C2F182)
aws elbv2 describe-load-balancers --load-balancer-arns "$(pid Alb16C2F182)" --query "LoadBalancers[].[LoadBalancerName,Type,State.Code]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AlbSecurityGroup580F65A6)
aws ec2 describe-security-groups --group-ids "$(pid AlbSecurityGroup580F65A6)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::TargetGroup (AlbTargetGroup40F9FCBA)
aws elbv2 describe-target-groups --target-group-arns "$(pid AlbTargetGroup40F9FCBA)" --query "TargetGroups[].[TargetGroupName,Port,TargetType]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::Listener (AlbListenerDFCDF14C)
aws elbv2 describe-listeners --listener-arns "$(pid AlbListenerDFCDF14C)" --query "Listeners[].[Port,Protocol]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::LoadBalancer (NlbBCDB97FE)
aws elbv2 describe-load-balancers --load-balancer-arns "$(pid NlbBCDB97FE)" --query "LoadBalancers[].[LoadBalancerName,Type,State.Code]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::TargetGroup (NlbTargetGroupB5099BEB)
aws elbv2 describe-target-groups --target-group-arns "$(pid NlbTargetGroupB5099BEB)" --query "TargetGroups[].[TargetGroupName,Port,TargetType]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::Listener (NlbListenerA43610D3)
aws elbv2 describe-listeners --listener-arns "$(pid NlbListenerA43610D3)" --query "Listeners[].[Port,Protocol]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::S3::BucketPolicy AppDataBucketPolicyE31553DB - shown by its bucket
#   Custom::S3AutoDeleteObjects AppDataBucketAutoDeleteObjectsCustomResourceD2BD59B3 - shown by the provider Lambda function and role listed here
#   AWS::SQS::QueuePolicy NotificationsQueuePolicy71DD684A - shown by its queue
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet1RouteTableAssociation4E83B6E4 - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet1DefaultRouteB88F9E93 - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet2RouteTableAssociationCCE257FF - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet2DefaultRoute732F0BEB - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcprivateSubnet1RouteTableAssociationEEBD93CE - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcprivateSubnet2RouteTableAssociationB691E645 - shown by its route table
#   AWS::EC2::VPCGatewayAttachment VpcVPCGWBF912B6E - shown by its internet gateway
#   AWS::IAM::Policy AppTaskDefinitionExecutionRoleDefaultPolicyA9233178 - shown by its IAM role
#   AWS::EC2::SecurityGroupIngress AppServiceSecurityGroupfromEnterprisePrdCell01StackAlbSecurityGroupC0CD5D3C80B855E637 - shown by its security group
#   AWS::EC2::SecurityGroupEgress AlbSecurityGrouptoEnterprisePrdCell01StackAppServiceSecurityGroup2D9C7A8D80EA648BB4 - shown by its security group
```

**On floci** (2.1.0), CloudFormation records `AWS::ApplicationAutoScaling::ScalableTarget`, `AWS::ApplicationAutoScaling::ScalingPolicy` without creating it, so those commands find nothing there - they work on real AWS. See [`REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).

Cell 02, `EnterprisePrdCell02Stack` in `us-west-2`:

```bash
# Match these to your deployment: CDK_PRODUCT and CDK_ENVIRONMENT in .env, and
# the region you deployed to (floci: the one in .env).
PRODUCT=learning-cdk-python ENV=prd REGION=us-west-2
STACK=EnterprisePrdCell02Stack
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
# Physical id of one of the stack's resources, by its logical id - the same in
# every environment. A second argument names another (e.g. nested) stack.
pid() { aws cloudformation describe-stack-resource --stack-name "${2:-$STACK}" \
  --logical-resource-id "$1" --region "$REGION" \
  --query StackResourceDetail.PhysicalResourceId --output text; }

# Every resource the stack created - type, logical id, physical id, status:
aws cloudformation describe-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResources[].[ResourceType,LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
  --output table

# AWS::CertificateManager::Certificate (AppCertificateE0EB6E86)
aws acm list-certificates --query "CertificateSummaryList[?DomainName=='${PRODUCT}.example.com'].[DomainName,Status,CertificateArn]" --output table --region "$REGION"
# AWS::DynamoDB::Table (TableCD117FA1)
aws dynamodb describe-table --table-name "${PRODUCT}-${ENV}-cell-02-ddb-items" --query "Table.[TableName,TableStatus]" --output table --region "$REGION"
# AWS::ECR::Repository (AppRepositoryB584A693)
aws ecr describe-repositories --repository-names "${PRODUCT}-${ENV}-cell-02-ecr-mytoolkit" --query "repositories[].[repositoryName,repositoryUri]" --output table --region "$REGION"
# AWS::IAM::Role (AppRoleDC883459)
aws iam get-role --role-name "${PRODUCT}-${ENV}-cell-02-role-app-task" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::IAM::ManagedPolicy (S3ReadOnlyPolicyE083D854)
aws iam list-policies --scope Local --query "Policies[?PolicyName=='${PRODUCT}-${ENV}-cell-02-policy-s3-read-only'].[PolicyName,Arn]" --output table --region "$REGION"
# AWS::KMS::Key (AppKey51DFC408)
aws kms describe-key --key-id "$(pid AppKey51DFC408)" --query "KeyMetadata.[KeyId,KeyState]" --output table --region "$REGION"
# AWS::KMS::Alias (AppKeyAliasDEC3B4C2)
aws kms list-aliases --query "Aliases[?AliasName=='alias/${PRODUCT}-${ENV}-cell-02-kms-app'].[AliasName,TargetKeyId]" --output table --region "$REGION"
# AWS::S3::Bucket (AppDataBucket857FA106)
aws s3api list-buckets --query "Buckets[?Name=='${PRODUCT}-${ENV}-cell-02-s3-app-data'].[Name,CreationDate]" --output table --region "$REGION"
# AWS::IAM::Role (CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)
aws iam get-role --role-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderRole3B1BD092)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::Lambda::Function (CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)
aws lambda get-function --function-name "$(pid CustomS3AutoDeleteObjectsCustomResourceProviderHandler9D90184F)" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# AWS::SQS::Queue (NotificationsQueue3B766469)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-02-sqs-notifications" --query "QueueUrl" --output table --region "$REGION"
# AWS::SNS::Subscription (NotificationsQueueEnterprisePrdCell02StackNotificationsTopic29EA79AF50D18F12)
aws sns list-subscriptions-by-topic --topic-arn "$(pid NotificationsTopicE4AF40A8)" --query "Subscriptions[].[Protocol,Endpoint]" --output table --region "$REGION"
# AWS::SNS::Topic (NotificationsTopicE4AF40A8)
aws sns get-topic-attributes --topic-arn "arn:aws:sns:${REGION}:${ACCOUNT}:${PRODUCT}-${ENV}-cell-02-sns-notifications" --query "Attributes.TopicArn" --output table --region "$REGION"
# AWS::SQS::Queue (OrdersDeadLetterQueue91101596)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-02-sqs-orders-dlq" --query "QueueUrl" --output table --region "$REGION"
# AWS::SQS::Queue (OrdersQueue3DFA1D51)
aws sqs get-queue-url --queue-name "${PRODUCT}-${ENV}-cell-02-sqs-orders" --query "QueueUrl" --output table --region "$REGION"
# AWS::EC2::VPC (Vpc8378EB38)
aws ec2 describe-vpcs --vpc-ids "$(pid Vpc8378EB38)" --query "Vpcs[].[VpcId,CidrBlock,State]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet1Subnet2BB74ED7)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet1Subnet2BB74ED7)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet1RouteTable15C15F8E)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet1RouteTable15C15F8E)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcpublicSubnet2SubnetE34B022A)
aws ec2 describe-subnets --subnet-ids "$(pid VpcpublicSubnet2SubnetE34B022A)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcpublicSubnet2RouteTableC5A6DF77)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcpublicSubnet2RouteTableC5A6DF77)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcprivateSubnet1SubnetCEAD3716)
aws ec2 describe-subnets --subnet-ids "$(pid VpcprivateSubnet1SubnetCEAD3716)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcprivateSubnet1RouteTable1979EACB)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcprivateSubnet1RouteTable1979EACB)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::Subnet (VpcprivateSubnet2Subnet2DE7549C)
aws ec2 describe-subnets --subnet-ids "$(pid VpcprivateSubnet2Subnet2DE7549C)" --query "Subnets[].[SubnetId,CidrBlock,AvailabilityZone]" --output table --region "$REGION"
# AWS::EC2::RouteTable (VpcprivateSubnet2RouteTable4D0FFC8C)
aws ec2 describe-route-tables --route-table-ids "$(pid VpcprivateSubnet2RouteTable4D0FFC8C)" --query "RouteTables[].[RouteTableId,length(Routes),length(Associations)]" --output table --region "$REGION"
# AWS::EC2::InternetGateway (VpcIGWD7BA715C)
aws ec2 describe-internet-gateways --internet-gateway-ids "$(pid VpcIGWD7BA715C)" --query "InternetGateways[].[InternetGatewayId,Attachments[0].VpcId]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AppSecurityGroupC396D536)
aws ec2 describe-security-groups --group-ids "$(pid AppSecurityGroupC396D536)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (InstanceSecurityGroup896E10BF)
aws ec2 describe-security-groups --group-ids "$(pid InstanceSecurityGroup896E10BF)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::IAM::Role (InstanceRole3CCE2F1D)
aws iam get-role --role-name "${PRODUCT}-${ENV}-cell-02-role-ec2-instance" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::IAM::InstanceProfile (AppInstanceInstanceProfileC6B6EFAA)
aws iam get-instance-profile --instance-profile-name "$(pid AppInstanceInstanceProfileC6B6EFAA)" --query "InstanceProfile.[InstanceProfileName,Arn]" --output table --region "$REGION"
# AWS::EC2::Instance (AppInstance13C82D50)
aws ec2 describe-instances --instance-ids "$(pid AppInstance13C82D50)" --query "Reservations[].Instances[].[InstanceId,InstanceType,State.Name]" --output table --region "$REGION"
# AWS::ECS::Cluster (ClusterEB0386A7)
aws ecs describe-clusters --clusters "${PRODUCT}-${ENV}-cell-02-ecs-cluster" --query "clusters[].[clusterName,status]" --output table --region "$REGION"
# AWS::IAM::Role (AppTaskDefinitionTaskRole96BC2009)
aws iam get-role --role-name "$(pid AppTaskDefinitionTaskRole96BC2009)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::ECS::TaskDefinition (AppTaskDefinitionCBC902A9)
aws ecs describe-task-definition --task-definition "${PRODUCT}-${ENV}-cell-02-ecs-app-task" --query "taskDefinition.[family,revision,status]" --output table --region "$REGION"
# AWS::IAM::Role (AppTaskDefinitionExecutionRoleE1F9B422)
aws iam get-role --role-name "$(pid AppTaskDefinitionExecutionRoleE1F9B422)" --query "Role.[RoleName,Arn]" --output table --region "$REGION"
# AWS::ECS::Service (AppServiceA2F9036C)
aws ecs describe-services --cluster "${PRODUCT}-${ENV}-cell-02-ecs-cluster" --services "${PRODUCT}-${ENV}-cell-02-ecs-app-service" --query "services[].[serviceName,status,desiredCount]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AppServiceSecurityGroupCD648D82)
aws ec2 describe-security-groups --group-ids "$(pid AppServiceSecurityGroupCD648D82)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::ApplicationAutoScaling::ScalableTarget (AppServiceTaskCountTarget8D11C093)
aws application-autoscaling describe-scalable-targets --service-namespace ecs --query "ScalableTargets[?contains(ResourceId, '${PRODUCT}-${ENV}-cell-02-ecs-cluster')].[ResourceId,MinCapacity,MaxCapacity]" --output table --region "$REGION"
# AWS::ApplicationAutoScaling::ScalingPolicy (AppServiceTaskCountTargetCpuScaling8D6A969B)
aws application-autoscaling describe-scaling-policies --service-namespace ecs --query "ScalingPolicies[?contains(ResourceId, '${PRODUCT}-${ENV}-cell-02-ecs-cluster')].[PolicyName,PolicyType]" --output table --region "$REGION"
# AWS::Lambda::Function (HelloFunctionD909AE8C)
aws lambda get-function --function-name "${PRODUCT}-${ENV}-cell-02-lambda-hello" --query "Configuration.[FunctionName,Runtime,State]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::LoadBalancer (Alb16C2F182)
aws elbv2 describe-load-balancers --load-balancer-arns "$(pid Alb16C2F182)" --query "LoadBalancers[].[LoadBalancerName,Type,State.Code]" --output table --region "$REGION"
# AWS::EC2::SecurityGroup (AlbSecurityGroup580F65A6)
aws ec2 describe-security-groups --group-ids "$(pid AlbSecurityGroup580F65A6)" --query "SecurityGroups[].[GroupId,GroupName,VpcId]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::TargetGroup (AlbTargetGroup40F9FCBA)
aws elbv2 describe-target-groups --target-group-arns "$(pid AlbTargetGroup40F9FCBA)" --query "TargetGroups[].[TargetGroupName,Port,TargetType]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::Listener (AlbListenerDFCDF14C)
aws elbv2 describe-listeners --listener-arns "$(pid AlbListenerDFCDF14C)" --query "Listeners[].[Port,Protocol]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::LoadBalancer (NlbBCDB97FE)
aws elbv2 describe-load-balancers --load-balancer-arns "$(pid NlbBCDB97FE)" --query "LoadBalancers[].[LoadBalancerName,Type,State.Code]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::TargetGroup (NlbTargetGroupB5099BEB)
aws elbv2 describe-target-groups --target-group-arns "$(pid NlbTargetGroupB5099BEB)" --query "TargetGroups[].[TargetGroupName,Port,TargetType]" --output table --region "$REGION"
# AWS::ElasticLoadBalancingV2::Listener (NlbListenerA43610D3)
aws elbv2 describe-listeners --listener-arns "$(pid NlbListenerA43610D3)" --query "Listeners[].[Port,Protocol]" --output table --region "$REGION"
# Also created - listed in the table above:
#   AWS::S3::BucketPolicy AppDataBucketPolicyE31553DB - shown by its bucket
#   Custom::S3AutoDeleteObjects AppDataBucketAutoDeleteObjectsCustomResourceD2BD59B3 - shown by the provider Lambda function and role listed here
#   AWS::SQS::QueuePolicy NotificationsQueuePolicy71DD684A - shown by its queue
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet1RouteTableAssociation4E83B6E4 - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet1DefaultRouteB88F9E93 - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcpublicSubnet2RouteTableAssociationCCE257FF - shown by its route table
#   AWS::EC2::Route VpcpublicSubnet2DefaultRoute732F0BEB - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcprivateSubnet1RouteTableAssociationEEBD93CE - shown by its route table
#   AWS::EC2::SubnetRouteTableAssociation VpcprivateSubnet2RouteTableAssociationB691E645 - shown by its route table
#   AWS::EC2::VPCGatewayAttachment VpcVPCGWBF912B6E - shown by its internet gateway
#   AWS::IAM::Policy AppTaskDefinitionExecutionRoleDefaultPolicyA9233178 - shown by its IAM role
#   AWS::EC2::SecurityGroupIngress AppServiceSecurityGroupfromEnterprisePrdCell02StackAlbSecurityGroupBA599BF980C5CBC0FC - shown by its security group
#   AWS::EC2::SecurityGroupEgress AlbSecurityGrouptoEnterprisePrdCell02StackAppServiceSecurityGroup704DFF0B801EAF2538 - shown by its security group
```

**On floci** (2.1.0), CloudFormation records `AWS::ApplicationAutoScaling::ScalableTarget`, `AWS::ApplicationAutoScaling::ScalingPolicy` without creating it, so those commands find nothing there - they work on real AWS. See [`REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations).
<!-- END resource-commands -->

## 10. Tests

This example's tests live outside the repository's own `tests/` directory
(the root `pyproject.toml`'s `testpaths = ["tests"]` means the repository's
own `uv run pytest` never runs them, and never has to know this example
exists) - run them explicitly:

```bash
uv run pytest examples/enterprise_stack/tests/ -v
```

`make coverage` runs these together with the repository's own tests and
reports coverage for both (this example is at 100%) - see
[`../../docs/TESTING.md`, "Test coverage"](../../docs/TESTING.md#test-coverage).
Keep it that way: every new builder or code path gets a test in the same
change.

`test_registry.py` tests the precedence/validation engine with fake
builders - no CDK, no AWS, no Docker, runs in milliseconds, the same
"fast and dependency-free" philosophy as
[`../../docs/TESTING.md`](../../docs/TESTING.md). `test_stack_synth.py`
and `test_ecs_ecr_load_balancing.py` build real `EnterpriseCellStack`s
with `aws_cdk.assertions`, the same way every
`tests/unit/test_NN_service.py` in this repository does -
`test_ecs_ecr_load_balancing.py` specifically covers: `ecs`/`alb`/`nlb`
correctly refusing to build without their new dependencies, the ECS task's
container image resolving from the `ecr` repository (never a public
registry string), the autoscaling `ScalableTarget`/`ScalingPolicy`
matching `EcsResourceBuilder`'s `MIN_TASK_COUNT`/`MAX_TASK_COUNT`/
`TARGET_CPU_UTILIZATION_PERCENT` constants, and the ECS service's own
`LoadBalancers` property listing both the ALB's and the NLB's target
groups when both are enabled (or just one, when only one is).
`test_builders.py` enables each remaining builder (`kms`, `dynamodb`,
`sns`, `acm`, `ec2`) on its own and checks its key resource and its
product-environment-cell name; `test_environment_config.py` checks that
`environments/{dev,stg,prd}.json` load into the documented cells, plus the
account/region fallback; and `test_app.py` checks `app.py` itself - one
stack per cell, the selected `ENTERPRISE_ENVIRONMENT` driving names and
tags, and a long name like `staging` being rejected.

## 11. Extending it: adding resource #15

1. Look up the exact CDK construct(s) you need in the
   [AWS CDK API Reference (Python)](https://docs.aws.amazon.com/cdk/api/v2/python/)
   - see [`../../CLAUDE.md`, section 4](../../CLAUDE.md#4-do-not-invent-things-the-core-guardrail).
   Ideally, base it on one of this repository's own `modules/NN_service/stack.py`
   files if a matching module already exists.
2. Create `builders/whatever_builder.py`, following the shape of any
   existing file in that directory: a `key`, an optional `depends_on`, and
   a `build(self, scope, context)` method that calls `resource_name()` and
   `apply_name_tag()` the same way every other builder does.
3. Import your class and add one `registry.register(YourBuilder())` line
   in `builders/__init__.py`. **Nothing else changes** - not
   `stack.py`, not `core/resource_registry.py`, not any other builder
   (unless another builder should now depend on yours).
4. Add its key to `enabled_resources` in whichever `environments/*.json`
   file(s) should include it.
5. Write a synth-level test (`tests/test_stack_synth.py` is the pattern)
   confirming it only appears when enabled, and confirm `uv run cdk synth`
   still succeeds.

## 12. Known limitations and honest scope

- **This is an example, not a 45th learning module** - it has no
  `README.md` matching the module-contract section structure on purpose
  (see [`../../CLAUDE.md`, section 3](../../CLAUDE.md#3-the-module-contract):
  that contract is specifically for `modules/NN_service/`), is not
  auto-discovered by the root `app.py`, and is not one of the 46 numbered
  modules or phases in
  [`../../docs/LEARNING-PATH.md`](../../docs/LEARNING-PATH.md) - that
  page's own closing "Beyond the 46 modules" section links here as an
  optional next step, not as a module.
- **`prd.json`'s explicit accounts are placeholders** (`111111111111`),
  not real AWS accounts - substitute your own before ever attempting a
  real deploy. On floci, the placeholder works as-is (see
  [section 9](#9-running-it)). The `ec2` builder uses
  `ec2.MachineImage.resolve_ssm_parameter_at_launch()`, so the AMI is
  resolved by EC2 at launch rather than by an SSM lookup or an SSM-typed
  template parameter - which keeps `prd` synthesizable without
  credentials, and keeps a re-deploy of an unchanged cell a no-op (see
  `modules/13_ec2/stack.py` for the details).
- **The `iam` builder's S3 policy is ARN-by-convention, not a live
  reference** (same as `modules/01_iam/stack.py`) - it works whether or
  not `s3` is actually enabled for the cell, but a fuller implementation
  could instead inject the live `s3.IBucket` construct when `s3` is
  enabled; see the comment in `builders/iam_builder.py` and
  [`../../docs/IMPORTING-EXISTING-RESOURCES.md`](../../docs/IMPORTING-EXISTING-RESOURCES.md)
  for the "reference an existing resource" pattern this would use.
- **`ecr`'s repository starts empty** - `cdk deploy` creates the
  repository, but nothing in this example (or in CDK/CloudFormation
  generally) copies the `aeciopires/mytoolkit` image into it; that's a
  manual `docker pull`/`tag`/`push`, documented in
  [section 8.1](#81---the-ecr-resource-copying-an-image-in). Deploying
  `ecs` before doing that push will succeed at the CloudFormation level
  and then fail to actually start any task (an `ecs.amazonaws.com`
  "CannotPullContainerError" in the service's events) - the same failure
  mode a real, empty ECR repository produces, not a bug specific to this
  example.
- **`alb`/`nlb` register the ECS service, not any particular task's IP** -
  `target_group.add_target(service)` is the entire integration; AWS
  itself keeps each target group's registered IPs in sync as
  Application Auto Scaling adds or removes tasks (see
  [section 8.2](#82---scaling-1-to-3-tasks-driven-by-cpu)). Neither
  builder opens security-group ingress from the load balancer to the
  service beyond what `modules/30_alb`/`modules/31_nlb`'s own verified
  code already does - confirm connectivity end to end before trusting
  this beyond learning purposes, same as the next point.
- **No fluent `.with_x()` builder methods** - see
  [section 4.1](#41---the-builder-pattern) for why, and as a natural next
  step.
- **No automated deploy/destroy round-trip has been run against floci or
  real AWS for this example** (only `cdk synth`/`cdk list` and the unit
  tests above) - do that yourself before trusting it beyond learning
  purposes, the same caution [`../../REQUIREMENTS.md`, section 10](../../REQUIREMENTS.md#10-observations-and-limitations)
  gives for every module.

## 13. Alternative: one git repository (and one release cadence) per builder

Everything above assumes what this example actually does: all 14
builders live in **one repository**, as plain local files imported with
`from .vpc_builder import VpcResourceBuilder` (a "monorepo" layout). That
is the right default for a learning path and for most small-to-medium
teams. This section documents - in comments in the code, and in more
detail here - a real, commonly-used **alternative**: publishing each
builder (or a related group of them) from its **own git repository**, as
its **own independently-versioned package**, using
[Semantic Versioning](https://semver.org/) ("SemVer") to communicate what
changed between releases. Nothing in this example is restructured this
way - the point is to explain the option and exactly where the seam
already is for anyone who needs it, not to add speculative code nobody
asked for.

### 13.1 - Why you'd want this

The moment a "combined app" like this one is owned by more than one
team - a networking team owning `vpc`/`alb`/`nlb`, a platform team owning
`iam`/`kms`/`ecr`, an application team owning `ecs`/`lambda` - a single
shared repository means every team's changes go through the same pull
request queue, the same CI run, and the same release, whether or not
their changes touch the same files. Splitting each builder (or each
team's group of builders) into its own repository gives each team:

- **An independent release cadence** - the networking team can ship a
  `vpc-builder` v2.1.0 the same day the platform team is mid-way through
  a breaking `kms-builder` v3.0.0 migration, with neither blocking the
  other or needing to coordinate a shared repository's release.
- **A clear ownership and review boundary** - who can approve a change to
  `alb-builder` is a repository-level permission, not a path-based rule
  inside one large repository.
- **An explicit, versioned contract** between "the team that builds a
  resource" and "the team that assembles cells from them" - the
  `enterprise_stack` app declares *which version* of each builder it
  depends on, the same way `pyproject.toml` already declares
  `aws-cdk-lib==2.271.0` rather than "whatever the latest CDK happens to
  be today."

The trade-off is real, not one-sided: more repositories to keep track of,
a version-bump-and-release step before a fix in one builder reaches the
app that uses it, and the possibility of two builders' declared versions
quietly drifting out of sync with each other. This is why it's presented
here as an *alternative* worth knowing about, not a better default -
[`CLAUDE.md`](../../CLAUDE.md) itself is a single, deliberately
monorepo-friendly learning path for exactly the same reason a small team
usually starts with one repository, not fourteen.

### 13.2 - Where the seam already is

This alternative is a natural fit for this codebase specifically because
`build_default_registry()` (`builders/__init__.py`) already depends only
on the `ResourceBuilder` abstraction (see
[section 2.5](#25---d-dependency-inversion-principle)) - it has no idea,
and does not need to know, whether `VpcResourceBuilder` was imported from
a local file or from an installed package. Moving a builder to its own
repository is mechanically just changing one `import` line - see the
comment above the `import` block in `builders/__init__.py`.

### 13.3 - Semantic Versioning for a builder package

[Semantic Versioning 2.0.0](https://semver.org/) numbers a release
`MAJOR.MINOR.PATCH` and defines exactly what must change each number for a
package other code depends on:

- **MAJOR** (`1.x.x` → `2.0.0`) - a change that breaks existing callers:
  removing/renaming the builder's `key`, changing what `depends_on`
  requires, changing `build()`'s signature, or changing what it publishes
  on `context.shared` in a way that breaks whatever already reads it.
- **MINOR** (`1.2.x` → `1.3.0`) - backward-compatible additions: a new
  optional property on the resource it creates, a new entry published to
  `context.shared` that nothing was already relying on.
- **PATCH** (`1.2.3` → `1.2.4`) - a backward-compatible bug fix: correcting
  a property value, a naming bug, a missing tag - nothing that changes
  what other code can rely on.

A team consuming `vpc-builder` pins a version range the same way this
repository already pins `aws-cdk-lib==2.271.0` in `pyproject.toml` (see
[`../../CLAUDE.md`, section 4, point 5](../../CLAUDE.md#4-do-not-invent-things-the-core-guardrail)
on why an exact, known version beats "whatever is newest") - upgrading is
then a deliberate, reviewed decision (read the new version's changelog,
bump the pin, run the tests), not something that happens silently.

### 13.4 - Declaring a builder as a versioned dependency

[uv](https://docs.astral.sh/uv/) - already this repository's package
manager - supports exactly this: a package can be declared as a normal
dependency and then pointed at a git repository, pinned to a tag, in
`[tool.uv.sources]` (verified against the current
[uv documentation on Git dependencies](https://docs.astral.sh/uv/concepts/projects/dependencies/)):

```toml
# pyproject.toml, if vpc_builder/kms_builder/ecr_builder were extracted
# into their own repositories, one release per team, each tagged with a
# SemVer version:

[project]
dependencies = [
    "acme-cdk-vpc-builder",
    "acme-cdk-kms-builder",
    "acme-cdk-ecr-builder",
]

[tool.uv.sources]
acme-cdk-vpc-builder = { git = "https://github.com/acme-platform/cdk-vpc-builder", tag = "v2.1.0" }
acme-cdk-kms-builder = { git = "https://github.com/acme-platform/cdk-kms-builder", tag = "v3.0.0" }
acme-cdk-ecr-builder = { git = "https://github.com/acme-platform/cdk-ecr-builder", tag = "v1.4.2" }
```

`uv.lock` then records the exact commit each tag resolved to at the time
of `uv sync`, so a later force-push or tag move upstream can't silently
change what gets installed - the same reproducibility guarantee
`uv.lock` already gives this repository's own dependencies. `tag=` can be
swapped for `branch=` (tracks a moving branch - rarely what you want for
a versioned dependency) or `rev=` (pins an exact commit, no tag needed) -
see the uv documentation linked above for the full syntax.

### 13.5 - Or a private package index, instead of git URLs directly

For builders that are internal/proprietary rather than open source, a
private Python package index is usually a better fit than pointing
`pyproject.toml` at git repository URLs directly - each builder is
published as an ordinary versioned wheel (`twine upload`, or a CI job
doing the equivalent), and installed as an ordinary dependency, with no
git-specific syntax at all. [AWS CodeArtifact](https://docs.aws.amazon.com/codeartifact/latest/ug/welcome.html)
is AWS's own managed option for this; configuring `pip` (or `uv`, which
reads the same `pip.conf`/index-url configuration) to use it is one
command, using AWS's own credentials rather than a separate token:

```bash
aws codeartifact login --tool pip --domain my-domain --domain-owner 111122223333 --repository my-cdk-builders
# then, as an ordinary version-pinned dependency:
uv add acme-cdk-vpc-builder==2.1.0
```

(verified against the
[AWS CodeArtifact - Configure and use pip](https://docs.aws.amazon.com/codeartifact/latest/ug/python-configure-pip.html)
guide - the `login` command's authorization token expires after 12 hours
by default and needs periodic refreshing, noted there in full.)

## References

- [SOLID (Wikipedia)](https://en.wikipedia.org/wiki/SOLID) - the five
  principles, their origin, and Robert C. Martin's original papers.
- [Design Patterns: Elements of Reusable Object-Oriented Software](https://en.wikipedia.org/wiki/Design_Patterns)
  (the "Gang of Four" book) - the Builder pattern's original source.
- [Topological sorting (Wikipedia)](https://en.wikipedia.org/wiki/Topological_sorting) -
  Kahn's algorithm, used in `core/resource_registry.py`.
- [AWS Well-Architected Framework - Cell-based architecture](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/cell-based-architecture.html)
- [AWS CDK Constructs](https://docs.aws.amazon.com/cdk/v2/guide/constructs.html) ·
  [AWS CDK - Environments](https://docs.aws.amazon.com/cdk/v2/guide/environments.html) ·
  [AWS CDK API Reference (Python)](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [Semantic Versioning 2.0.0](https://semver.org/) - the MAJOR.MINOR.PATCH
  spec referenced in [section 13.3](#133---semantic-versioning-for-a-builder-package).
- [uv - Git dependencies (`[tool.uv.sources]`)](https://docs.astral.sh/uv/concepts/projects/dependencies/) -
  the `git`/`tag`/`branch`/`rev` syntax used in
  [section 13.4](#134---declaring-a-builder-as-a-versioned-dependency).
- [AWS CodeArtifact - Configure and use pip](https://docs.aws.amazon.com/codeartifact/latest/ug/python-configure-pip.html) -
  the private-index alternative in
  [section 13.5](#135---or-a-private-package-index-instead-of-git-urls-directly).
- This repository's own conventions: [`../../CLAUDE.md`](../../CLAUDE.md) ·
  [`../../REQUIREMENTS.md`](../../REQUIREMENTS.md) ·
  [`../../docs/TESTING.md`](../../docs/TESTING.md)
