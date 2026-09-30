# Makefile for learning-cdk-python.
#
# This repository is otherwise run directly with `uv run ...` and
# `docker compose ...` (see CONTRIBUTING.md and REQUIREMENTS.md) - the one
# thing this Makefile automates is the "is my machine even set up for this?"
# check, so a beginner gets one clear error message pointing at
# REQUIREMENTS.md instead of a confusing failure three steps later.
#
# See REQUIREMENTS.md, "Running and reading `make check`", for how to run
# this and how to read its output.

SHELL := /bin/bash

.DEFAULT_GOAL := help

.PHONY: help check typecheck

help: ## Show this list of targets
	@echo "Targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  %-10s %s\n", $$1, $$2}'

check: ## Check your OS + every required/recommended/optional tool (see REQUIREMENTS.md section 3)
	@bash scripts/check-deps.sh

# Module directories start with a digit (01_iam, 03_vpc, ...), which is not a
# valid Python package name, so a single `mypy modules` refuses to run.
# Instead, each modules/NN_service/stack.py is checked on its own, with its
# directory as the package base (MYPYPATH + --explicit-package-bases).
typecheck: ## Type-check shared/, app.py, every module's stack.py, and examples/ with mypy
	@uv run mypy shared app.py
	@uv run mypy --explicit-package-bases examples/enterprise_stack
	@set -e; for dir in modules/*/; do \
		[ -f "$${dir}stack.py" ] || continue; \
		echo "mypy $${dir}stack.py"; \
		MYPYPATH="$$dir" uv run mypy --explicit-package-bases --no-error-summary "$${dir}stack.py"; \
	done
