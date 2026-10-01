<!-- TOC -->

- [Requirements](#requirements)
  - [0. Zero to your first deploy, in order](#0-zero-to-your-first-deploy-in-order)
  - [1. Supported operating systems](#1-supported-operating-systems)
  - [2. Recommended hardware](#2-recommended-hardware)
  - [3. Required software](#3-required-software)
    - [3.1 - Install on Ubuntu (amd64)](#31---install-on-ubuntu-amd64)
    - [3.2 - Install on macOS (arm64 and amd64)](#32---install-on-macos-arm64-and-amd64)
    - [3.3 - Managing tool versions with mise](#33---managing-tool-versions-with-mise)
    - [3.4 - Running and reading `make check`](#34---running-and-reading-make-check)
  - [4. Project setup (uv)](#4-project-setup-uv)
  - [5. Running floci (the local AWS emulator)](#5-running-floci-the-local-aws-emulator)
    - [5.1 - Option A: docker compose (this repository's `docker-compose.yml`)](#51---option-a-docker-compose-this-repositorys-docker-composeyml)
    - [5.2 - Option B: floci-cli](#52---option-b-floci-cli)
    - [5.3 - The built-in floci-ui web console](#53---the-built-in-floci-ui-web-console)
    - [5.4 - Optional: the standalone floci-ui project (built from source)](#54---optional-the-standalone-floci-ui-project-built-from-source)
    - [5.5 - Optional: floci-dash, a second console](#55---optional-floci-dash-a-second-console)
    - [5.6 - Optional: `make` shortcuts for floci and the CDK](#56---optional-make-shortcuts-for-floci-and-the-cdk)
    - [5.7 - Bootstrapping the CDK (once per floci instance or AWS account/region)](#57---bootstrapping-the-cdk-once-per-floci-instance-or-aws-accountregion)
    - [5.8 - Re-running `cdk deploy` on floci without duplicating resources](#58---re-running-cdk-deploy-on-floci-without-duplicating-resources)
    - [5.9 - `cdk destroy` on floci leaves VPCs behind](#59---cdk-destroy-on-floci-leaves-vpcs-behind)
    - [5.10 - Listing every resource a stack created](#510---listing-every-resource-a-stack-created)
    - [5.11 - Previewing changes with `cdk diff`](#511---previewing-changes-with-cdk-diff)
  - [6. Network ports used](#6-network-ports-used)
  - [7. Tagging policy](#7-tagging-policy)
  - [8. Naming policy](#8-naming-policy)
  - [9. Flexible account and region](#9-flexible-account-and-region)
  - [10. Observations and limitations](#10-observations-and-limitations)
  - [11. Building, rendering and exporting the slide decks (Marp)](#11-building-rendering-and-exporting-the-slide-decks-marp)
    - [11.1 - Installing Marp CLI](#111---installing-marp-cli)
    - [11.2 - Rendering and exporting `docs/slides/SLIDES-*.md`](#112---rendering-and-exporting-docsslidesslides-md)
    - [11.3 - Enabling HTML in a live preview (VS Code / marp.app)](#113---enabling-html-in-a-live-preview-vs-code--marpapp)
  - [12. References](#12-references)

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
- **`cdk diff`** compares what `cdk synth` would produce *now* with what is
  already deployed, and prints the difference - resources that would be
  added (`[+]`), removed (`[-]`), or changed (`[~]`). Like `cdk synth`, it
  changes nothing; run it before every `cdk deploy` to see what the deploy
  is about to do (section 5.11).
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
   Toolkit version, then list 45 stack ids (one per deployable module - see
   [`docs/LEARNING-PATH.md`](docs/LEARNING-PATH.md)), with no errors:
   ```bash
   uv run cdk --version
   uv run cdk list
   ```
8. **Bootstrap the CDK in floci** - a one-time step that prepares floci to
   receive CDK deployments (see
   [section 5.7](#57---bootstrapping-the-cdk-once-per-floci-instance-or-aws-accountregion)
   for what it does and why). Skip it and your first `cdk deploy` fails with
   `SsmParameterNotFound: SSM parameter /cdk-bootstrap/hnb659fds/version not found`:
   ```bash
   uv run cdk bootstrap
   ```
   Run it again on every new computer, and after `make floci-destroy` or
   deleting `./.floci/` - floci's state lives only on the machine that runs
   it. Running it when it isn't needed is harmless.
9. **Pick the first module and follow its own README**, starting with
   [`modules/01_iam/README.md`](modules/01_iam/README.md) - every module's
   README has its own copy-pasteable "Deploy with floci" and "Clean up"
   commands, so you never need to guess a stack id or a flag.
10. **When you're done for the day**, stop floci so it isn't left running in
    the background (its state, including the bootstrap from step 8, is
    kept):
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
| Python | 3.14 | yes | pinned in `.python-version`/`mise.toml` and required by `pyproject.toml` (`requires-python = ">=3.14"`); `aws-cdk-lib` 2.271.0 itself supports Python 3.10-3.14 (see [PyPI](https://pypi.org/project/aws-cdk-lib/)) - `uv sync` downloads 3.14 automatically if you don't have it |
| [uv](https://docs.astral.sh/uv/) | latest | yes | Python package/venv manager used by every module - see [section 4](#4-project-setup-uv) |
| [mise](https://mise.jdx.dev) | latest | recommended | installs the exact Python, Node.js, npm, and AWS CLI versions this repository pins (`mise.toml`, `.python-version`) - see [section 3.3](#33---managing-tool-versions-with-mise) |
| Node.js | 26 | yes | the AWS CDK Toolkit (`aws-cdk`, the `cdk` CLI) is distributed as an npm package - installed by `mise install` (pinned in `mise.toml`), see [section 3.3](#33---managing-tool-versions-with-mise) |
| npm | 11 | yes | installs the AWS CDK Toolkit (`npm install -g aws-cdk`) and provides `npx` - installed by `mise install` (pinned in `mise.toml`) |
| AWS CDK Toolkit (`cdk`) | v2, matching `aws-cdk-lib`'s major version | yes | `cdk synth` / `cdk deploy` / `cdk destroy` - install with `npm install -g aws-cdk` or run on demand with `npx aws-cdk@2` |
| Docker Engine / Docker Desktop, or [Colima](https://github.com/abiosoft/colima) (macOS alternative - section 3.2) | 24+ | yes | runs floci (and, for some modules, floci's "real Docker" backends) |
| Docker Compose v2 (`docker compose`) | 2.20+ | yes | brings up `docker-compose.yml` |
| AWS CLI | v2 | recommended | used in every module's "Verify" section, pointed at floci or at a real account - installed by `mise install` (pinned in `mise.toml`), see [section 3.3](#33---managing-tool-versions-with-mise) |
| git | 2.x | yes | - |
| floci CLI | latest | optional | an alternative to `docker compose` for running floci - see [section 5.2](#52---option-b-floci-cli) |
| [Marp CLI](https://github.com/marp-team/marp-cli) (`@marp-team/marp-cli`) | latest | optional | render/export `docs/slides/SLIDES-*.md` to HTML/PDF/PPTX - see [section 11](#11-building-rendering-and-exporting-the-slide-decks-marp) |

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

# mise (recommended - installs into ~/.local/bin; see section 3.3)
curl https://mise.run | sh
echo 'eval "$(~/.local/bin/mise activate bash)"' >> ~/.bashrc   # Bash; Zsh/Fish/others: section 3.3
# open a new terminal, then, from this repository's root - installs
# Python, Node.js 26, npm 11, and the AWS CLI v2 pinned in mise.toml:
mise trust && mise install

# AWS CDK Toolkit (uses the mise-managed Node.js/npm installed above)
npm install -g aws-cdk

# floci CLI (optional - see section 5.2)
curl -fsSL https://floci.io/install.sh | sh
```

### 3.2 - Install on macOS (arm64 and amd64)

```bash
# Homebrew, if you don't have it yet:
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install --cask docker      # Docker Desktop - open the app at least once
brew install uv git
curl https://mise.run | sh
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc   # Zsh (macOS default); other shells: section 3.3
brew install floci-io/floci/floci-cli   # optional - see section 5.2
```

Open a new terminal (so the `mise activate` line above takes effect), then,
from this repository's root:

```bash
mise trust && mise install   # Python, Node.js 26, npm 11, and the AWS CLI v2 pinned in mise.toml
npm install -g aws-cdk       # AWS CDK Toolkit, using the mise-managed Node.js/npm
```

See [section 3.3](#33---managing-tool-versions-with-mise) for what this does.

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

### 3.3 - Managing tool versions with mise

**New to version managers? Here's the problem one solves.** Your computer
probably already has a Python installed - but is it Python 3.14 (what this
repository requires - see the table above)? Is it the *same*
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
format, instead of one tool per language). This repository declares four
tools in [`mise.toml`](mise.toml):

```toml
[tools]
python = "3.14"
node = "26"
npm = "11"
aws-cli = "2"
```

- `python` - the same version pinned in [`.python-version`](.python-version),
  which `uv` also reads - see [section 4](#4-project-setup-uv).
- `node` - Node.js 26 (`"26"` means "the latest 26.x release"), which runs
  the AWS CDK Toolkit (`cdk`) and the optional Marp/Mermaid CLIs via `npx`.
  Global packages (`npm install -g aws-cdk`) are installed inside mise's
  Node.js 26 directory, so they're on your `PATH` only while that version is
  active - reinstall them after switching Node.js versions.
- `npm` - npm 11, pinned separately (mise registry backend `aqua:npm/cli`)
  instead of relying on whichever npm Node.js happens to bundle; it takes
  precedence over the bundled one on your `PATH`.
- `aws-cli` - the AWS CLI v2 (the `aws` command every module's "Verify"
  section uses). mise downloads it from the official
  [aws/aws-cli](https://github.com/aws/aws-cli) releases (its registry
  backend is `aqua:aws/aws-cli`); `"2"` means "the latest 2.x release",
  so no `sudo`, no `.zip` installer, and no system-wide `/usr/local/bin/aws`
  is involved. Pin a full version instead (e.g. `aws-cli = "2.37.6"`) if you
  need an exact, reproducible build - run `mise ls-remote aws-cli` to see
  the current releases first, since they change often.

**Activate mise in your shell (once per machine).** mise only switches
tools automatically as you `cd` into this repository if your shell runs
`mise activate` at startup. Add the line matching your shell, once, to that
shell's interactive startup file, then open a new terminal (commands from
the official [`mise activate` reference](https://mise.jdx.dev/cli/activate.html)):

| Shell | Startup file | Line to add |
|---|---|---|
| Bash | `~/.bashrc` | `eval "$(mise activate bash)"` |
| Zsh | `~/.zshrc` | `eval "$(mise activate zsh)"` |
| Fish | `~/.config/fish/config.fish` | `mise activate fish \| source` |
| Xonsh | your Xonsh startup file | `execx($(mise activate xonsh))` |
| PowerShell | `$PROFILE` | `(&mise activate pwsh) \| Out-String \| Invoke-Expression` |

Not sure which shell you're using? Run `echo $SHELL` (Bash/Zsh/Fish on
Ubuntu and macOS). Or append the line from a terminal, for example:

```bash
echo 'eval "$(mise activate bash)"' >> ~/.bashrc                  # Bash
echo 'eval "$(mise activate zsh)"' >> ~/.zshrc                    # Zsh
echo 'mise activate fish | source' >> ~/.config/fish/config.fish  # Fish
```

The `mise` executable must already be on your `PATH` when that line runs.
If it isn't (for example, right after the `curl https://mise.run | sh`
install in section 3.1, which puts it in `~/.local/bin`), use its absolute
path instead, e.g. `eval "$(~/.local/bin/mise activate bash)"`. mise
supports `elvish` and `nu` too - see the
[shell activation guide](https://mise.jdx.dev/getting-started.html) for
those. In scripts or CI, where there's no interactive shell to activate,
skip activation and use `mise exec -- aws ...` instead.

Once mise is installed and activated, two commands set everything up:

```bash
mise trust      # you're telling mise "I trust the mise.toml in this specific
                 # folder to run its declared tools" - a one-time confirmation
                 # per project, a safety measure since a malicious mise.toml
                 # could otherwise run arbitrary install scripts
mise install    # downloads and installs exactly Python 3.14, Node.js 26,
                 # npm 11, and the AWS CLI v2 (if you don't already have
                 # those versions via mise) into ~/.local/share/mise/ - it
                 # never touches or overwrites any Python, Node.js, npm,
                 # or `aws` your system already has installed elsewhere
```

After that, simply being in this repository's directory (with mise's shell
activation from section 3.1/3.2 in place) puts those exact Python,
Node.js, npm, and AWS CLI versions first on your `PATH` - `cd` out to any
other project and it's gone again,
replaced by whatever *that* project needs (or your system default, if none
is declared). Run `mise ls` at any time to see every tool/version mise has
installed, and `python --version` / `node --version` / `npm --version` /
`aws --version` inside this repository's folder to confirm you're on Python 3.14,
Node.js `v26.x`, npm `11.x`, and `aws-cli/2.x`.

To move to a newer release within the same major version later, run
`mise upgrade` (or `mise upgrade node npm aws-cli` for specific tools) - with
`node = "26"`, `npm = "11"`, and `aws-cli = "2"`, this picks up the newest
26.x/11.x/2.x release. To change a major version, edit it in `mise.toml`
and run `mise install` again (then `npm install -g aws-cdk` again, for the
reason explained under `node` above). For Python, also update
`.python-version` to match and run `uv sync` to rebuild `.venv/` - see
[section 4](#4-project-setup-uv).

**Already using nvm, fnm, Volta, or a system Node.js?** Whichever directory
comes first on your `PATH` wins. `mise activate` puts mise's tools first
when it runs, so place the `mise activate` line **after** any other Node.js
version manager's setup lines in your shell startup file. Then check with
`command -v node` (should print a path under `~/.local/share/mise/`) and
`npm prefix -g` (should print mise's Node.js 26 directory - if it prints
another manager's directory, `npm install -g aws-cdk` puts `cdk` there
instead).

Without shell activation (in scripts or CI, for example), `mise exec --
<command>` runs a command with the same pinned tools, e.g. `mise exec -- aws
--version`.

**Is mise required?** No - it's marked "recommended" in the table above,
not "yes". `uv` (section 4) is capable of downloading and managing its own
Python versions automatically, so `uv sync` works even without mise
installed at all - if Python 3.14 isn't already on your machine, uv
downloads it itself. mise is offered for two reasons: (1) if
you're used to managing every language's version the same way across
several repositories (this GitHub account's other repositories already use
`mise.toml` the same way, for other languages), it keeps that one habit
here too; (2) pinning the interpreter itself, not just the packages
installed into it, is one less variable to debug if something behaves
differently on your machine than someone else's.

**Skipping mise? Install Node.js and the AWS CLI yourself.** Without mise,
nothing else in this repository installs `node`, `npm`, or `aws`. On Ubuntu
(amd64):

```bash
# Node.js 26 (bundles npm 11) - see https://nodejs.org/en/download for other options
curl -fsSL https://deb.nodesource.com/setup_26.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g npm@11     # only if `npm --version` isn't 11.x already

# AWS CLI v2 - https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install
```

On macOS, `brew install awscli` for the AWS CLI, and Node.js 26 from
[nodejs.org](https://nodejs.org/en/download) (Homebrew's `node` formula
follows the newest Node.js release, which may not be 26).

### 3.4 - Running and reading `make check`

**New to `make`?** [`Makefile`](Makefile) is a small automation file read by
the `make` command (pre-installed on Ubuntu and macOS, or `sudo apt-get
install -y build-essential` / Xcode Command Line Tools if it's ever
missing). It defines named **targets** - `make <target>` runs the shell
commands listed under that target in the `Makefile`. This repository
defines `help` (the default - just running `make` with no target lists
every target), `check` (covered here), `typecheck` (runs `mypy` - see
[`CONTRIBUTING.md`](CONTRIBUTING.md)), `coverage` (runs every test with a
coverage report - see [`docs/TESTING.md`, "Test coverage"](docs/TESTING.md#test-coverage)),
and the `floci-*`/`cdk-*` shortcuts in
[section 5.6](#56---optional-make-shortcuts-for-floci-and-the-cdk).

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
  [ OK ] Python 3.14.7 (3.14 pinned in .python-version/mise.toml)
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
`.venv/` with - if you set up mise ([section 3.3](#33---managing-tool-versions-with-mise)),
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

### 5.6 - Optional: `make` shortcuts for floci and the CDK

**Learn the long form first.** Every module's README, and every section
above, uses the full commands - `docker compose up -d floci`,
`set -a; source .env; set +a`, `uv run cdk synth VpcStack`, ... - because
knowing what each one does is part of what this path teaches. Once those
feel familiar, the [`Makefile`](Makefile) targets below run the same
commands for you (each one prints the command it runs), so you can move
faster. They're a shortcut, not a replacement: nothing in this repository
requires them.

| Target | What it does | Long form it replaces |
|---|---|---|
| `make floci-status` | shows whether floci (and any console) is running, plus every URL | `docker compose ps` |
| `make floci-start` | starts floci, if it isn't already healthy, and waits until it is | `docker compose up -d floci` |
| `make floci-start UI=floci-dash` | same, plus the floci-dash console (section 5.5); `UI=floci-ui` for floci-ui (section 5.4, needs its clone), `UI="floci-ui floci-dash"` for both | `docker compose --profile floci-dash up -d` |
| `make floci-stop` | stops floci and any console, keeping every deployed resource | `docker compose --profile floci-ui --profile floci-dash stop` |
| `make floci-destroy` | removes floci, its consoles, **and every resource deployed to it** (`./.floci/`) - asks you to type `yes` first (`CONFIRM=yes` skips the question) | `docker compose ... down` + deleting `./.floci/` |
| `make cdk-destroy STACK=VpcStack` | destroys one stack (or `STACK=all`, or `EXAMPLE=enterprise ENV=...`) from floci, then deletes the VPCs floci leaves behind (section 5.9) | `uv run cdk destroy VpcStack` + `uv run python scripts/floci_prune.py --apply` |
| `make cdk-diff STACK=SqsStack` | shows what a deploy would change, without changing anything (section 5.11); no `STACK` = every stack, or `EXAMPLE=enterprise ENV=...` | `uv run cdk diff SqsStack` |
| `make cdk-resources STACK=SqsStack` | runs every "List every resource with the AWS CLI" command for that stack (or `STACK=all`, or `EXAMPLE=enterprise ENV=...`) and reports what each found - read-only (section 5.10) | the README section's commands, one by one |
| `make floci-prune` | lists the VPCs floci left behind after `cdk destroy`; `APPLY=yes` deletes them (section 5.9) | `uv run python scripts/floci_prune.py [--apply]` |
| `make cdk-synth STACK=VpcStack` | synthesizes one module's stack (no `STACK` = every stack) | `uv run cdk synth VpcStack` |
| `make cdk-synth EXAMPLE=enterprise ENV=stg` | synthesizes the [enterprise example](examples/enterprise_stack/README.md) for `dev`, `stg`, or `prd` | `ENTERPRISE_ENVIRONMENT=stg uv run cdk synth --app "uv run python examples/enterprise_stack/app.py"` |
| `make cdk-deploy STACK=VpcStack` | bootstraps floci (if needed) and deploys one stack to it; `STACK=all` deploys every module, `EXAMPLE=enterprise ENV=...` the example (for `ENV=prd`, acting as `prd.json`'s account and bootstrapping its regions - see the [enterprise README, section 9](examples/enterprise_stack/README.md#9-running-it)) | `uv run cdk bootstrap` + `uv run cdk deploy VpcStack --require-approval never --method=direct` |

Details worth knowing:

- `cdk-synth` and `cdk-deploy` always run `floci-status` and then
  `floci-start` first, so floci is up before any CDK command talks to it.
- Both load your `.env` (or, if you haven't created one, `.env.example`)
  exactly like step 6 of [section 0](#0-zero-to-your-first-deploy-in-order).
- `cdk-deploy` **only deploys to floci**: it refuses to run if
  `AWS_ENDPOINT_URL` isn't set in that file. To deploy to a real AWS
  account, follow a module README's "Deploy to real AWS" section by hand.
- `make cdk-destroy` (same `STACK=`/`EXAMPLE=`/`ENV=` options as
  `cdk-deploy`) destroys, then deletes the VPCs floci leaves behind (section
  5.9); `make floci-destroy` wipes everything at once.
- Run `make` with no target to list every target and these examples.

### 5.7 - Bootstrapping the CDK (once per floci instance or AWS account/region)

**What bootstrapping is.** Before the CDK can deploy anything to an
environment (an AWS account + region - or, here, floci), that environment
must be *bootstrapped*: `cdk bootstrap` deploys a CloudFormation stack
called `CDKToolkit` with the resources every later `cdk deploy` relies on
- an S3 bucket for templates and assets, an ECR repository for Docker
images, IAM roles for deployments, and an SSM parameter recording the
bootstrap version. The CDK never does this automatically, and each
environment is bootstrapped independently - see
[AWS CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html).

**Why a missing bootstrap shows up as `SsmParameterNotFound`.** Every
template this repository synthesizes contains this parameter (open any
`cdk.out/*.template.json` after a `cdk synth` to see it):

```json
"BootstrapVersion": {
  "Type": "AWS::SSM::Parameter::Value<String>",
  "Default": "/cdk-bootstrap/hnb659fds/version"
}
```

plus a `CheckBootstrapVersion` rule that rejects versions older than the
one the CDK needs. So the first thing a deploy does is read the SSM
parameter `/cdk-bootstrap/hnb659fds/version` (`hnb659fds` is the CDK's
default bootstrap "qualifier"). Only `cdk bootstrap` creates it - so in a
never-bootstrapped environment, the deploy stops with:

```
IamStack: SSM parameter /cdk-bootstrap/hnb659fds/version not found in aws://000000000000/us-east-1.
Has the environment been bootstrapped? Please run 'cdk bootstrap' ...
‣ SsmParameterNotFound: ...
```

**Why it works on one computer and not on another.** floci is a separate
AWS "environment" on every machine: its state - including the
`CDKToolkit` stack and that SSM parameter - is stored in `./.floci/data`
(`FLOCI_STORAGE_MODE: persistent` in [`docker-compose.yml`](docker-compose.yml)),
which is local to that computer and not committed to git (see
[`.gitignore`](.gitignore)). A fresh clone on a second computer starts
with an empty floci, so it needs its own `cdk bootstrap`.

**When to run it:**

| Situation | Run `cdk bootstrap`? |
|---|---|
| First time on this computer (step 8 of [section 0](#0-zero-to-your-first-deploy-in-order)) | yes |
| After `make floci-destroy`, or deleting `./.floci/` | yes - the state is gone |
| After `docker compose down`/`up`, `make floci-stop`/`floci-start`, or a reboot | no - persistent mode keeps it |
| After upgrading the CDK CLI, if a deploy asks for a newer bootstrap version | yes - it upgrades the stack in place |
| Before your first deploy to each real AWS account + region | yes, once per account/region (`uv run cdk bootstrap --profile <your-aws-cli-profile>`) |

Re-running it is always safe: if nothing changed it reports
`bootstrapped (no changes)`. `make cdk-deploy` (section 5.6) runs it for
you before every deploy.

**Check whether an environment is bootstrapped:**

```bash
aws cloudformation describe-stacks --stack-name CDKToolkit --query "Stacks[0].StackStatus"
aws ssm get-parameter --name /cdk-bootstrap/hnb659fds/version --query Parameter.Value
```

### 5.8 - Re-running `cdk deploy` on floci without duplicating resources

**Always add `--method=direct` when deploying to floci** - every module's
"Deploy with floci" command already does:

```bash
uv run cdk deploy KmsStack --require-approval never --method=direct
```

**The problem it avoids.** With the default deploy method, running
`cdk deploy` a second time on an unchanged stack creates a *second* copy of
some resources on floci - a new KMS key, a new API Gateway REST API, and so
on - each time, leaving the old ones orphaned (still there, no longer in
the stack). Resources with a fixed physical name (an SQS queue, an S3
bucket) aren't duplicated, but resources AWS identifies only by a generated
ID (a KMS key) or whose names needn't be unique (REST APIs) are.

**Why it happens** (checked while writing this - re-check with newer floci
and CDK versions):

1. The CDK CLI deploys through a CloudFormation *change set*: it creates
   one, and executes it only if it contains changes. It recognizes an
   empty change set the way real CloudFormation reports one - status
   `FAILED` with the reason "The submitted information didn't contain
   changes".
2. floci reports an empty change set as `CREATE_COMPLETE` with no changes
   listed, so the CDK executes it as a normal update.
3. floci's update re-creates resources that have no fixed physical name,
   even when their properties didn't change.

**Why `--method=direct` fixes it.** It deploys without a change set. In that
mode the CDK first compares the template it just synthesized with the one
already deployed and, when they're identical, skips the deployment
entirely (`✅  KmsStack (no changes)`) - floci is never asked to update
anything. On real AWS, the default change-set method behaves correctly, so
the "Deploy to real AWS" commands keep it. `make cdk-deploy` (section 5.6)
always uses `--method=direct`.

**What it can't fix.** When you *change* a stack's code and deploy again,
floci still performs an update, and step 3 still re-creates the unnamed
resources. For a clean result after a code change on floci, recreate the
stack instead: `uv run cdk destroy <StackId>` then deploy again. If orphans
have already piled up, `make floci-destroy` (section 5.6) wipes floci
completely; bootstrap again afterwards (section 5.7).

### 5.9 - `cdk destroy` on floci leaves VPCs behind

**The problem.** On floci, `cdk destroy` of a stack that creates a VPC
deletes the stack and everything in the VPC - subnets, route tables,
internet and NAT gateways, Elastic IPs, security groups, instances - but
leaves the **VPC itself** behind, empty except for the default security
group and main route table every VPC comes with. Deploy the stack again and
it creates a new VPC, so each destroy + deploy cycle adds one more
duplicate. (Checked while writing this by destroying one stack of each
networking kind: exactly one VPC per destroyed VPC was left, and nothing
else. Re-running `cdk deploy` without a destroy duplicates nothing - see
section 5.8.)

**Why.** floci's CloudFormation has no delete step for `AWS::EC2::VPC`: its
VPC provisioner says so in its source ("stack teardown leaves the VPC
alone"). Real AWS CloudFormation deletes VPCs normally, so this only
affects floci.

**The fix: delete orphan VPCs after destroying.** A VPC is an *orphan* when
it isn't a default VPC and no CloudFormation stack (nested stacks
included) lists it as a resource. [`scripts/floci_prune.py`](scripts/floci_prune.py)
finds them and, with `--apply`, deletes them (and anything still inside
them):

```bash
uv run cdk destroy VpcStack
uv run python scripts/floci_prune.py            # list orphan VPCs (dry run)
uv run python scripts/floci_prune.py --apply    # delete them
```

Every module that creates a VPC has this line in its "Clean up" section.
The script uses your current credentials' account (floci maps the access
key to an account - see the enterprise example's README, section 9) and
`AWS_DEFAULT_REGION`; pass `--region` once per region to check others. It
refuses to run unless `AWS_ENDPOINT_URL` points at floci, so it can never
touch a real AWS account. `make cdk-destroy` (section 5.6) destroys and
then runs it for you; `make floci-prune` runs it on its own.

### 5.10 - Listing every resource a stack created

`cdk deploy` printing ✅ means CloudFormation reports success - not that you
have looked at what it built. Every module README (and the enterprise
example's, section 9.1) has a **"List every resource with the AWS CLI"**
section: one `aws` command per resource the stack creates, so you can see
each one with the same tool you'd use on a real account. The commands are:

- **Parametrized** - set `PRODUCT` and `ENV` (your `CDK_PRODUCT` /
  `CDK_ENVIRONMENT`), `REGION`, and - where a command builds an ARN -
  `ACCOUNT` once at the top; names built by `shared/naming.py` become
  `${PRODUCT}-${ENV}-...`, so the same block works for `dev`, `stg`, or
  `prd`.
- **Looked up through the stack when a resource has no name of its own** (a
  VPC, a subnet, a KMS key, ...): `pid <LogicalId>` asks CloudFormation for
  the physical id of the stack resource with that logical id, which is the
  same in every environment. EC2 resources are never filtered by tag: floci
  doesn't keep EC2 tags, so a tag filter finds nothing there.
- **Generated, not hand-written** - from the stack's template, by
  [`scripts/resource_commands.py`](scripts/resource_commands.py), between
  `<!-- BEGIN resource-commands -->` / `<!-- END resource-commands -->`
  markers. To (re)generate one after changing a stack:

  ```bash
  uv run cdk synth VpcStack -o cdk.out
  uv run python scripts/resource_commands.py --markdown VpcStack --template cdk.out/VpcStack.template.json
  ```

  and paste the output between the markers (CLAUDE.md, section 3, point 6).

`make cdk-resources STACK=VpcStack` (or `STACK=all`, or `EXAMPLE=enterprise
ENV=prd`) runs the very same commands against what's deployed and reports
which ones found their resource - a read-only shortcut, safe to repeat; the
README commands remain the reference. Checked while writing this: across
every module and all enterprise cells, every command found its resource
except the floci gaps listed in [section 10](#10-observations-and-limitations),
which `make cdk-resources` marks with `~~`.

### 5.11 - Previewing changes with `cdk diff`

`cdk diff` answers "what would `cdk deploy` change?" without changing
anything. It synthesizes your app, compares each stack's template with the
one CloudFormation has deployed, and prints the differences
([`cdk diff` reference](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-diff.html)):

```bash
uv run cdk diff SqsStack     # one stack
uv run cdk diff              # every stack in the app
```

| Symbol | Meaning |
|---|---|
| `[+]` | added if you deploy |
| `[-]` | removed if you deploy |
| `[~]` | modified - for some properties an in-place update, for others (e.g. a name) a full replacement |

`There were no differences` means a deploy would do nothing - which is also
why `cdk deploy --method=direct` skips an unchanged stack (section 5.8).
Two details worth knowing:

- **It needs the deployed stack to compare with** - for floci, floci must be
  running and your `.env` loaded; a never-deployed stack shows every
  resource as `[+]`.
- **How it computes the diff** (`--method`): by default (`auto`) the CDK
  creates a read-only CloudFormation change set to report replacements
  accurately, and falls back to comparing templates if it can't. floci
  can't create that read-only change set, so on floci you'll see "Could
  not create a change set, will base the diff on template differences" -
  harmless (checked while writing this: nothing is created or changed).
  `--method=template` skips the attempt. `--fail` exits with code 1 when
  there are differences (useful in CI).

`make cdk-diff STACK=SqsStack` (or `EXAMPLE=enterprise ENV=stg`) is the
shortcut (section 5.6).

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
| `environment` | `dev`, `stg`, or `prd` | short names only - `dev` (development), `stg` (staging), `prd` (production); any other value (including `staging`/`prod`) is rejected by [`shared/config.py`](shared/config.py) with a hint. The same short name is the environment segment of every resource name - see [section 8](#8-naming-policy) |
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
separator, e.g. `learning-cdk-python-dev-orders-queue`. The environment
segment (`dev` above) is always one of the three short names `dev`, `stg`,
`prd` - the same value as the `environment` tag (see
[section 7](#7-tagging-policy)) - which also keeps names short for resource
types with tight length limits. `_` is used only
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
- **CDK custom resources need two floci settings.** Several modules deploy
  CDK-managed Lambda functions behind the scenes - custom resources such as
  S3 `auto_delete_objects` (modules 12, 25, 32), EventBridge's log-group
  policy (28), OpenSearch's access policy (23), and EKS's cluster provider
  (16). [`docker-compose.yml`](docker-compose.yml) sets both settings
  floci's own Compose file uses:
  - `FLOCI_HOSTNAME: floci` - floci injects `AWS_ENDPOINT_URL=http://floci:4566`
    into every Lambda container, so the handler's AWS API calls reach floci
    ([floci - Lambda](https://floci.io/floci/services/lambda/), "Docker
    Compose service names").
  - `FLOCI_TLS_ENABLED: "true"` - the handler then reports its result to
    CloudFormation's `ResponseURL`, but the CDK's handler code always uses
    `https://` and drops the URL's port, so it connects to port 443. With
    TLS on, floci also listens on 443 and the containers it starts trust
    its certificate ([floci - TLS / HTTPS](https://floci.io/floci/configuration/tls/)).
    Plain `http://localhost:4566` keeps working.

  Without them, those deploys fail with `connect ECONNREFUSED <floci-ip>:443`.
- **Secrets Manager references are written by secret name.** floci
  resolves a `{{resolve:secretsmanager:...}}` dynamic reference only when it
  is a plain string in the template - not the `Fn::Join` + `Ref` form the
  CDK builds from a `Secret` object (floci fails with "Invalid Secrets
  Manager dynamic reference"). The database modules (18, 19, 20, 45)
  therefore create their master-password secret with a fixed name and pass
  `SecretValue.secrets_manager(<name>, json_field="password")`, which works
  identically on real AWS.
- **floci's `cdk destroy` leaves VPCs behind** - see
  [section 5.9](#59---cdk-destroy-on-floci-leaves-vpcs-behind).
- **Some resources are recorded, not created, by floci's CloudFormation.**
  floci 2.1.0 (the current `floci/floci:latest` image, checked while writing
  this) reports these types as `CREATE_COMPLETE` but logs each as
  unsupported and creates nothing, so the AWS CLI finds nothing:
  `AWS::ApplicationAutoScaling::ScalableTarget`/`ScalingPolicy` (enterprise
  `stg`/`prd`), `AWS::Athena::WorkGroup` (25), `AWS::Backup::BackupPlan`
  (41), `AWS::CE::AnomalyMonitor`/`AnomalySubscription` (42),
  `AWS::DocDB::*` (45), `AWS::EC2::TransitGateway*` (06),
  `AWS::EC2::VPCPeeringConnection` (07), `AWS::ElastiCache::*` (22),
  `AWS::GuardDuty::Detector` (38), `AWS::MSK::Cluster` (46),
  `AWS::OpenSearchService::Domain` (23), `AWS::ResourceGroups::Group` (43 -
  floci implements no Resource Groups API at all), `AWS::Route53::RecordSet`
  (33), and `AWS::SES::EmailIdentity` (36). Each module's generated
  resource-listing section says which of its resources this affects. Also:
  S3 buckets are created without their `AWS::S3::BucketPolicy` and
  `PublicAccessBlockConfiguration` (12, 32), EC2 resources don't keep their
  tags, and `aws logs describe-metric-filters` isn't implemented (39).
  floci's unreleased main branch already provisions several of these -
  re-check with each new floci release. Everything else in this repository
  (353 resources across every module and enterprise cell, at the time of
  writing) is created for real.
- **Deploying to a real AWS account has real cost** for some modules (NAT
  Gateway, RDS, OpenSearch, EKS, ElastiCache, in particular - hourly
  charges start the moment the resource exists). Each such module's README
  has a "Notes and cautions" section calling this out explicitly before its
  optional "Deploy to real AWS" instructions.

## 11. Building, rendering and exporting the slide decks (Marp)

[`docs/slides/SLIDES-en-US.md`](docs/slides/SLIDES-en-US.md) and
[`docs/slides/SLIDES-pt-BR.md`](docs/slides/SLIDES-pt-BR.md) are
[Marp](https://marp.app) decks (plain Markdown with a `marp: true` front
matter and a `---`-separated slide, plus a self-contained custom CSS
theme) covering this repository's tooling - AWS CDK v2, uv, and floci
(with its `floci-ui`/`floci-dash` consoles) in particular - and how to run
the hands-on lab. They can be edited as plain text, but rendering them to
HTML/PDF/PPTX or previewing them with full styling needs the Marp
toolchain below.

### 11.1 - Installing Marp CLI

No install is required for one-off use - `npx` downloads and runs it on
demand:

```bash
npx @marp-team/marp-cli@latest --version
```

For repeated use, install it globally instead:

```bash
npm install -g @marp-team/marp-cli
marp --version
```

Rendering to PDF or PPTX drives a headless Chromium under the hood (via
Puppeteer). Marp CLI downloads/uses a bundled Chromium automatically on
first run in most environments; on a minimal Linux server you may
additionally need the system libraries Chromium depends on (fonts,
`libnss3`, `libatk*`, etc. - see the Puppeteer troubleshooting reference
below) if the export fails with a browser-launch error.

### 11.2 - Rendering and exporting `docs/slides/SLIDES-*.md`

Both decks embed the official floci/AWS CDK logos and the two screenshots
captured from this repository's own running floci stack (see
[section 5](#5-running-floci-the-local-aws-emulator)) as inline
`data:image/...;base64,...` URIs directly in the Markdown - **not** as
`<img src="../images/tools/...">` links to the source PNG/SVG files under
[`docs/images/tools/`](docs/images/tools/) (those files still exist in the
repo as the maintained originals the data URIs were generated from, and as
standalone assets other docs can link to). This is deliberate: an earlier
version of this deck referenced them by relative path, which broke in two
different ways depending on export format -

- **HTML export** never embeds referenced images at all (only the theme's
  CSS is inlined) - a browser resolves a `src` **relative to the exported
  `.html` file's own location**, not the source `.md`'s, so exporting
  anywhere other than the file's own directory (the repository root, a
  Desktop folder, ...) broke every image.
- **PDF/PPTX/PNG export** additionally needs `--allow-local-files`
  (Chromium blocks local file reads by default) - without it, every image
  silently renders missing even though the command "succeeds".

Data URIs sidestep both failure modes - the image bytes travel with the
Markdown itself, so every export format works from **any** output
directory with no extra flag beyond the PDF/PPTX/PNG ones below (which are
about Chromium's local-file sandbox at conversion time, unrelated to
images). The tradeoff is size: both `.md` source files are ~1.5 MB instead
of ~50 KB. If you regenerate a screenshot or logo, re-run the same
base64-encoding step against the new file under `docs/images/tools/` and
replace the matching `data:...;base64,...` value.

```bash
# HTML - works from any output directory, e.g. straight to your Desktop
npx @marp-team/marp-cli@latest docs/slides/SLIDES-en-US.md -o ~/Desktop/slides-en.html
npx @marp-team/marp-cli@latest docs/slides/SLIDES-pt-BR.md -o ~/Desktop/slides-pt.html

# PDF (one page per slide) - --allow-local-files is still required (see above)
npx @marp-team/marp-cli@latest docs/slides/SLIDES-en-US.md --pdf --allow-local-files -o ~/Desktop/slides-en.pdf

# PowerPoint (.pptx, editable in PowerPoint/Keynote/Google Slides)
npx @marp-team/marp-cli@latest docs/slides/SLIDES-en-US.md --pptx --allow-local-files -o ~/Desktop/slides-en.pptx

# One PNG image per slide (useful for a quick visual review)
npx @marp-team/marp-cli@latest docs/slides/SLIDES-en-US.md --images png --allow-local-files -o ~/Desktop/slide.png

# Watch mode: re-render on every save while editing
npx @marp-team/marp-cli@latest -w docs/slides/SLIDES-en-US.md -o docs/slides/slides-en.html
```

Verify any export before trusting it: open the HTML file (or PDF/PPTX) and
confirm the AWS CDK/floci logos on the first slide actually render - the
fastest way to catch a broken-path regression.

Exported files are build artifacts - don't commit them; add any output
filename pattern you use locally to your own git excludes if needed.

### 11.3 - Enabling HTML in a live preview (VS Code / marp.app)

Both slide decks rely on inline HTML (`<div class="card">…</div>`, etc.)
and CSS classes defined in their own front matter for the card grids,
step diagrams, and stat callouts - this is standard Marp usage, but
several Marp viewers disable raw HTML **by default** as an XSS precaution
for untrusted files, which makes the deck render as plain, unstyled text
(the cards/steps collapse to bare paragraphs). Marp CLI (section 11.2)
already renders HTML by default, so exported HTML/PDF/PPTX files are
unaffected - this only matters for **live preview**:

- **VS Code, "Marp for VS Code" extension:** open Settings and enable
  `markdown.marp.html` (or add `"markdown.marp.html": true` to
  `settings.json`), then reopen the preview.
- **[marp.app](https://marp.app) (web editor):** use the editor's
  settings/gear menu to enable HTML rendering for the deck before
  previewing.

## 12. References

- [floci - Local AWS Emulator](https://floci.io) · [github.com/floci-io/floci](https://github.com/floci-io/floci) · [github.com/floci-io/floci-cli](https://github.com/floci-io/floci-cli) · [github.com/floci-io/floci-ui](https://github.com/floci-io/floci-ui)
- [Marp CLI](https://github.com/marp-team/marp-cli) · [Marp for VS Code](https://marketplace.visualstudio.com/items?itemName=marp-team.marp-vscode) · [marp.app](https://marp.app) · [Marpit - `html` and other Markdown directives](https://marpit.marp.app/directives)
- [Puppeteer - Troubleshooting (headless Chromium system dependencies on Linux)](https://pptr.dev/troubleshooting)
- [uv - Getting started](https://docs.astral.sh/uv/getting-started/installation/)
- [mise - Getting started](https://mise.jdx.dev/getting-started.html) · [mise - Installing mise](https://mise.jdx.dev/installing-mise.html) · [mise - Registry](https://mise.jdx.dev/registry.html) (the `aws-cli` tool) · [aws/aws-cli releases](https://github.com/aws/aws-cli) · [Node.js releases](https://nodejs.org/en/about/previous-releases) · [npm/cli](https://github.com/npm/cli)
- [AWS CDK v2 Developer Guide - Working with the AWS CDK in Python](https://docs.aws.amazon.com/cdk/v2/guide/work-with-cdk-python.html)
- [AWS CDK v2 Developer Guide - Environments](https://docs.aws.amazon.com/cdk/v2/guide/environments.html)
- [AWS CDK CLI reference - `cdk deploy` (`--method`)](https://docs.aws.amazon.com/cdk/v2/guide/ref-cli-cmd-deploy.html)
- [AWS CDK v2 Developer Guide - AWS CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) · [Troubleshooting common AWS CDK issues](https://docs.aws.amazon.com/cdk/v2/guide/troubleshooting.html)
- [AWS CDK v2 Developer Guide (home)](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- [AWS CDK API Reference (Python)](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [aws/aws-cdk on GitHub](https://github.com/aws/aws-cdk) - the AWS CDK's source code, issues, and release notes
- Community tutorials and articles (not official AWS documentation - helpful
  for a second explanation, but check details against the official guides
  above):
  [AWS CDK and Python - Step by Step Tutorial (Be A Better Dev)](https://beabetterdev.com/2022/06/24/aws-cdk-and-python-step-by-step-tutorial/) ·
  [AWS CDK tutorial (DataCamp)](https://www.datacamp.com/tutorial/aws-cdk) ·
  [AWS CDK tutorial, in Portuguese (DataCamp)](https://www.datacamp.com/pt/tutorial/aws-cdk) ·
  [Getting started with CDK and Python (Medium)](https://medium.com/@ihona.correadecabo/getting-started-with-cdk-and-python-aef821265e2b) ·
  [Getting started with Python based IaC using AWS CDK (DEV Community)](https://dev.to/aws-builders/getting-started-with-python-based-iac-using-aws-cdk-152h) ·
  [My journey to master AWS CDK (Towards AWS)](https://towardsaws.com/my-journey-to-master-aws-cdk-d8b9b230fa9e) ·
  [Lessons in AWS Python CDK: 3 - Sometimes You Just Need to Learn to Read Typescript (DEV Community)](https://dev.to/aws-builders/lessons-in-aws-python-cdk-3-sometimes-you-just-need-to-learn-to-read-typescript-597c) ·
  [Using uv with the Python AWS CDK (Manny Savage)](https://savage.cx/kbase/2024-12-01-uv-aws-cdk/)
- [`aws-cdk-lib` on PyPI](https://pypi.org/project/aws-cdk-lib/) · [`constructs` on PyPI](https://pypi.org/project/constructs/)
- [Docker Engine - Install on Ubuntu](https://docs.docker.com/engine/install/ubuntu/) · [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/) · [Colima](https://github.com/abiosoft/colima) (macOS/Linux Docker Desktop alternative)
- [AWS CLI v2 - Install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [GNU Make Manual](https://www.gnu.org/software/make/manual/make.html)
