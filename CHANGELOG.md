<!-- TOC -->

- [Changelog](#changelog)
  - [\[0.1.0 \] - 2026-10-29](#010----2026-10-29)
    - [Added](#added)
    - [Fixed](#fixed)

<!-- TOC -->

# Changelog

All notable changes to this project are documented in this file. The format
loosely follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
written in English by convention.

## [0.1.0 ] - 2026-10-29

### Added

- Repository scaffold: `pyproject.toml` (uv-managed, `aws-cdk-lib==2.271.0`,
  `constructs`, `boto3`), `.python-version`, `cdk.json` (`"app": "uv run
  python app.py"`), `app.py` (dynamic module discovery - see
  `CLAUDE.md` section 3), `.gitignore`, `.env.example`.
- `docker-compose.yml`: a single `floci` service (the local AWS emulator),
  with the `floci-ui` browser console enabled at
  `http://localhost:4566/_floci/ui`.
- `shared/tagging.py`, `shared/naming.py`, `shared/config.py`: the shared
  tagging policy (7 mandatory tags), naming policy, and account/region/tag
  value resolution every module uses - see `REQUIREMENTS.md` sections 7-9.
- `REQUIREMENTS.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `docs/LEARNING-PATH.md`.
- The 44-module learning path (`modules/01_iam` through
  `modules/44_resource_quotas`), covering IAM, STS, VPC (subnets, security
  groups, route tables), Internet Gateway, NAT Gateway, Transit Gateway,
  VPC Peering, KMS, Secrets Manager, Parameter Store, ACM, S3, EC2, ECR,
  ECS, EKS, Lambda, RDS (MySQL, PostgreSQL, Aurora PostgreSQL), DynamoDB,
  ElastiCache, OpenSearch Service, Kinesis Data Streams, Athena, SQS, SNS,
  EventBridge, Step Functions, Application Load Balancer, Network Load
  Balancer, CloudFront, Route 53, API Gateway, Cognito, SES, WAF (WAFv2),
  GuardDuty, CloudWatch, CloudTrail, AWS Backup, Cost Explorer (cost
  anomaly detection), and Resource Groups & Tagging. `44_resource_quotas`
  (Service Quotas) is documentation- and `boto3`-only: the service has no
  CloudFormation/CDK resource - see that module's README.
- `aws-cdk-lambda-layer-kubectl-v36` added to `pyproject.toml`: the current
  stable `aws_cdk.aws_eks.Cluster` (module 16) requires an explicit
  `kubectl_layer`, no longer bundled by default in `aws-cdk-lib` - see
  `modules/16_eks/README.md`.
- `docs/TESTING.md`, `tests/conftest.py` (shared `config` fixture),
  `tests/_helpers.py` (`stack_class()`, `mandatory_tag_pairs()`), and one
  `tests/unit/test_NN_service.py` per module with a `stack.py` (43 files,
  199 tests total, `uv run pytest` runs in ~3s with no Docker/floci/AWS
  credentials) - `aws_cdk.assertions`-based unit tests, plus a matching
  "Tests" section in every module's `README.md` - see `CLAUDE.md` section
  3, point 7. `modules/44_resource_quotas` has no test file, on purpose -
  see that module's own "Tests" section.
- `docker-compose.yml`: two additional, independent, opt-in console
  profiles alongside the default `floci` service - `--profile floci-ui`
  (build-from-source, see `REQUIREMENTS.md` section 5.4) and
  `--profile floci-dash` (ready-made image from
  [floci-dash](https://github.com/ofsazib/floci-dash), a separate project
  from a different author - see `REQUIREMENTS.md` section 5.5); both can
  run together on their own ports (`4500`/`4501` and `9877`) alongside the
  built-in console (section 5.3), all pointed at the one `floci` service. A
  `healthcheck` was added to the `floci` service so the optional profiles
  can depend on it being actually ready, not just started.
- `REQUIREMENTS.md`: explicit Ubuntu 22.04/24.04/26.04 (`amd64`) and macOS
  (`arm64`/`amd64`) support table (section 1), and
  [Colima](https://github.com/abiosoft/colima) documented as a Docker
  Desktop alternative for macOS (section 3.2).
- `mise.toml` (pins Python 3.12, matching `.python-version`) and
  `REQUIREMENTS.md` section 3.3: [mise](https://mise.jdx.dev) documented,
  from zero, as a recommended (not required - `uv` can also manage Python
  on its own) way to install this repository's exact Python version,
  including Ubuntu and macOS install steps in sections 3.1/3.2.
- `docs/ARCHITECTURE.md`: four diagrams (Mermaid source in
  `docs/diagrams/*.mmd`, rendered `.svg` in `docs/images/`) - the CDK
  `synth`/`deploy`/`destroy` workflow against floci or a real AWS account,
  the `docker-compose.yml` floci/floci-ui/floci-dash console wiring, how
  `shared/config.py`/`tagging.py`/`naming.py` feed every module's
  `stack.py` and its unit test, and how `modules/03_vpc`'s own resources
  (VPC, Internet Gateway, subnets, route tables, security group) relate to
  each other. `CLAUDE.md` sections 2 and 7 document where diagram sources
  live and how to regenerate them with `@mermaid-js/mermaid-cli`.
- `Makefile` (`make check`, `make help`) and `scripts/check-deps.sh`:
  checks the OS/architecture against `REQUIREMENTS.md` section 1 and every
  tool in section 3 (required, recommended, and optional), printing an
  `[ OK ]`/`[WARN]`/`[FAIL]` line per item with a pointer back to the exact
  `REQUIREMENTS.md` subsection to fix it, and exiting non-zero if any
  required item is missing. Written for bash 3.2 (macOS's default shell) -
  no GNU-only `sort -V`, no bash-4-only syntax. `REQUIREMENTS.md` section
  3.4 explains how to run and read it; wired into the section 0
  walkthrough (now 9 steps) and `CONTRIBUTING.md`'s workflow as the first
  command to run in a fresh clone.

- `docs/slides/SLIDES-en-US.md` and `docs/slides/SLIDES-pt-BR.md`: a
  [Marp](https://marp.app) slide deck (bilingual pair, kept in parity, 35
  slides each) covering this repository's tooling (uv, AWS CDK v2/`aws-cdk-lib`,
  `pytest`/`mypy`/`ruff`, Docker Compose) with a focus on the AWS CDK
  workflow and floci - including its built-in console, the standalone
  `floci-ui` project, and `floci-dash` - plus the commands to run the
  hands-on lab, embedding the four diagrams already under `docs/images/`.
  Also embeds, under `docs/images/tools/`: the official AWS CDK and floci
  logos (from `aws/aws-cdk` and `floci-io/floci`'s own repos), the official
  floci-dash icon (`ofsazib/floci-dash`), direct quotes from each project's
  own README/homepage, and two screenshots (the built-in floci console and
  floci-dash) captured live against this repository's own
  `docker compose up -d floci`, with `IamStack`, `SqsStack`, `SnsStack`,
  `DynamoDbStack`, `KmsStack`, and `ParameterStoreStack` actually deployed
  to it. `REQUIREMENTS.md` section 11 documents how to install Marp CLI and
  render/export the decks to HTML/PDF/PPTX (`--allow-local-files` is
  required for the local images on the PDF/PPTX/PNG export paths, and the
  HTML export must be written into `docs/slides/` itself - see the next
  entry).

### Fixed

- `docs/slides/SLIDES-en-US.md` / `SLIDES-pt-BR.md`: the tool logos and
  live floci/floci-dash screenshots (previously `<img src="../images/tools/...">`)
  broke in exported HTML whenever the output file was written outside
  `docs/slides/` (a Desktop folder, the repo root, ...) - a browser
  resolves a relative `src` against the *exported* file's location, and
  Marp CLI never embeds referenced images into HTML output, only the
  theme's CSS. Fixed by embedding all 7 images as inline
  `data:image/...;base64,...` URIs directly in both decks, so every
  export format (HTML/PDF/PPTX/PNG) now works from any output directory
  with no extra step. The maintained original files stay under
  `docs/images/tools/` - see `REQUIREMENTS.md` section 11.2 for how to
  regenerate a data URI after replacing one. Trade-off: both `.md` files
  grew from ~50 KB to ~1.5 MB.
- `docs/slides/SLIDES-en-US.md` / `SLIDES-pt-BR.md`: the four embedded
  Mermaid SVGs (`01-cdk-workflow.svg` through `04-vpc-resources.svg`)
  rendered far too small on a 16:9 slide - `01-cdk-workflow.svg` in
  particular is a 553×1830 portrait flowchart, so fitting it inside a
  460px-tall slide left it barely 140px wide. Replaced all four with
  native HTML/CSS flow diagrams (new `.flow`/`.flow-box`/`.flow-arrow`
  and `.az-grid`/`.az-col` theme components) built from the same content
  as the underlying `.mmd` sources, sized to fill the slide and read at
  full font size; each slide still links to the full Mermaid diagram
  under `docs/images/` and the matching `docs/ARCHITECTURE.md` section
  for the authoritative, more detailed version.
- `REQUIREMENTS.md` section 11.2: the documented `-o slides-en.html`
  command wrote the exported file to the repository root, one directory
  above where the deck's `../images/...` paths actually resolve from -
  every image (including the two new tool-logo rows) rendered as a
  broken-image icon. Marp CLI inlines the theme's CSS into HTML output but
  never embeds `<img>` sources, and a browser resolves a relative `src`
  against the *exported* file's own location, not the source `.md`'s - so
  the fix is exporting into `docs/slides/` (where the source file already
  lives), not a CLI flag. PDF/PPTX/PNG export were unaffected (Chromium
  resolves those relative to the source `.md` regardless of `-o`), but the
  commands now write next to the source consistently either way.
- `docs/slides/SLIDES-en-US.md` / `SLIDES-pt-BR.md`: the "From identity to
  governance" slide's 11-card `cols-3` grid overlapped the footer/page
  number. Added a `.tight` grid modifier (smaller card padding/font) for
  this one densely-populated grid, applied only to that slide.
- `docker-compose.yml`: the `floci` service's `healthcheck` used `curl`,
  which the `floci/floci` image does not ship (a minimal native-binary
  image) - every attempt failed with `curl: executable file not found`,
  so the container never reported `healthy` and `floci-dash`'s
  `depends_on: condition: service_healthy` would wait forever. Now probes
  the port with bash's own `/dev/tcp` instead (bash is present in the
  image). Found and fixed while capturing the live floci/floci-dash
  screenshots for `docs/slides/SLIDES-*.md` above; verified against a real
  `docker compose --profile floci-dash up -d` run.
- `modules/03_vpc/stack.py`: read route table IDs from `vpc.isolated_subnets`
  instead of the (empty, for a `PRIVATE_ISOLATED`-only VPC) `vpc.private_subnets`.
- `modules/19_rds_postgresql` and `modules/20_rds_aurora`: master username
  changed from `"admin"` to `"dbadmin"` - AWS reserves `"admin"` for
  PostgreSQL-compatible RDS/Aurora engines (`cdk synth` flags it).
- `modules/22_elasticache/stack.py`: replaced the deprecated
  `CfnResource.add_dependency()` call with `add_resource_dependency()`.
- `app.py`: minor lint cleanup (direct attribute access instead of
  `getattr` with a constant name; made the file executable to match its
  shebang).
