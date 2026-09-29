<!-- TOC -->

- [floci stack — personal setup tutorial (macOS)](#floci-stack--personal-setup-tutorial-macos)
  - [1. What this is](#1-what-this-is)
  - [2. Prerequisites](#2-prerequisites)
  - [3. Install](#3-install)
  - [4. Start](#4-start)
  - [5. Default ports](#5-default-ports)
  - [6. Point your terminal at floci](#6-point-your-terminal-at-floci)
    - [6.1 - Set environment variables](#61---set-environment-variables)
    - [6.2 - Unset environment variables](#62---unset-environment-variables)
  - [7. Stop](#7-stop)
  - [8. Update](#8-update)
  - [9. Examples](#9-examples)
    - [9.1 - S3: create a bucket, upload and download a file](#91---s3-create-a-bucket-upload-and-download-a-file)
    - [9.2 - ECS: register a task definition, create a cluster, run a task](#92---ecs-register-a-task-definition-create-a-cluster-run-a-task)
  - [10. Notes and cautions](#10-notes-and-cautions)
  - [References](#references)

<!-- TOC -->

# floci stack — personal setup tutorial (macOS)

This is a personal, macOS-oriented tutorial for running the
[floci-ui](https://github.com/floci-io/floci-ui) stack - the standalone
frontend + API project for [floci](https://floci.io), the free/open-source
local AWS emulator - via [Colima](https://github.com/abiosoft/colima)
instead of Docker Desktop. It's kept under `OLD/` as a legacy/personal
reference, separate from this repository's own `docker-compose.yml`
(documented in [`../REQUIREMENTS.md`](../REQUIREMENTS.md) section 5) -
that file runs `floci` on its own with a built-in console; this tutorial
instead clones and runs the full standalone `floci-ui` project (its own
frontend on port 4500 and API on port 4501, in front of `floci` itself on
4566), which is a richer but heavier alternative covered in
[`../REQUIREMENTS.md` section 5.4](../REQUIREMENTS.md#54---optional-the-standalone-floci-ui-project-built-from-source).

## 1. What this is

- **floci** emulates the AWS API on your own machine (`http://localhost:4566`)
  - no AWS account, no cost, no risk to a real account.
- **floci-ui** is a separate, open-source project (its own frontend + API)
  that gives floci a full web console, built from source via its own
  `docker-compose.yml`.
- **Colima** is a free, open-source container runtime for macOS/Linux that
  provides a Docker-API-compatible daemon - an alternative to Docker
  Desktop, driven by the same `docker`/`docker-compose` CLI commands.

## 2. Prerequisites

- macOS with [Homebrew](https://brew.sh) installed.
- `git`, to clone `floci-ui`.
- The [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
  (`aws`), to exercise the examples in [section 9](#9-examples) - it talks
  to floci the same way it would talk to real AWS, once pointed at the
  right endpoint (see [section 6](#6-point-your-terminal-at-floci)).

## 3. Install

Run the following commands to install floci-ui and its dependencies:

```bash
brew install docker colima docker-compose

export MY_DIR="/Users/aecio/OLD"
mkdir "$MY_DIR"
cd "$MY_DIR"
git clone https://github.com/floci-io/floci-ui.git
```

`MY_DIR` is just this tutorial's convention for "where my floci-ui checkout
lives" - adjust it to wherever you keep local projects, and keep using the
same value in every command below.

> **Note:** Homebrew's `docker-compose` formula installs the standalone
> `docker-compose` binary (used with a hyphen, as every command below
> does), not the `docker compose` v2 CLI plugin. If you'd rather use
> `docker compose` (no hyphen), see
> [`../REQUIREMENTS.md` section 3.2](../REQUIREMENTS.md#32---install-on-macos-arm64-and-amd64)
> for how to register it as a plugin.

## 4. Start

Run the following commands to start floci-ui and the floci CLI/API stack
via Docker Compose:

```bash
colima start
colima status
cp "$MY_DIR/docker-compose.yml" "$MY_DIR/floci-ui" 
cd "$MY_DIR/floci-ui"
docker-compose up --build -d
```

## 5. Default ports

- floci-ui on <http://localhost:4500>
- floci-api on <http://localhost:4501>
- floci on <http://localhost:4566>

## 6. Point your terminal at floci

The AWS CLI (and any AWS SDK) reads `AWS_ENDPOINT_URL` to redirect every
API call to floci instead of real AWS - set these once per terminal
session before running any `aws` command against floci, and unset them
before running an `aws` command against a real account.

### 6.1 - Set environment variables

```bash
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
```

### 6.2 - Unset environment variables

```bash
unset AWS_ENDPOINT_URL
unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_DEFAULT_REGION
```

## 7. Stop

```bash
cd "$MY_DIR/floci-ui"
docker-compose down
```

## 8. Update

```bash
cd "$MY_DIR/floci-ui"
git pull
cp "$MY_DIR/docker-compose.yml" "$MY_DIR/floci-ui"
```

> **[ATTENTION]** Verify whether `floci-ui`'s own `docker-compose.yml`
> changed upstream before overwriting it with the backup copy above - a
> newer upstream file may have picked up fixes or new options that the
> backed-up copy doesn't have.

## 9. Examples

A couple of quick, hands-on examples of creating resources against floci
once it's running and your terminal is pointed at it (section 6.1).

### 9.1 - S3: create a bucket, upload and download a file

```bash
# Creating a S3 bucket and making a uploading file
aws s3 mb s3://my-bucket

echo "Why pay for S3 when floci is free? 🎉" \
  > hello-floci.txt

aws s3 cp hello-floci.txt \
  s3://my-bucket/hello-floci.txt

aws s3 cp s3://my-bucket/hello-floci.txt \
  hello-back.txt

cat hello-back.txt
```

### 9.2 - ECS: register a task definition, create a cluster, run a task

```bash
# Register task definition and create cluster
aws ecs register-task-definition \
    --family web-task --network-mode bridge \
    --container-definitions '[{"name":"web","image":"nginx:alpine","portMappings":[{"containerPort":80,"hostPort":8081}],"memory":128,"cpu":64}]'

aws ecs create-cluster --cluster-name dev-cluster

# Run a task (floci launches a real Docker container for it)
aws ecs run-task \
    --cluster dev-cluster \
    --task-definition web-task \
    --count 1

# List tasks
aws ecs list-tasks
```

## 10. Notes and cautions

- ECS is one of the services floci backs with a **real Docker container**
  rather than a lightweight mock - `aws ecs run-task` above actually
  starts an `nginx:alpine` container on your machine, reachable at
  `http://localhost:8081` (the `hostPort` in the task definition).
- Re-check [floci.io](https://floci.io) for the current list of
  Docker-backed vs. mocked services - this can change between floci
  releases.

## References

- [floci - Local AWS Emulator](https://floci.io)
- [floci-ui on GitHub](https://github.com/floci-io/floci-ui)
- [Colima on GitHub](https://github.com/abiosoft/colima)
- [AWS CLI - Install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AWS CLI / SDK - `AWS_ENDPOINT_URL` environment variable](https://docs.aws.amazon.com/sdkref/latest/guide/feature-ss-endpoints.html)
- [Amazon ECS - `register-task-definition`](https://docs.aws.amazon.com/cli/latest/reference/ecs/register-task-definition.html) · [`create-cluster`](https://docs.aws.amazon.com/cli/latest/reference/ecs/create-cluster.html) · [`run-task`](https://docs.aws.amazon.com/cli/latest/reference/ecs/run-task.html) · [`list-tasks`](https://docs.aws.amazon.com/cli/latest/reference/ecs/list-tasks.html)
- This repository's own floci setup (a different, simpler path - no floci-ui clone needed): [`../REQUIREMENTS.md` section 5](../REQUIREMENTS.md#5-running-floci-the-local-aws-emulator)
