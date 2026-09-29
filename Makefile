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

.PHONY: help check

help: ## Show this list of targets
	@echo "Targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "  %-8s %s\n", $$1, $$2}'

check: ## Check your OS + every required/recommended/optional tool (see REQUIREMENTS.md section 3)
	@bash scripts/check-deps.sh
