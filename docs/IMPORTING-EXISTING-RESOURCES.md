<!-- TOC -->

- [Importing existing resources into CDK](#importing-existing-resources-into-cdk)
  - [Why this matters](#why-this-matters)
  - [Two completely different things people mean by "import"](#two-completely-different-things-people-mean-by-import)
  - [1. Referencing an existing resource, without managing it](#1-referencing-an-existing-resource-without-managing-it)
    - [1.1 - By ARN, name, or other attribute (`from_*`)](#11---by-arn-name-or-other-attribute-from_)
    - [1.2 - By live account lookup (`Vpc.from_lookup()`)](#12---by-live-account-lookup-vpcfrom_lookup)
    - [1.3 - What you can and can't do with a reference](#13---what-you-can-and-cant-do-with-a-reference)
  - [2. `cdk import`: bringing a resource under full CDK management](#2-cdk-import-bringing-a-resource-under-full-cdk-management)
    - [2.1 - Preconditions](#21---preconditions)
    - [2.2 - The exact workflow](#22---the-exact-workflow)
    - [2.3 - Limitations](#23---limitations)
  - [3. `cdk migrate`: generating a whole new CDK app from what already exists](#3-cdk-migrate-generating-a-whole-new-cdk-app-from-what-already-exists)
    - [3.1 - The three migration sources](#31---the-three-migration-sources)
    - [3.2 - `cdk import` vs. `cdk migrate`](#32---cdk-import-vs-cdk-migrate)
    - [3.3 - Considerations for stateful resources](#33---considerations-for-stateful-resources)
  - [4. Which one do I actually want?](#4-which-one-do-i-actually-want)
  - [5. Common scenarios in this learning path](#5-common-scenarios-in-this-learning-path)
  - [6. Trying this against floci](#6-trying-this-against-floci)
  - [References](#references)

<!-- TOC -->

# Importing existing resources into CDK

This page explains, from zero, the ways an AWS CDK app can work with an
AWS resource that **already exists** - created by hand in the console,
by a colleague's script, by Terraform, by a different CDK app, or by a
legacy CloudFormation stack nobody wants to touch directly anymore. None
of the 46 modules in this learning path need this - every module creates
its own resources from scratch - but it's one of the first real questions
a team asks once they start applying CDK to an existing AWS account rather
than a brand-new one, so it's documented here on its own.

## Why this matters

A brand-new CDK app has the luxury of creating everything itself. A real
AWS account almost never does - it already has resources, created before
anyone decided to adopt CDK, or created manually for a one-off reason. CDK
gives you two genuinely different tools for this, and picking the wrong
one for the job either fails outright or (worse) quietly does the wrong
thing. This page's whole purpose is making sure you reach for the right
one.

## Two completely different things people mean by "import"

1. **"I want my CDK code to *use* something that already exists"** -
   for example, an S3 bucket someone else's stack owns, that your Lambda
   function just needs read access to. You never want CDK to create,
   change, or delete that bucket. See [section 1](#1-referencing-an-existing-resource-without-managing-it).
2. **"I want CDK to fully *own and manage* a resource that already
   exists"** - for example, a database created by hand three years ago
   that a team now wants under the same `cdk deploy` lifecycle as
   everything else, including the ability to change its properties or
   eventually delete it through CDK. See
   [section 2](#2-cdk-import-bringing-a-resource-under-full-cdk-management)
   and [section 3](#3-cdk-migrate-generating-a-whole-new-cdk-app-from-what-already-exists).

Mixing these up is the single most common mistake: using a `from_*`
reference (tool #1) and then being confused that changing its properties
in code does nothing at deploy time - by design, it's read-only. Or
reaching for `cdk import` (tool #2) for a resource you only ever wanted to
*read from*, adding needless risk (a mistake here can modify or delete a
real resource) for no benefit.

## 1. Referencing an existing resource, without managing it

### 1.1 - By ARN, name, or other attribute (`from_*`)

Every L2 construct that represents an AWS resource has one or more static
`from_*` methods that build a lightweight **proxy object** for a resource
that already exists, from just enough identifying information (usually an
ARN, sometimes a name or ID):

```python
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_ec2 as ec2

# By name (must be in the same AWS account)
existing_bucket = s3.Bucket.from_bucket_name(self, "ExistingBucket", "amzn-s3-demo-bucket1")

# By full ARN (can be in a different account)
existing_bucket = s3.Bucket.from_bucket_arn(self, "ExistingBucket", "arn:aws:s3:::amzn-s3-demo-bucket1")

# By one or more attributes
existing_vpc = ec2.Vpc.from_vpc_attributes(self, "ExistingVpc", vpc_id="vpc-1234567890abcdef")
```

You can then pass `existing_bucket` or `existing_vpc` anywhere your own
code expects that construct's interface type (`s3.IBucket`, `ec2.IVpc`) -
for example, granting a Lambda function read access to `existing_bucket`,
or placing a new resource inside `existing_vpc`.

### 1.2 - By live account lookup (`Vpc.from_lookup()`)

`ec2.Vpc` is complex enough that CDK also offers `Vpc.from_lookup()`
(Python: `from_lookup`), which queries your AWS account **at synthesis
time** to find the matching VPC, instead of requiring you to already know
its ID:

```python
default_vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)
public_vpc = ec2.Vpc.from_lookup(self, "PublicVpc", tags={"aws-cdk:subnet-type": "Public"})
```

This needs real AWS credentials for the target account at `cdk synth`
time (the CDK CLI does the lookup, not just at deploy time), and only
works for a stack with an **explicit** `env=` (account and region) - an
environment-agnostic stack has no account to query. See
[AWS CDK - Environments](https://docs.aws.amazon.com/cdk/v2/guide/environments.html)
and [`REQUIREMENTS.md`, section 9](../REQUIREMENTS.md#9-flexible-account-and-region)
for why every module in this learning path is environment-agnostic by
default, and therefore never uses `from_lookup()`. Results are cached in
`cdk.context.json` (already gitignored in this repository - see
`.gitignore`) so the same VPC keeps being selected on later runs even if
you don't have account access at that moment; commit that file yourself
in a project that relies on `from_lookup()`.

### 1.3 - What you can and can't do with a reference

However you build one, a `from_*` proxy **never becomes part of your CDK
app's managed resources**. You can pass it anywhere a resource of that
type is expected, but you cannot modify the real thing through it -
calling a mutating method (for example `add_to_resource_policy` on an
external `s3.Bucket`) silently does nothing. If you need to actually
change or eventually delete the resource through CDK, you need
[section 2](#2-cdk-import-bringing-a-resource-under-full-cdk-management)
instead.

## 2. `cdk import`: bringing a resource under full CDK management

`cdk import` uses
[AWS CloudFormation resource imports](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import.html)
to bring one or more already-existing resources under the management of a
CDK stack's CloudFormation stack - useful when migrating to CDK, moving a
resource between stacks, or changing its logical ID. Not every
CloudFormation resource type supports this - see the
[current list of resource types that support import](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-supported-resources.html)
before planning around it, since it changes over time.

### 2.1 - Preconditions

- The resource must not currently be managed by **any other**
  CloudFormation stack. If it is, first set that stack's removal policy
  for it to `RemovalPolicy.RETAIN` and deploy, then remove it from that
  stack and deploy again - this detaches it from CloudFormation without
  deleting the real resource.
- `cdk diff` against the target stack must show **no pending changes**
  other than the new resource(s) you're about to import - an import
  operation only tolerates additions.
- Your CDK code must **exactly model the resource's current state** -
  every property CloudFormation cares about (encryption settings,
  lifecycle rules, everything), not just the ones you happen to remember.
  Getting this wrong doesn't fail the import; it makes the *next* `cdk
  deploy` try to "correct" properties you never meant to change.

### 2.2 - The exact workflow

1. Add a construct for the resource you want to import to your stack -
   for example `s3.Bucket(self, "ImportedBucket", ...)` - modeling every
   property the real bucket already has. You can choose whether to
   include the physical resource name in the definition; leaving it out
   is usually recommended so the resource can be deployed multiple times
   more easily in the future, but during an import CDK will prompt you for
   the actual physical name if it isn't in your code.
2. Run `cdk import <STACKNAME>`.
3. If your code didn't specify the resource's physical name, the CLI
   prompts you for it.
4. Once `cdk import` reports success, the resource is managed by both
   AWS CloudFormation and your CDK app - the next `cdk deploy` will apply
   any subsequent changes you make to its construct's properties.
5. Run a
   [CloudFormation drift detection](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-drift.html)
   operation to confirm your construct's definition actually matches the
   resource's real, current state.

### 2.3 - Limitations

`cdk import` does not support importing into nested stacks.

## 3. `cdk migrate`: generating a whole new CDK app from what already exists

> `cdk migrate` was in preview at the time the official AWS CDK Developer
> Guide page consulted for this section was written - re-check
> [the current guide](https://docs.aws.amazon.com/cdk/v2/guide/migrate.html)
> before relying on details here, since a preview feature can change.

Where `cdk import` adds one or more resources to a stack you already have,
`cdk migrate` creates an **entirely new CDK app** (via `cdk init` under
the hood) from a source you point it at, using `cdk import` internally to
bring the resources in:

```bash
# From deployed resources not yet in any CloudFormation stack (uses the
# CloudFormation IaC generator service to scan an account/region)
cdk migrate --from-scan --stack-name "myStack"

# From an already-deployed CloudFormation stack
cdk migrate --from-stack --stack-name "myCloudFormationStack"

# From a local CloudFormation template (JSON or YAML)
cdk migrate --from-path "./template.json" --stack-name "myStack"
```

### 3.1 - The three migration sources

- **`--from-scan`** - scans an AWS account/region for resources not
  already in a CloudFormation stack, using the CloudFormation "IaC
  generator" service, and migrates what it finds (up to that service's
  quota; you can narrow the scan with `--filter`).
- **`--from-stack`** - retrieves an already-deployed stack's template and
  migrates it, matching logical IDs so a later `cdk deploy` updates the
  existing stack rather than creating a new one.
- **`--from-path`** - migrates a local template file you already have
  (does not support nested templates, or AWS SAM templates directly - a
  SAM template must first be converted to CloudFormation or deployed and
  migrated as a deployed stack).

### 3.2 - `cdk import` vs. `cdk migrate`

Use `cdk import` to bring **one or more specific resources** into a
**new or existing** CDK app, defining each one as an L1 construct
yourself. Use `cdk migrate` when starting a **brand-new** CDK app from an
existing account scan, stack, or template - it generates the L1 constructs
for you (and only L1 constructs; add higher-level L2s afterward yourself)
and always produces a single-stack app.

### 3.3 - Considerations for stateful resources

For anything stateful - a database, an S3 bucket, anything you cannot
just recreate - verify the resource type
[supports CloudFormation import](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-supported-resources.html)
first, then make sure the migrated resource's logical ID (and, if
migrating a deployed stack, the stack name) matches the original exactly,
and deploy to the *same* AWS account and region the resource already
lives in. Some resource properties are write-only (for example, a
database's master password) and cannot be read back from the account by
the scan - `cdk migrate` flags these in the generated project's own
`ReadMe` under a "Warnings" section, and you must fill in the real values
yourself before the app is deployable.

## 4. Which one do I actually want?

| Situation | Use |
|---|---|
| Grant your code access to a resource another team/stack owns, and you'll never manage it | `from_*` (e.g. `Bucket.from_bucket_arn`) |
| Your code needs to select a complex existing resource (like a VPC) it doesn't own, by tag or default-ness | `Vpc.from_lookup()` |
| A specific, already-known resource should come under your existing CDK stack's management | `cdk import` |
| You have no CDK app yet, and want one generated from an account scan, a deployed stack, or a template | `cdk migrate` |

## 5. Common scenarios in this learning path

- **"I clicked around the AWS Console/floci UI and created something by
  hand - can I bring it under this repository's CDK management?"** - yes,
  with `cdk import`: add a construct matching what you created (see
  [`CLAUDE.md`, section 4](../CLAUDE.md#4-do-not-invent-things-the-core-guardrail)
  for looking up its exact properties first) to the relevant module's
  `stack.py`, then run `cdk import <StackId>` against the same endpoint
  (floci or real AWS) the resource actually lives in.
- **"A teammate's stack already made an S3 bucket I just want to read
  from in my own module while learning"** - use `s3.Bucket.from_bucket_arn()`
  or `from_bucket_name()`, not a second `s3.Bucket(...)` creation - creating
  a second bucket construct pointed at the same name will conflict at
  deploy time.
- **"I have an old, hand-written CloudFormation template for something
  and want to bring it into this style of repository"** - `cdk migrate
  --from-path` gets you a starting CDK app; from there, follow this
  repository's own module contract ([`CLAUDE.md`, section 3](../CLAUDE.md#3-the-module-contract))
  to reshape it to match, replacing the generated L1 constructs with L2s
  where one exists (see [`CLAUDE.md`, section 4, point 2](../CLAUDE.md#4-do-not-invent-things-the-core-guardrail)).

## 6. Trying this against floci

Every command on this page works against floci exactly the way it works
against real AWS - point your terminal at it first (see
[`REQUIREMENTS.md`, section 5](../REQUIREMENTS.md#5-running-floci-the-local-aws-emulator)),
then run `cdk import`/`cdk migrate` the same way, at zero cost and with no
risk to a real account. This is a safe way to practice the whole workflow
(create something "by hand" with the AWS CLI against floci, then `cdk
import` it) before ever trying it against a real account.

## References

- [AWS CDK v2 Developer Guide - Resources and the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/resources.html) (the `from_*` / `fromLookup` reference pattern, section "Referencing resources in your AWS account")
- [AWS CDK v2 Developer Guide - AWS CDK CLI reference](https://docs.aws.amazon.com/cdk/v2/guide/cli.html) (the `cdk import` section, "Import existing resources into a stack")
- [AWS CDK v2 Developer Guide - Migrate existing resources and AWS CloudFormation templates to the AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/migrate.html) (`cdk migrate`, preview at time of writing - re-check before relying on details)
- [AWS CloudFormation User Guide - Resource import](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import.html)
- [AWS CloudFormation User Guide - Resource type support for import operations](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resource-import-supported-resources.html)
- [AWS CloudFormation User Guide - Generating templates for existing resources (IaC generator)](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/generate-IaC.html)
- [AWS CloudFormation User Guide - Detecting unmanaged configuration changes (drift detection)](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-stack-drift.html)
