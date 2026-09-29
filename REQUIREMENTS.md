<!-- TOC -->

- [Requirements](#requirements)
  - [0. Zero to your first deploy, in order](#0-zero-to-your-first-deploy-in-order)
  - [1. Supported operating systems](#1-supported-operating-systems)
  - [2. Recommended hardware](#2-recommended-hardware)
  - [3. Required software](#3-required-software)
    - [3.1 - Install on Ubuntu (amd64)](#31---install-on-ubuntu-amd64)
    - [3.2 - Install on macOS (arm64 and amd64)](#32---install-on-macos-arm64-and-amd64)
    - [3.3 - Managing the Python version with mise](#33---managing-the-python-version-with-mise)
    - [3.4 - Running and reading `make check`](#34---running-and-reading-make-check)
  - [4. Project setup (uv)](#4-project-setup-uv)
  - [5. Running floci (the local AWS emulator)](#5-running-floci-the-local-aws-emulator)
    - [5.1 - Option A: docker compose (this repository's `docker-compose.yml`)](#51---option-a-docker-compose-this-repositorys-docker-composeyml)
    - [5.2 - Option B: floci-cli](#52---option-b-floci-cli)
    - [5.3 - The built-in floci-ui web console](#53---the-built-in-floci-ui-web-console)
    - [5.4 - Optional: the standalone floci-ui project (built from source)](#54---optional-the-standalone-floci-ui-project-built-from-source)
    - [5.5 - Optional: floci-dash, a second console](#55---optional-floci-dash-a-second-console)
  - [6. Network ports used](#6-network-ports-used)
  - [7. Tagging policy](#7-tagging-policy)
  - [8. Naming policy](#8-naming-policy)
  - [9. Flexible account and region](#9-flexible-account-and-region)
  - [10. Observations and limitations](#10-observations-and-limitations)
  - [11. References](#11-references)

<!-- TOC -->

# Requirements

This document lists the software and hardware needed to work through the
learning path in [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md). Every
module is designed to be deployed first against
[floci](https://floci.io) - a local AWS emulator - so you can complete the
entire path, and make mistakes, without an AWS account or any cost.
Deploying to a real AWS account afterward is optional and covered in each
module's own README.

**Never touched AWS CDK, Docker, or uv before? Start here.** The rest of
this document is reference material (exact versions, every option, every
port); this section is the one path to follow, top to bottom, the first
time.

## 0. Zero to your first deploy, in order

A few concepts first, so the commands below make sense instead of being
magic incantations to copy-paste:

- **AWS CDK** ("Cloud Development Kit") lets you describe AWS resources
  (a queue, a bucket, a database, ...) as Python code instead of clicking
  through the AWS Console or writing raw CloudFormation/JSON. You write a
  `Stack` (a Python class); the CDK turns it into a CloudFormation
  template; CloudFormation creates the actual resources.
- **`cdk synth`** ("synthesize") turns your Python code into that
  CloudFormation template, on your machine, without creating anything. It
  is the safe, free command you run constantly while learning - it cannot
  cost money or touch a real account.
- **`cdk deploy`** actually creates (or updates) the resources - against
  floci (free, local, see below) or a real AWS account, depending on which
  one your terminal is currently pointed at.
- **floci** is a program that pretends to be AWS on your own computer
  (`http://localhost:4566`). Every module in this repository is written to
  be deployed against floci first, so "deploying" while you learn never
  costs money and never touches a real account.
- **uv** installs the exact Python packages this project needs (including
  `aws-cdk-lib`, the library that provides `Stack`, `Bucket`, `Queue`, and
  everything else you'll import) into a private folder (`.venv/`) just for
  this project, so it can't conflict with anything else on your machine.

Now, step by step:

1. **Install the software** in [section 3](#3-required-software) for your
   operating system ([3.1](#31---install-on-ubuntu-amd64) for Ubuntu,
   [3.2](#32---install-on-macos-arm64-and-amd64) for macOS). This is a
   one-time setup.
2. **Get the code and enter the project folder**, if you haven't already:
   ```bash
   git clone <this-repository-url>
   cd learning-cdk-python
   ```
3. **Double-check your machine has everything step 1 asked for** - see
   [section 3.4](#34---running-and-reading-make-check) for how to read its
   output:
   ```bash
   make check
   ```
4. **Install this project's Python dependencies** - see
   [section 4](#4-project-setup-uv) for what this command does:
   ```bash
   uv sync
   ```
5. **Start floci** (your local, free, fake AWS) - see
   [section 5](#5-running-floci-the-local-aws-emulator) for what this does
   and for an alternative way (`floci-cli`) to do the same thing:
   ```bash
   docker compose up -d floci
   ```
6. **Point your terminal at floci**, not real AWS, by copying the example
   environment file and loading it into your current shell session (you'll
   repeat the `source` line in every new terminal window you open):
   ```bash
   cp .env.example .env
   set -a; source .env; set +a
   ```
7. **Confirm everything is wired up correctly** - this should print a CDK
   Toolkit version, then list 43 stack ids (one per deployable module - see
   [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md)), with no errors:
   ```bash
   uv run cdk --version
   uv run cdk list
   ```
8. **Pick the first module and follow its own README**, starting with
   [`modules/01_iam/README.md`](modules/01_iam/README.md) - every module's
   README has its own copy-pasteable "Deploy with floci" and "Clean up"
   commands, so you never need to guess a stack id or a flag.
9. **When you're done for the day**, stop floci so it isn't left running in
   the background:
   ```bash
   docker compose down
   ```

If any command above fails, re-run `make check` first - it usually
pinpoints exactly which tool or OS mismatch is the cause. Otherwise,
re-read the error message (uv, Docker, and the CDK CLI all print a
specific reason), then check
[section 10](#10-observations-and-limitations) for a known limitation
before assuming something is broken.

## 1. Supported operating systems

| OS | Architecture | Status |
|---|---|---|
| Ubuntu 22.04 LTS | `amd64` (`x86_64`) | Supported |
| Ubuntu 24.04 LTS | `amd64` (`x86_64`) | Supported |
| Ubuntu 26.04 LTS | `amd64` (`x86_64`) | Supported |
| macOS 13+ | `arm64` (Apple Silicon) | Supported |
| macOS 13+ | `amd64` (Intel) | Supported |
| Windows | - | Not directly supported - use WSL2 (Ubuntu, one of the rows above) |

Nothing in this repository is OS- or architecture-specific: every module
is plain, pure-Python CDK code (`aws-cdk-lib`, `constructs`, `boto3` all
ship as pure-Python or multi-arch wheels), `uv` and the AWS CDK Toolkit
(Node.js/npm) both publish native builds for `amd64` and `arm64` on both
Linux and macOS, and the `floci/floci` image used by
[`docker-compose.yml`](docker-compose.yml) is a
[multi-arch image](https://floci.io) (built for both `amd64` and `arm64`).
None of the three Ubuntu LTS releases above change any command in this
document - the same `apt`/`curl` install commands in
[section 3.1](#31---install-on-ubuntu-amd64) work unchanged across 22.04,
24.04, and 26.04.

## 2. Recommended hardware

| Resource | Minimum | Comfortable | Note |
|---|---|---|---|
| Free RAM | ~2 GB | ~4 GB | floci itself is lightweight; modules that use "real Docker" backends (ECS, EKS, RDS, ElastiCache - see [section 10](#10-observations-and-limitations)) use more while running |
| Free disk | ~2 GB | ~5 GB | the `floci/floci` image, `aws-cdk-lib`'s bundled assets, and uv's package cache |
| CPU | 2 vCPU | 4 vCPU | CDK synth/deploy and Docker |

## 3. Required software

**The fastest way to see exactly what's missing on your machine:** run
`make check` (see [section 3.4](#34---running-and-reading-make-check)) -
it checks your operating system and every row of the table below in one
go, and tells you exactly what to install.

| Software | Recommended version | Required? | What for |
|---|---|---|---|
| Python | 3.10+ | yes | `aws-cdk-lib` 2.271.0 requires Python >= 3.10 (see [PyPI](https://pypi.org/project/aws-cdk-lib/)) |
| [uv](https://docs.astral.sh/uv/) | latest | yes | Python package/venv manager used by every module - see [section 4](#4-project-setup-uv) |
| [mise](https://mise.jdx.dev) | latest | recommended | installs the exact Python version this repository pins (`.python-version`, `mise.toml`) - see [section 3.3](#33---managing-the-python-version-with-mise) |
| Node.js | 20 LTS+ | yes | the AWS CDK Toolkit (`aws-cdk`, the `cdk` CLI) is distributed as an npm package |
| AWS CDK Toolkit (`cdk`) | v2, matching `aws-cdk-lib`'s major version | yes | `cdk synth` / `cdk deploy` / `cdk destroy` - install with `npm install -g aws-cdk` or run on demand with `npx aws-cdk@2` |
| Docker Engine / Docker Desktop, or [Colima](https://github.com/abiosoft/colima) (macOS alternative - section 3.2) | 24+ | yes | runs floci (and, for some modules, floci's "real Docker" backends) |
| Docker Compose v2 (`docker compose`) | 2.20+ | yes | brings up `docker-compose.yml` |
| AWS CLI | v2 | recommended | used in every module's "Verify" section, pointed at floci or at a real account |
| git | 2.x | yes | - |
| floci CLI | latest | optional | an alternative to `docker compose` for running floci - see [section 5.2](#52---option-b-floci-cli) |

> **Guardrail:** the `aws-cdk-lib`/`constructs` version pins in
> [`pyproject.toml`](pyproject.toml) and the `floci/floci:latest` image tag in
> [`docker-compose.yml`](docker-compose.yml) were the current, stable
> versions at the time this material was written (September 2026). Re-check
> [PyPI](https://pypi.org/project/aws-cdk-lib/) and
> [Docker Hub](https://hub.docker.com/r/floci/floci/tags) before relying on
> them - both projects release frequently.

### 3.1 - Install on Ubuntu (amd64)

```bash
# Docker Engine + Compose plugin
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"   # log back in afterward

# git
sudo apt-get update && sudo apt-get install -y git

# uv (installs into ~/.local/bin)
curl -LsSf https://astral.sh/uv/install.sh | sh

# mise (optional but recommended - installs into ~/.local/bin; see section 3.3)
curl https://mise.run | sh
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc
# open a new terminal, then, from this repository's root:
mise trust && mise install

# Node.js (LTS) - see https://nodejs.org/en/download for other options
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# AWS CDK Toolkit
npm install -g aws-cdk

# AWS CLI v2 - see https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# floci CLI (optional - see section 5.2)
curl -fsSL https://floci.io/install.sh | sh
```

### 3.2 - Install on macOS (arm64 and amd64)

```bash
# Homebrew, if you don't have it yet:
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install --cask docker      # Docker Desktop - open the app at least once
brew install uv mise node awscli git
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc   # or ~/.bash_profile for bash
npm install -g aws-cdk
brew install floci-io/floci/floci-cli   # optional - see section 5.2
```

Open a new terminal (so the `mise activate` line above takes effect), then, from
this repository's root: `mise trust && mise install` - see
[section 3.3](#33---managing-the-python-version-with-mise) for what this does.

**Docker Desktop alternative: [Colima](https://github.com/abiosoft/colima).**
Anywhere this document or a module's README says `docker compose ...` or
`docker run ...`, a [Colima](https://github.com/abiosoft/colima)-provided
daemon works the same way - Colima is a free, open-source, lightweight
container runtime for macOS (and Linux) that provides a Docker-API-compatible
daemon, used through the same `docker`/`docker compose` CLI. Instead of the
`brew install --cask docker` line above:

```bash
brew install colima docker docker-compose
colima start                              # default resources
# or, with explicit resources (CPU cores, memory in GiB, disk in GiB):
colima start --cpu 4 --memory 8 --disk 60
```

The `docker` CLI works against Colima immediately after `colima start`, with
no extra configuration - see the
[Colima README](https://github.com/abiosoft/colima#usage). Homebrew's
`docker-compose` formula, though, installs the `docker-compose` binary
without registering it as a `docker compose` CLI plugin - if
`docker compose version` doesn't work after the install above, register it
the same way Colima's own FAQ documents for the (separate) Buildx plugin:

```bash
mkdir -p ~/.docker/cli-plugins
ln -sfn "$(brew --prefix)/opt/docker-compose/bin/docker-compose" ~/.docker/cli-plugins/docker-compose
docker compose version   # confirm it's now found
```

Everything else in this document (`docker compose up -d floci`, the
`/var/run/docker.sock` mount in `docker-compose.yml`, etc.) is unaffected by
which of the two you use - both present the same Docker API.

### 3.3 - Managing the Python version with mise

**New to version managers? Here's the problem one solves.** Your computer
probably already has a Python installed - but is it Python 3.10 or later
(what `aws-cdk-lib` requires - see the table above)? Is it the *same*
version a teammate has, or that this repository was tested with? Installing
a second, third, or tenth Python version by hand, and remembering to
`export PATH=...` to the right one in the right project, gets unmanageable
fast, especially once other projects on your machine want *different*
versions. A **version manager** solves this by installing exact tool
versions per-project and switching between them automatically, invisibly,
based on which directory you're in.

[mise](https://mise.jdx.dev) is one such version manager (in the same
family as tools like `pyenv`, `nvm`, or `rbenv` - the difference is that
mise handles many languages/tools through one CLI and one config file
format, instead of one tool per language). This repository declares its
Python version in [`mise.toml`](mise.toml):

```toml
[tools]
python = "3.12"
```

(the same version pinned in [`.python-version`](.python-version), which
`uv` also reads - see [section 4](#4-project-setup-uv)). Once mise is
installed and shell-activated (section 3.1/3.2 above), two commands set
everything up:

```bash
mise trust      # you're telling mise "I trust the mise.toml in this specific
                 # folder to run its declared tools" - a one-time confirmation
                 # per project, a safety measure since a malicious mise.toml
                 # could otherwise run arbitrary install scripts
mise install    # downloads and installs exactly Python 3.12 (if you don't
                 # already have that exact version via mise) into
                 # ~/.local/share/mise/ - it never touches or overwrites
                 # any Python your system already has installed elsewhere
```

After that, simply being in this repository's directory (with mise's shell
activation from section 3.1/3.2 in place) puts that exact Python version
first on your `PATH` - `cd` out to any other project and it's gone again,
replaced by whatever *that* project needs (or your system default, if none
is declared). Run `mise ls` at any time to see every tool/version mise has
installed, and `python --version` inside this repository's folder to
confirm you're on 3.12.

**Is mise required?** No - it's marked "recommended" in the table above,
not "yes". `uv` (section 4) is capable of downloading and managing its own
Python versions automatically, so `uv sync` works even without mise
installed at all, as long as *some* Python 3.10+ is reachable (or as a
fallback, uv fetches one itself). mise is offered for two reasons: (1) if
you're used to managing every language's version the same way across
several repositories (this GitHub account's other repositories already use
`mise.toml` the same way, for other languages), it keeps that one habit
here too; (2) pinning the interpreter itself, not just the packages
installed into it, is one less variable to debug if something behaves
differently on your machine than someone else's.

### 3.4 - Running and reading `make check`

**New to `make`?** [`Makefile`](Makefile) is a small automation file read by
the `make` command (pre-installed on Ubuntu and macOS, or `sudo apt-get
install -y build-essential` / Xcode Command Line Tools if it's ever
missing). It defines named **targets** - `make <target>` runs the shell
commands listed under that target in the `Makefile`. This repository
defines exactly two: `help` (the default - just running `make` with no
target shows this) and `check`.

**Run it:**

```bash
make check
```

This runs [`scripts/check-deps.sh`](scripts/check-deps.sh), which detects
your operating system/architecture and checks every row of the
[section 3](#3-required-software) table, printing one line per check:

```
== Operating system (REQUIREMENTS.md section 1) ==
  [ OK ] Ubuntu 24.04 (x86_64) - supported

== Required software (REQUIREMENTS.md section 3) ==
  [ OK ] Python 3.12.4 (>= 3.10 required)
  [FAIL] uv not found. See REQUIREMENTS.md, section 3 (Required software), ...
  ...
```

**Reading the output:**

| Marker | Meaning |
|---|---|
| `[ OK ]` | Found, and (where a minimum version applies) new enough. Nothing to do. |
| `[WARN]` | Either an optional/recommended tool is missing (see the "Required?" column in [section 3](#3-required-software)), or a required tool was found but is older than the recommended version. Worth reading, not necessarily worth stopping for. |
| `[FAIL]` | A **required** tool is missing, too old, or your OS/architecture isn't one this repository is tested on. **This is what blocks you** - every `[FAIL]` line names exactly what's missing and points back at this file. |

At the end, `make check` prints a one-line summary count of `[FAIL]`/`[WARN]`
items and exits with a status code you can check yourself
(`echo $?` right after, or use it in your own scripts/CI): **`0`** means
every required item passed (there may still be `[WARN]`s); **non-zero**
(`make` reports `1` from the script, though `make` itself may report `2` -
both mean "something required failed") means at least one `[FAIL]` needs
fixing before continuing to [section 4](#4-project-setup-uv).

**When something fails:** each `[FAIL]`/`[WARN]` line already tells you
which subsection of this document has the fix - usually
[section 3.1](#31---install-on-ubuntu-amd64) (Ubuntu) or
[section 3.2](#32---install-on-macos-arm64-and-amd64) (macOS). Install
just that one tool and re-run `make check` - it's safe to run as many
times as you like, it never installs or changes anything itself, it only
looks.

`make help` (or just `make`, since `help` is the default target) lists
both targets with a one-line description, if you forget the `check` name.

## 4. Project setup (uv)

This project's dependencies are declared in [`pyproject.toml`](pyproject.toml)
and locked in `uv.lock` (created by the command below). See
[uv - Getting started](https://docs.astral.sh/uv/getting-started/installation/)
and [Working with the AWS CDK in Python](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html)
for the concepts this setup is based on. `uv sync` reads
[`.python-version`](.python-version) to pick the interpreter it builds
`.venv/` with - if you set up mise ([section 3.3](#33---managing-the-python-version-with-mise)),
that's the same Python version mise installs, already on your `PATH`; if
you skipped mise, uv downloads a matching Python version on its own, so
either way works.

```bash
uv sync                 # creates .venv/ and installs aws-cdk-lib, constructs, boto3, and dev tools
uv run cdk --version    # sanity check: the cdk CLI can find aws-cdk-lib in the uv-managed venv
uv run cdk list         # lists every stack this repository can synthesize/deploy
```

`cdk.json`'s `"app"` entry is `uv run python app.py`, so every `cdk` command
below (`cdk synth`, `cdk deploy`, `cdk destroy`, `cdk diff`) already runs
through uv - you do not need to activate `.venv` manually, though
`source .venv/bin/activate` still works if you prefer it.

## 5. Running floci (the local AWS emulator)

[floci](https://floci.io) is a free, open-source AWS emulator - a drop-in
replacement for LocalStack Community - that every module in this repository
targets by default. It emulates the AWS API on `http://localhost:4566`, so
the AWS CLI, the AWS SDKs (`boto3`), and the AWS CDK all "just work" against
it once the right environment variables are set.

### 5.1 - Option A: docker compose (this repository's `docker-compose.yml`)

```bash
docker compose up -d floci
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

(See [`.env.example`](.env.example) for a file you can `source` instead of
exporting each variable by hand.)

### 5.2 - Option B: floci-cli

The [floci CLI](https://github.com/floci-io/floci-cli) manages the same
emulator's lifecycle without a `docker-compose.yml` of your own:

```bash
floci start                 # launches the emulator container and waits for readiness
eval $(floci env)           # exports AWS_ENDPOINT_URL, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
floci status                # container state and health
floci stop                  # stops the container
```

Use either option, not both at once (they would try to bind the same port).

### 5.3 - The built-in floci-ui web console

With either option above, a browser-based console for inspecting the
resources you create (S3 buckets, DynamoDB tables, SQS queues, Lambda logs,
...) is available at:

```
http://localhost:4566/_floci/ui
```

`docker-compose.yml` in this repository sets `FLOCI_SERVICES_UI_ENABLED: "true"`
and mounts the Docker socket, which the console needs to run its own sidecar
container - see [floci - AWS](https://floci.io/aws/) for the underlying
`FLOCI_SERVICES_UI_*` variables. This built-in console is enough for every
module in this learning path - section 5.4 below is optional.

### 5.4 - Optional: the standalone floci-ui project (built from source)

[floci-ui](https://github.com/floci-io/floci-ui) is also a separate,
richer open-source project (its own frontend + API, not the built-in
console in section 5.3 above), useful if you want a more full-featured
console or plan to contribute to floci-ui itself. It ships no published
Docker image - its own
[`docker-compose.yml`](https://github.com/floci-io/floci-ui/blob/main/docker-compose.yml)
*builds* the frontend and API from source, so using it here means cloning
that repository first:

```bash
# Clone floci-ui next to this repository (the default this repo's
# docker-compose.yml looks for - see FLOCI_UI_REPO_PATH below to use a
# different location):
git clone https://github.com/floci-io/floci-ui.git ../floci-ui

# From this repository's root, build and start the floci-ui + floci-api
# services (the "floci-ui" Compose profile) alongside floci itself:
docker compose --profile floci-ui up -d --build

# floci-ui (frontend):  http://localhost:4500
# floci-api (backend):  http://localhost:4501
```

If you cloned `floci-ui` somewhere other than `../floci-ui`, point
`docker-compose.yml` at it with:

```bash
export FLOCI_UI_REPO_PATH=/path/to/your/floci-ui
docker compose --profile floci-ui up -d --build
```

To pick up floci-ui's own updates later, pull and rebuild:

```bash
git -C ../floci-ui pull
docker compose --profile floci-ui up -d --build
```

This repository's `floci-api` service intentionally omits the
`FLOCI_AZURE_ENDPOINT`/`FLOCI_GCP_ENDPOINT` variables that floci-ui's own
`docker-compose.yml` sets for its optional multi-cloud panels - this
learning path is AWS-only and doesn't run the `floci-az`/`floci-gcp`
emulators those variables point at.

### 5.5 - Optional: floci-dash, a second console

[floci-dash](https://github.com/ofsazib/floci-dash) is a separate,
unrelated open-source project (a different author than floci-ui above)
that provides its own "AWS Console-style" browser dashboard for floci.
Unlike floci-ui (section 5.4), it publishes a ready-made
**dashboard-only** image, so it needs no source clone - just enable its
Compose profile:

```bash
docker compose --profile floci-dash up -d
# floci-dash: http://localhost:9877
```

`docker-compose.yml`'s `floci-dash` service points `FLOCI_URL` at this
file's own `floci` service (not a second emulator) and waits for its
`healthcheck` before starting, the same way floci-dash's own
`docker-compose.yml` does for the bundled `floci` service it ships (this
repository uses floci-dash's **dashboard-only** image, `ghcr.io/ofsazib/floci-dash:latest`,
specifically to reuse the one `floci` container instead of running two).

**Running floci-dash and floci-ui at the same time.** They're independent
Compose profiles on different ports (floci-dash: `9877`; floci-ui:
`4500`/`4501` - section 5.4), so nothing stops you from enabling both,
alongside the built-in console (section 5.3) that's always on with the
default `docker compose up -d floci`:

```bash
docker compose --profile floci-ui --profile floci-dash up -d --build
```

## 6. Network ports used

| Port | Service | Note |
|---|---|---|
| `4566` | floci (AWS-compatible API + `/_floci/ui` console) | published by `docker-compose.yml` |
| `4500` | floci-ui (standalone frontend) | only with `--profile floci-ui` - see section 5.4 |
| `4501` | floci-api (standalone backend) | only with `--profile floci-ui` - see section 5.4 |
| `9877` | floci-dash (dashboard) | only with `--profile floci-dash` - see section 5.5 |

## 7. Tagging policy

Every resource created in this repository carries these 7 tags, applied by
[`shared/tagging.py`](shared/tagging.py) (see that file's docstring for the
exact CDK calls):

| Tag key | Value | Notes |
|---|---|---|
| `Name` | e.g. `learning-cdk-python-dev-orders-queue` | AWS's own default tag for displaying a resource's name in the console - the only tag key in this repository kept capitalized, and the only one applied per-resource rather than once per stack |
| `environment` | e.g. `dev`, `staging`, `prod` | |
| `product` | e.g. `learning-cdk-python` | the product/system this resource belongs to |
| `team-owner` | e.g. `platform-engineering` | the team responsible for the resource |
| `pci` | `true` or `false` | whether the resource is in scope for PCI DSS |
| `cell-based` | `true` or `false` | whether the resource belongs to a [cell-based architecture](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/cell-based-architecture.html) deployment |
| `cell-id` | e.g. `cell-01` | present **only** when `cell-based` is `true` |

Tag *values* other than `Name` and `cell-id` are configured once, for the
whole app, via the `CDK_*` environment variables in
[`.env.example`](.env.example) and resolved by
[`shared/config.py`](shared/config.py).

## 8. Naming policy

Physical resource names (bucket names, queue names, function names, ...) are
built by [`shared/naming.py`](shared/naming.py) and use `-` as the
separator, e.g. `learning-cdk-python-dev-orders-queue`. `_` is used only
where a specific AWS resource type's naming rules forbid hyphens - each
module's README links to that service's naming-rules page when this
applies.

## 9. Flexible account and region

No module hardcodes an AWS account ID or region. [`shared/config.py`](shared/config.py)
builds the stacks' `env=` from `CDK_DEFAULT_ACCOUNT` / `CDK_DEFAULT_REGION`
(set automatically by the CDK CLI from your AWS CLI credentials/profile) or
falls back to an "environment-agnostic" stack - see
[AWS CDK - Environments](https://docs.aws.amazon.com/cdk/v2/guide/environments.html).
Any Availability Zone selection (for example, in `modules/03_vpc`) uses
`max_azs`/CloudFormation pseudo parameters rather than a hardcoded AZ name,
for the same reason.

## 10. Observations and limitations

- **floci emulates the AWS API, not AWS's exact internal behavior**, and
  service coverage/fidelity varies by service - see the
  [floci](https://floci.io) site for what's covered. A module's README says
  when a service is better verified against a real account than against
  floci.
- **"Real Docker" backends.** floci runs some services (Lambda, RDS,
  ElastiCache, ECS, EKS, among others - see [floci - AWS](https://floci.io/aws/))
  as actual Docker containers rather than lightweight mocks, which is more
  faithful but also means those modules need more RAM/CPU and take longer to
  start than, say, an S3 bucket or an SQS queue.
- **Deploying to a real AWS account has real cost** for some modules (NAT
  Gateway, RDS, OpenSearch, EKS, ElastiCache, in particular - hourly
  charges start the moment the resource exists). Each such module's README
  has a "Notes and cautions" section calling this out explicitly before its
  optional "Deploy to real AWS" instructions.

## 11. References

- [floci - Local AWS Emulator](https://floci.io) · [github.com/floci-io/floci](https://github.com/floci-io/floci) · [github.com/floci-io/floci-cli](https://github.com/floci-io/floci-cli) · [github.com/floci-io/floci-ui](https://github.com/floci-io/floci-ui)
- [uv - Getting started](https://docs.astral.sh/uv/getting-started/installation/)
- [mise - Getting started](https://mise.jdx.dev/getting-started.html) · [mise - Installing mise](https://mise.jdx.dev/installing-mise.html)
- [AWS CDK v2 Developer Guide - Working with the AWS CDK in Python](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html)
- [AWS CDK v2 Developer Guide - Environments](https://docs.aws.amazon.com/cdk/v2/guide/environments.html)
- [AWS CDK v2 Developer Guide (home)](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [AWS CDK API Reference (Python)](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [`aws-cdk-lib` on PyPI](https://pypi.org/project/aws-cdk-lib/) · [`constructs` on PyPI](https://pypi.org/project/constructs/)
- [Docker Engine - Install on Ubuntu](https://docs.docker.com/engine/install/ubuntu/) · [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) · [Colima](https://github.com/abiosoft/colima) (macOS/Linux Docker Desktop alternative)
- [AWS CLI v2 - Install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [GNU Make Manual](https://www.gnu.org/software/make/manual/make.html)
