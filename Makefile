# Makefile for learning-cdk-python.
#
# Every target here is a *shortcut* for commands documented step by step
# elsewhere (REQUIREMENTS.md, CONTRIBUTING.md, docs/TESTING.md, and every
# module's README). Learn the long form first - `uv run cdk synth VpcStack`,
# `docker compose up -d floci`, ... - then use these once you know what
# they run. `make` (or `make help`) lists every target.
#
# See REQUIREMENTS.md, section 3.4, for how to run `make check` and read
# its output, and section 5.6 for the floci-* and cdk-* targets.

SHELL := /bin/bash

.DEFAULT_GOAL := help

# --- Variables (override on the command line, e.g. `make cdk-synth STACK=VpcStack`) ---

# A module's stack id (see docs/LEARNING-PATH.md, or `uv run cdk list`).
# cdk-synth: empty = every stack. cdk-deploy: required ("all" = every stack).
STACK ?=
# EXAMPLE=enterprise targets examples/enterprise_stack/ instead of modules/.
EXAMPLE ?=
# The enterprise example's environment: dev, stg, or prd.
ENV ?= dev
# SKIP_COVERAGE_CHECK=1 makes `make coverage` report coverage without
# failing below the 80% minimum - for work in progress only; the default
# (and what a finished change must pass) is to enforce it.
SKIP_COVERAGE_CHECK ?=
# Optional consoles to start with floci: floci-ui, floci-dash, or both
# ("floci-ui floci-dash") - see REQUIREMENTS.md sections 5.4 and 5.5.
UI ?=
# Variables loaded before every cdk-* command: your .env if it exists,
# otherwise .env.example (which already points at floci).
ENV_FILE ?= $(if $(wildcard .env),.env,.env.example)

COMPOSE := docker compose
ALL_PROFILES := --profile floci-ui --profile floci-dash
UI_PROFILES := $(foreach p,$(UI),--profile $(p))
FLOCI_CONTAINER := learning-cdk-python-floci
FLOCI_IMAGE := floci/floci:latest

ifeq ($(EXAMPLE),enterprise)
  CDK_APP := --app "uv run python examples/enterprise_stack/app.py"
  CDK_ENV := ENTERPRISE_ENVIRONMENT=$(ENV)
  # The regions an environment file pins its cells to (prd.json: two), so
  # floci-prune and cdk-resources check each one.
  ENV_REGIONS := $(shell python3 -c "import json; f='examples/enterprise_stack/environments/$(ENV).json'; print(*sorted({c['region'] for c in json.load(open(f))['cells'] if c.get('region')}))" 2>/dev/null)
  # An environment file that pins its cells to an explicit account (prd.json
  # does) is deployed to floci *as* that account: floci treats a 12-digit
  # access key id as the account id (examples/enterprise_stack/README.md,
  # section 9). Read from the JSON file, so it's never repeated here.
  ENV_ACCOUNT := $(shell python3 -c "import json,sys; f='examples/enterprise_stack/environments/$(ENV).json'; a={c['account'] for c in json.load(open(f))['cells'] if c.get('account')}; print(*a) if len(a)==1 else None" 2>/dev/null)
  # This environment's cells are the stacks named Enterprise<Env>... (app.py).
  ENV_STACK_PREFIX := Enterprise$(shell echo '$(ENV)' | sed 's/^./\U&/')
else ifeq ($(EXAMPLE),)
  CDK_APP :=
  CDK_ENV :=
else
  $(error Unknown EXAMPLE='$(EXAMPLE)' - the only example is EXAMPLE=enterprise)
endif

# `set -a; source <file>; set +a` exports every variable in ENV_FILE - the
# same command REQUIREMENTS.md section 0, step 6 runs by hand.
LOAD_ENV := set -a; source $(ENV_FILE); set +a; $(if $(ENV_ACCOUNT),export AWS_ACCESS_KEY_ID=$(ENV_ACCOUNT);)

.PHONY: help check typecheck coverage cdk-synth cdk-diff cdk-deploy cdk-destroy cdk-resources \
	floci-start floci-stop floci-status floci-destroy floci-prune

help: ## Show this list of targets
	@echo "Targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  %-14s %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make cdk-synth STACK=VpcStack           make cdk-deploy STACK=SqsStack"
	@echo "  make cdk-synth EXAMPLE=enterprise ENV=stg   make floci-start UI=floci-dash"

check: ## Check your OS + every required/recommended/optional tool (see REQUIREMENTS.md section 3)
	@bash scripts/check-deps.sh

# Module directories start with a digit (01_iam, 03_vpc, ...), which is not a
# valid Python package name, so a single `mypy modules` refuses to run.
# Instead, each modules/NN_service/stack.py is checked on its own, with its
# directory as the package base (MYPYPATH + --explicit-package-bases).
typecheck: ## Type-check shared/, app.py, every module's stack.py, and examples/ with mypy
	@uv run mypy shared app.py
	@uv run mypy --explicit-package-bases examples/enterprise_stack
	@uv run mypy scripts/floci_prune.py scripts/resource_commands.py
	@set -e; for dir in modules/*/; do \
		[ -f "$${dir}stack.py" ] || continue; \
		echo "mypy $${dir}stack.py"; \
		MYPYPATH="$$dir" uv run mypy --explicit-package-bases --no-error-summary "$${dir}stack.py"; \
	done

# Runs both test suites (the repository's tests/ and the enterprise
# example's own tests/) in one go, so the report covers everything. The
# settings - branch coverage, the 80% minimum - live in pyproject.toml's
# [tool.coverage.*] sections. See docs/TESTING.md, "Test coverage".
coverage: ## Run every test with a coverage report (fails below 80%; SKIP_COVERAGE_CHECK=1 to only report; HTML in htmlcov/)
	@if [ -n "$(SKIP_COVERAGE_CHECK)" ]; then \
		echo "SKIP_COVERAGE_CHECK is set: reporting coverage without enforcing the 80% minimum."; \
	fi
	uv run pytest tests examples/enterprise_stack/tests --cov --cov-report=term-missing --cov-report=html \
		$(if $(SKIP_COVERAGE_CHECK),--cov-fail-under=0)

# --- floci (the local AWS emulator) -------------------------------------------

floci-status: ## Show whether floci (and any console) is running, and its URLs
	@state="$$(docker inspect -f '{{.State.Status}}{{if and .State.Running .State.Health}} ({{.State.Health.Status}}){{end}}' $(FLOCI_CONTAINER) 2>/dev/null || echo 'not created')"; \
	echo "floci: $$state"
	@$(COMPOSE) $(ALL_PROFILES) ps --format '{{.Service}}: {{.Status}}' 2>/dev/null | grep -vE '^floci:' | sed 's/^/  /' || true
	@echo "  API:              http://localhost:4566"
	@echo "  Built-in console: http://localhost:4566/_floci/ui"
	@echo "  floci-ui:         http://localhost:4500   (only with UI=floci-ui)"
	@echo "  floci-dash:       http://localhost:9877   (only with UI=floci-dash)"

floci-start: ## Start floci and wait until it's healthy (add UI=floci-ui and/or UI=floci-dash for a console)
	@if [ "$$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' $(FLOCI_CONTAINER) 2>/dev/null)" = "healthy" ] && [ -z "$(UI)" ]; then \
		echo "floci is already running and healthy."; \
	else \
		$(COMPOSE) $(UI_PROFILES) up -d floci $(UI) && \
		echo -n "Waiting for floci to be healthy" && \
		for i in $$(seq 1 60); do \
			[ "$$(docker inspect -f '{{.State.Health.Status}}' $(FLOCI_CONTAINER) 2>/dev/null)" = "healthy" ] && { echo " - ready."; exit 0; }; \
			echo -n "."; sleep 2; \
		done; \
		echo ""; echo "floci did not become healthy in 120s - see: docker compose logs floci" >&2; exit 1; \
	fi

floci-stop: ## Stop floci and any console, keeping their containers and data
	$(COMPOSE) $(ALL_PROFILES) stop

# floci runs in "persistent" mode (docker-compose.yml), keeping everything
# you deployed in ./.floci/data. After this target, run `uv run cdk
# bootstrap` again before the next deploy (REQUIREMENTS.md section 5.7).
# Those files are created by the container as root, so they're deleted from inside a throwaway floci container (with
# this folder mounted at /repo) rather than with a plain `rm`, which would
# need sudo.
floci-destroy: ## Remove floci, its consoles, and ALL deployed local resources (asks first; CONFIRM=yes skips)
	@if [ "$(CONFIRM)" != "yes" ]; then \
		read -r -p "Delete floci's containers and every resource deployed to it (./.floci/data)? Type 'yes': " answer; \
		[ "$$answer" = "yes" ] || { echo "Cancelled."; exit 1; }; \
	fi
	@# Stop floci first, so it can't start new containers while the ones it
	@# already started are being removed below.
	$(COMPOSE) $(ALL_PROFILES) stop
	@# Containers floci itself started for deployed resources (Lambda, ECS,
	@# EKS, EC2, ElastiCache, the ECR registry, ...) aren't Compose services,
	@# so `down` would leave them behind (and couldn't remove the network they're
	@# attached to) - floci labels every one with floci=true.
	@ids="$$(docker ps -aq --filter label=floci=true)"; \
	if [ -n "$$ids" ]; then docker rm -f $$ids >/dev/null && echo "Removed $$(echo $$ids | wc -w) container(s) floci had started."; fi
	$(COMPOSE) $(ALL_PROFILES) down --remove-orphans
	@if [ -d .floci ]; then \
		docker run --rm --entrypoint bash -v "$(CURDIR):/repo" $(FLOCI_IMAGE) -c 'rm -rf /repo/.floci' && \
		echo "Deleted ./.floci (all local floci data)."; \
	fi

# Runs the same `aws` commands each README's "List every resource with the
# AWS CLI" section shows, against the deployed stack(s) - read-only, so it
# is safe to repeat. A shortcut, not a replacement for those commands; see
# REQUIREMENTS.md section 5.10.
cdk-resources: ## List every resource a deployed stack created, via the AWS CLI (STACK=VpcStack, STACK=all, or EXAMPLE=enterprise ENV=...); read-only
	@if [ -z "$(EXAMPLE)" ] && [ -z "$(STACK)" ]; then \
		echo "Pick what to list: make cdk-resources STACK=VpcStack, STACK=all, or EXAMPLE=enterprise ENV=dev|stg|prd." >&2; exit 1; \
	fi
	@$(MAKE) --no-print-directory floci-status
	@$(MAKE) --no-print-directory floci-start
	$(LOAD_ENV) $(CDK_ENV) uv run python scripts/resource_commands.py $(if $(EXAMPLE),--all --prefix $(ENV_STACK_PREFIX) $(foreach r,$(ENV_REGIONS),--region $(r)),$(if $(filter-out all,$(STACK)),$(STACK),--all))

# floci's CloudFormation never deletes AWS::EC2::VPC resources on stack
# deletion, so every `cdk destroy` of a stack with a VPC leaves an empty VPC
# behind - see REQUIREMENTS.md section 5.9. This lists (or, with APPLY=yes,
# deletes) VPCs no stack owns. It refuses to run against real AWS.
floci-prune: ## List VPCs floci left behind after cdk destroy; APPLY=yes deletes them (floci only)
	$(LOAD_ENV) uv run python scripts/floci_prune.py $(foreach r,$(ENV_REGIONS),--region $(r)) $(if $(filter yes,$(APPLY)),--apply)

# --- CDK shortcuts -------------------------------------------------------------

# Both run `floci-status` then `floci-start` first, so floci is always up
# (context lookups and every deploy talk to it). cdk-deploy uses
# --method=direct so re-running it on an unchanged stack is a no-op instead
# of duplicating resources on floci - see REQUIREMENTS.md section 5.8. The long form they replace
# is in every module's README - `uv run cdk synth <StackId>` etc.
cdk-synth: ## Synthesize one stack (STACK=VpcStack), every stack, or EXAMPLE=enterprise ENV=dev|stg|prd
	@$(MAKE) --no-print-directory floci-status
	@$(MAKE) --no-print-directory floci-start
	$(LOAD_ENV) $(CDK_ENV) uv run cdk synth $(CDK_APP) $(if $(STACK),$(STACK),--all --quiet)

# `cdk diff` compares what `cdk synth` would produce now with what's deployed,
# and changes nothing - see REQUIREMENTS.md section 5.11.
cdk-diff: ## Show what cdk deploy would change (STACK=VpcStack, every stack, or EXAMPLE=enterprise ENV=...); changes nothing
	@$(MAKE) --no-print-directory floci-status
	@$(MAKE) --no-print-directory floci-start
	$(LOAD_ENV) $(CDK_ENV) uv run cdk diff $(CDK_APP) $(if $(filter-out all,$(STACK)),$(STACK),--all)

cdk-deploy: ## Deploy to floci: STACK=VpcStack, STACK=all, or EXAMPLE=enterprise ENV=dev|stg|prd
	@if [ -z "$(EXAMPLE)" ] && [ -z "$(STACK)" ]; then \
		echo "Pick what to deploy: make cdk-deploy STACK=VpcStack (see 'uv run cdk list'), STACK=all, or EXAMPLE=enterprise." >&2; exit 1; \
	fi
	@$(LOAD_ENV) if [ -z "$${AWS_ENDPOINT_URL:-}" ]; then \
		echo "AWS_ENDPOINT_URL is not set in $(ENV_FILE) - cdk-deploy only targets floci. To deploy to real AWS, follow the module README's 'Deploy to real AWS' section instead." >&2; exit 1; \
	fi
	@$(MAKE) --no-print-directory floci-status
	@$(MAKE) --no-print-directory floci-start
	$(LOAD_ENV) $(CDK_ENV) uv run cdk bootstrap $(CDK_APP) --quiet
	$(LOAD_ENV) $(CDK_ENV) uv run cdk deploy $(CDK_APP) $(if $(filter-out all,$(STACK)),$(STACK),--all) --require-approval never --method=direct

cdk-destroy: ## Destroy from floci (STACK=VpcStack, STACK=all, or EXAMPLE=enterprise ENV=...), then delete the VPCs floci leaves
	@if [ -z "$(EXAMPLE)" ] && [ -z "$(STACK)" ]; then \
		echo "Pick what to destroy: make cdk-destroy STACK=VpcStack, STACK=all, or EXAMPLE=enterprise ENV=dev|stg|prd." >&2; exit 1; \
	fi
	@$(LOAD_ENV) if [ -z "$${AWS_ENDPOINT_URL:-}" ]; then \
		echo "AWS_ENDPOINT_URL is not set in $(ENV_FILE) - cdk-destroy only targets floci." >&2; exit 1; \
	fi
	$(LOAD_ENV) $(CDK_ENV) uv run cdk destroy $(CDK_APP) $(if $(filter-out all,$(STACK)),$(STACK),--all) --force
	@$(MAKE) --no-print-directory floci-prune APPLY=yes
