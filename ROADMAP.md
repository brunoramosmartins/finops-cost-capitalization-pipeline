# FinOps Cost Capitalization Pipeline - Project Roadmap

> End-to-end Analytics Engineering project that simulates cloud billing data,
> applies a Medallion architecture (Bronze, Silver, Gold), classifies cloud
> spend into OPEX vs CAPEX-eligible categories, and publishes a versioned Gold
> data product ready for downstream ML forecasting and MLOps work.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Repository Structure](#3-repository-structure)
4. [Technology Stack](#4-technology-stack)
5. [GitHub Semantic Guide](#5-github-semantic-guide)
6. [Phase 1 - Foundation and Synthetic Data Generation](#phase-1---foundation-and-synthetic-data-generation)
7. [Phase 2 - Analytics Engineering Pipeline](#phase-2---analytics-engineering-pipeline)
8. [Phase 3 - Quality, Orchestration and CI/CD](#phase-3---quality-orchestration-and-cicd)
9. [Phase 4 - Gold Product and ML Handoff](#phase-4---gold-product-and-ml-handoff)
10. [Accounting Classification Rules Appendix](#10-accounting-classification-rules-appendix)
11. [Data Contracts and Quality Standards](#11-data-contracts-and-quality-standards)
12. [GitHub Workflow Standards Appendix](#12-github-workflow-standards-appendix)
13. [GitHub Automation Scripts](#13-github-automation-scripts)
14. [Issues Catalog](#14-issues-catalog)

---

## 1. Project Overview

### What This Project Does

This project simulates a realistic cloud billing and accounting scenario for a
company that needs to:

- generate synthetic cloud cost data with realistic financial and engineering tags
- ingest raw billing files into a local-first analytical stack
- transform the data through Bronze, Silver, and Gold layers
- classify cost lines into `opex`, `capex_eligible`, `shared_cost_review`, or `unclassified`
- expose a versioned Gold layer for dashboards, finance analysis, and a future ML repository

### Why This Project Matters

This is not just a data pipeline exercise. It demonstrates:

- Analytics Engineering with dbt and Medallion architecture
- FinOps reasoning applied to cloud billing
- financial classification logic expressed as reproducible SQL rules
- production rigor through orchestration, testing, CI/CD, and documented contracts
- a clean handoff from Analytics Engineering to MLOps

### Business Problem

Cloud invoices are operationally detailed but financially ambiguous. Finance teams
need a defensible process to distinguish:

- daily operational spend that should remain OPEX
- technology build costs that may be capitalized or amortized according to internal policy
- shared or weakly tagged spend that requires review instead of blind automation

This project produces a governed analytical layer that narrows that ambiguity.

### Project Success Criteria

- Synthetic billing data covers at least 12-24 months with realistic usage patterns
- Bronze, Silver, and Gold layers are reproducible from raw input files
- Gold outputs expose clear accounting recommendation fields and supporting rationale
- Data quality rules fail fast on broken assumptions
- Daily orchestration can run locally without manual intervention
- GitHub automation validates Python and dbt changes on every push and PR
- Gold data can be exported and consumed by a second ML-focused repository

### Primary Use Cases

| Use Case | Consumer | Output |
|----------|----------|--------|
| Simulate cloud billing at company scale | Data Engineer | Raw Parquet or CSV files in mock lake |
| Clean and standardize billing records | Analytics Engineer | Silver dbt models |
| Apply accounting rules for OPEX/CAPEX | Finance + FinOps | Gold classification tables |
| Publish versioned analytical features | ML Engineer | Gold exports for downstream forecasting |
| Validate pipeline quality on every change | Engineering Team | GitHub Actions + dbt tests + pytest |

### Recommended Milestone Cadence

| Phase | Milestone | Suggested Duration | Tag | Release |
|-------|-----------|--------------------|-----|---------|
| 1 | Foundation and Synthetic Data Generation | 2 weeks | `v0.1.0-foundation` | No |
| 2 | Analytics Engineering Pipeline | 3 weeks | `v0.2.0-transform` | No |
| 3 | Quality, Orchestration and CI/CD | 2 weeks | `v0.3.0-rigor` | Yes, prerelease |
| 4 | Gold Product and ML Handoff | 2 weeks | `v0.4.0-ml-handoff` | Yes, prerelease |
| Final | Portfolio Release | 2-3 days | `v1.0.0` | Yes |

### Scope Boundary

This repository owns the Analytics Engineering and data product layer.
The future ML repository will:

- consume Gold exports from this project
- train time-series or cost forecasting models
- track experiments with MLflow
- manage model packaging and deployment

This roadmap prepares that bridge, but does not implement the model itself here.

---

## 2. Architecture Overview

### End-to-End Data Flow

```text
Synthetic Billing Generator (Python: Pandas + Faker + NumPy)
            |
            v
Mock Data Lake
local_lake/raw/cloud_costs/run_date=YYYY-MM-DD/*.parquet
            |
            v
Bronze Layer (DuckDB + dbt source/raw models)
raw, append-only, minimal logic
            |
            v
Silver Layer (dbt staging + intermediate models)
standardized schema, type casts, UTC timestamps, normalized tags
            |
            v
Gold Layer (dbt marts)
OPEX vs CAPEX-eligible rules, allocations, summaries, finance-ready metrics
            |
            +----------------------+
            |                      |
            v                      v
Versioned Gold Exports        BI / Analytical Consumption
Parquet tables + metadata     DuckDB queries / notebooks / dashboards
            |
            v
Project 2 - ML Repository
feature consumption, experiment tracking, training, deployment
```

### Medallion Layer Responsibilities

| Layer | Purpose | Transformation Rule |
|-------|---------|---------------------|
| Bronze | Preserve raw provider-like structure | No business logic, append-only ingestion |
| Silver | Clean and standardize | Type casting, column normalization, timezone normalization, tag parsing |
| Gold | Apply finance rules | Accounting recommendation, allocation logic, amortization attributes, aggregated marts |

### Recommended Core Entities

| Layer | Model | Description |
|-------|-------|-------------|
| Bronze | `brz_cloud_cost_usage` | Raw usage and billing lines loaded from generated files |
| Bronze | `brz_generation_manifest` | Batch metadata for each synthetic load |
| Silver | `stg_cloud_cost_usage` | Typed and standardized billing line items |
| Silver | `stg_cloud_resource_tags` | Flattened and normalized infrastructure tags |
| Silver | `int_cost_enriched` | Billing joined with tag semantics and policy inputs |
| Gold | `fct_cost_classification` | Grain-level accounting recommendation |
| Gold | `fct_capex_candidate_costs` | CAPEX-eligible spend facts |
| Gold | `mart_monthly_finops_summary` | Monthly OPEX/CAPEX summary by team or product |
| Gold | `mart_capitalization_waterfall` | Review-ready bridge from raw cost to accounting recommendation |

### Orchestration Flow

```text
Dagster Job: daily_finops_pipeline

1. generate_synthetic_billing_files
2. validate_raw_drop_manifest
3. dbt seed (optional policy/reference tables)
4. dbt run --select bronze
5. dbt run --select silver
6. dbt test --select silver
7. dbt run --select gold
8. dbt test --select gold
9. export_gold_tables
10. publish_run_metadata
```

### Design Principles

- Local-first execution: the full pipeline must run on a laptop with DuckDB
- Cloud-ready abstractions: storage layout and contracts must allow later migration to S3, BigQuery, or Snowflake
- Accounting recommendations, not legal conclusions: the Gold layer should surface rationale and policy versioning
- Explainability over opacity: every Gold classification must be traceable back to tags and rule logic
- Reproducibility over convenience: batch manifests, run dates, and versioned exports are first-class artifacts

---

## 3. Repository Structure

```text
finops-cost-capitalization-pipeline/
|
|-- .github/
|   |-- ISSUE_TEMPLATE/
|   |   |-- task.md
|   |   `-- bug.md
|   |-- PULL_REQUEST_TEMPLATE.md
|   `-- workflows/
|       |-- ci.yml
|       `-- release.yml
|
|-- .claude/                         # Optional local assistant workflow
|   |-- system_prompt.md
|   |-- project_context.md
|   |-- code_style.md
|   `-- task_templates/
|       |-- dbt_model.md
|       |-- python_data_task.md
|       `-- review_checklist.md
|
|-- conf/
|   |-- accounting_policy.yml
|   |-- generator_profiles.yml
|   `-- pipeline.yml
|
|-- data/
|   |-- contracts/
|   |   |-- raw_cloud_cost_usage.yml
|   |   `-- gold_ml_handoff.yml
|   |-- dictionaries/
|   |   `-- tag_dictionary.md
|   `-- sample/
|       `-- README.md
|
|-- local_lake/                      # gitignored mock data lake
|   |-- raw/
|   |-- bronze/
|   |-- silver/
|   `-- gold/
|
|-- warehouse/
|   `-- finops.duckdb               # gitignored local warehouse file
|
|-- dbt/
|   |-- dbt_project.yml
|   |-- packages.yml
|   |-- models/
|   |   |-- bronze/
|   |   |-- silver/
|   |   |-- gold/
|   |   `-- marts/
|   |-- macros/
|   |-- tests/
|   |-- seeds/
|   `-- snapshots/
|
|-- orchestration/
|   `-- dagster_project/
|       |-- definitions.py
|       |-- jobs.py
|       |-- sensors.py
|       `-- assets.py
|
|-- scripts/
|   |-- generate_billing_data.py
|   |-- run_local_pipeline.py
|   |-- export_gold.py
|   |-- setup_labels.ps1
|   |-- setup_milestones.ps1
|   |-- setup_issues.ps1
|   `-- setup_all.ps1
|
|-- src/
|   `-- finops_capex/
|       |-- __init__.py
|       |-- generators/
|       |   |-- billing_generator.py
|       |   |-- patterns.py
|       |   `-- tags.py
|       |-- ingestion/
|       |   |-- manifest.py
|       |   `-- lake_writer.py
|       |-- policies/
|       |   `-- accounting_policy.py
|       |-- exports/
|       |   `-- gold_exporter.py
|       |-- quality/
|       |   |-- validators.py
|       |   `-- expectations.py
|       `-- utils/
|           |-- dates.py
|           `-- logging.py
|
|-- tests/
|   |-- unit/
|   |-- integration/
|   `-- fixtures/
|
|-- docs/
|   |-- architecture.md
|   |-- accounting_policy.md
|   |-- ml_handoff.md
|   |-- contributing.md
|   `-- runbooks/
|       |-- local_execution.md
|       |-- ci_cd.md
|       `-- incident_response.md
|
|-- .gitignore
|-- README.md
|-- ROADMAP.md
|-- requirements.txt
`-- requirements-dev.txt
```

### Naming Conventions

- Python modules: `snake_case`
- dbt staging models: `stg_*`
- dbt intermediate models: `int_*`
- dbt facts: `fct_*`
- dbt marts: `mart_*`
- Raw lake partitions: `run_date=YYYY-MM-DD`
- Export versions: `version=vX.Y.Z`

---

## 4. Technology Stack

### Recommended Default Stack

| Category | Choice | Why |
|----------|--------|-----|
| Language | Python 3.12 | Strong ecosystem for generation, orchestration, and testing |
| Data generation | Pandas, Faker, NumPy, PyArrow | Fast synthetic data generation and Parquet support |
| Local data lake | `local_lake/` directory | Simple, portable, and cloud-mappable |
| Warehouse | DuckDB | Excellent local analytics engine with dbt support |
| Transformations | dbt Core + dbt-duckdb | Best fit for Medallion analytics workflows |
| Orchestration | Dagster | Strong local developer experience and dbt integration |
| Testing | pytest, dbt tests, SQLFluff | Covers Python, SQL, and model contracts |
| Linting | Ruff + SQLFluff | Fast linting for Python and SQL |
| CI/CD | GitHub Actions | Standard portfolio-grade automation |
| Documentation | Markdown + dbt docs | Simple and reviewable |
| Optional cloud storage | AWS S3 or GCS | For future remote execution |

### Suggested Python Dependencies

`requirements.txt`

- `pandas`
- `numpy`
- `faker`
- `pyarrow`
- `duckdb`
- `dbt-core`
- `dbt-duckdb`
- `dagster`
- `dagster-dbt`
- `pyyaml`

`requirements-dev.txt`

- `pytest`
- `pytest-cov`
- `ruff`
- `sqlfluff`
- `pre-commit`

### Cloud-Ready Substitutions

| Local-first Choice | Cloud-ready Replacement |
|-------------------|-------------------------|
| `local_lake/` | AWS S3 or Google Cloud Storage |
| DuckDB | BigQuery, Snowflake, or Databricks SQL |
| Dagster local instance | Dagster Cloud, Airflow, or Composer |
| Parquet export folder | Feature store, managed table, or object storage zone |

### Architectural Recommendation

For this repository, the strongest portfolio path is:

- DuckDB as the warehouse
- dbt-duckdb for transformations
- Dagster for orchestration
- local Parquet lake for raw and exported data

This keeps the project fully reproducible locally while preserving a realistic
enterprise data engineering shape.

---

## 5. GitHub Semantic Guide

This section defines how issues, milestones, labels, tags, and releases should
be used in this project.

### 5.1 Issues

An issue represents one bounded unit of work: a feature, documentation task,
test suite, or operational improvement.

**When to create an issue:**

- before starting any roadmap task
- when identifying a broken data quality assumption
- when adding or changing accounting logic
- when making a workflow or CI/CD improvement

**Example - creating an issue:**

```bash
gh issue create \
  --title "feat(gold): implement accounting classification rules for opex vs capex eligibility" \
  --body-file .github/ISSUE_TEMPLATE/task.md \
  --label "feature,phase-2,priority:high" \
  --milestone "Phase 2 - Analytics Engineering Pipeline"
```

### 5.2 Milestones

Each phase maps to one milestone.

**Milestones for this roadmap:**

- `Phase 1 - Foundation and Synthetic Data Generation`
- `Phase 2 - Analytics Engineering Pipeline`
- `Phase 3 - Quality, Orchestration and CI/CD`
- `Phase 4 - Gold Product and ML Handoff`

**When to create a milestone:**

- once at project setup
- before creating the phase issues

**Example - creating a milestone:**

```bash
gh api repos/{owner}/{repo}/milestones \
  --method POST \
  -f title="Phase 3 - Quality, Orchestration and CI/CD" \
  -f description="Add data quality rules, orchestration, observability, and GitHub automation." \
  -f state="open"
```

### 5.3 Labels

Recommended label taxonomy:

- Type labels: `feature`, `data`, `quality`, `orchestration`, `infra`, `docs`, `test`, `release`
- Phase labels: `phase-1`, `phase-2`, `phase-3`, `phase-4`
- Priority labels: `priority:high`, `priority:medium`
- Status labels: `blocked`, `needs-review`

### 5.4 Tags

Tags are used as phase completion snapshots.

**Naming convention:**

- `v0.1.0-foundation`
- `v0.2.0-transform`
- `v0.3.0-rigor`
- `v0.4.0-ml-handoff`
- `v1.0.0`

**When to create a tag:**

- after all milestone issues are closed
- after the phase PR is merged into `main`

### 5.5 Releases

Releases are only created when the repository has external demonstration value.

- Phase 1: no release
- Phase 2: no release
- Phase 3: prerelease allowed
- Phase 4: prerelease or release candidate
- Final: `v1.0.0` release

**Example - creating a prerelease:**

```bash
gh release create v0.3.0-rigor \
  --title "v0.3.0 - Quality, Orchestration and CI/CD" \
  --notes "Pipeline now runs end-to-end with Dagster, dbt tests, pytest, and GitHub Actions." \
  --prerelease
```

### 5.6 Relationship Diagram

```text
Milestone (Phase 2 - Analytics Engineering Pipeline)
 |-- Issue #10: bootstrap DuckDB + dbt project
 |-- Issue #11: create Bronze ingestion models
 |-- Issue #12: create Silver standardization models
 |-- Issue #13: implement Gold accounting rules
 `-- Issue #14: publish dbt docs
            |
            v
      Tag: v0.2.0-transform
            |
            v
      Release: none
```

---

## Phase 1 - Foundation and Synthetic Data Generation

**Objective:** Build the repository foundation, standardize the local engineering
workflow, and generate realistic synthetic cloud billing data with finance-ready
tags and operational variability.

### Tasks

- [ ] **P1-01: Bootstrap repository and collaboration standards**
  - [ ] Create `README.md`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`
  - [ ] Add `LICENSE`
  - [ ] Create `.github/ISSUE_TEMPLATE/`, PR template, and base workflows
  - [ ] Add `docs/` and `tests/` skeleton
  - [ ] Document project goals and execution commands

- [ ] **P1-02: Configure local agent workflow**
  - [ ] Create `.claude/system_prompt.md`
  - [ ] Create `.claude/project_context.md`
  - [ ] Create `.claude/code_style.md`
  - [ ] Add reusable prompt templates for dbt, Python, and reviews
  - [ ] Document how these prompts are used to standardize code generation

- [ ] **P1-03: Implement synthetic billing generator**
  - [ ] Create Python generator modules in `src/finops_capex/generators/`
  - [ ] Generate provider-like billing rows for compute, storage, database, network, and support services
  - [ ] Support at least daily granularity across 12-24 months
  - [ ] Include payer account, linked account, service, resource, usage type, region, and cost metrics

- [ ] **P1-04: Inject realistic usage behavior**
  - [ ] Add monthly seasonality patterns
  - [ ] Add weekday versus weekend effects
  - [ ] Add deployment spikes, product launches, and anomalous cost surges
  - [ ] Add discounts or credits to mimic real billing adjustments
  - [ ] Add imperfect tagging rate to make Silver cleaning meaningful

- [ ] **P1-05: Model finance and infrastructure tags**
  - [ ] Generate tags such as `cost_center`, `owner_team`, `environment`, `product_line`
  - [ ] Generate accounting-oriented tags such as `capitalization_candidate`, `initiative_id`, `initiative_stage`, `asset_lifecycle`
  - [ ] Add policy metadata such as `accounting_policy_version`
  - [ ] Define valid and invalid tag scenarios

- [ ] **P1-06: Persist raw drops into the mock lake**
  - [ ] Save generated data to `local_lake/raw/`
  - [ ] Partition by `run_date`
  - [ ] Prefer Parquet, optionally produce CSV samples
  - [ ] Emit batch manifest with row counts, date coverage, and checksum-friendly metadata
  - [ ] Keep a small sample subset in `data/sample/` for tests and docs

### Deliverables

- [x] Repository skeleton exists and is documented
- [x] Local assistant workflow exists under `.claude/`
- [x] Synthetic billing generator creates realistic billing drops
- [x] Raw data includes infrastructure and accounting tags
- [x] Mock data lake receives partitioned files plus run manifest
- [x] Sample dataset and raw contract are documented

### GitHub

| Item | Value |
|------|-------|
| Branch | `feat/foundation-data-generation` |
| Merge strategy | Squash merge into `main` |
| PR title | `feat(data): bootstrap repo and synthetic cloud billing generator` |
| Milestone | `Phase 1 - Foundation and Synthetic Data Generation` |
| Tag | `v0.1.0-foundation` |
| Release | No - internal foundation only |

---

## Phase 2 - Analytics Engineering Pipeline

**Objective:** Build the Bronze, Silver, and Gold layers in DuckDB with dbt,
turn raw generated cost files into standardized analytical models, and encode
the accounting recommendation logic that separates OPEX from CAPEX-eligible spend.

### Tasks

- [ ] **P2-01: Bootstrap DuckDB warehouse and dbt project**
  - [ ] Create `dbt/dbt_project.yml` and `packages.yml`
  - [ ] Configure dbt profile for DuckDB
  - [ ] Create source definitions for raw lake files
  - [ ] Configure materializations and model folders by layer

- [ ] **P2-02: Build Bronze ingestion models**
  - [ ] Load raw files into `brz_cloud_cost_usage`
  - [ ] Preserve provider-like raw columns
  - [ ] Add ingestion metadata: `source_file_name`, `ingestion_timestamp`, `batch_id`
  - [ ] Avoid business-rule transformations in Bronze

- [ ] **P2-03: Build Silver standardization models**
  - [ ] Normalize column names
  - [ ] Cast timestamps, numeric fields, and booleans correctly
  - [ ] Convert all operational timestamps to UTC
  - [ ] Flatten or normalize tag structures
  - [ ] Handle nulls and invalid placeholders in a deterministic way
  - [ ] Create reusable intermediate models for enriched records

- [ ] **P2-04: Build Gold accounting models**
  - [ ] Create rule-based classification into `opex`, `capex_eligible`, `shared_cost_review`, `unclassified`
  - [ ] Add `classification_reason`
  - [ ] Add `policy_version`
  - [ ] Add `amortization_months_default` where applicable
  - [ ] Separate direct product-build costs from shared or operational costs

- [ ] **P2-05: Build marts for finance and FinOps consumers**
  - [ ] Monthly summary by team and product
  - [ ] CAPEX candidate summary by initiative and lifecycle stage
  - [ ] Waterfall from raw cost to accounting recommendation
  - [ ] Optional anomaly summary for spike interpretation

- [ ] **P2-06: Publish lineage and transformation documentation**
  - [ ] Add model-level descriptions
  - [ ] Add dbt tests on key columns
  - [ ] Generate dbt docs artifacts
  - [ ] Document business logic in `docs/accounting_policy.md`

### Deliverables

- [x] DuckDB and dbt project are runnable locally
- [x] Bronze layer preserves raw billing structure
- [x] Silver layer standardizes schema and tags
- [x] Gold layer exposes accounting recommendations with rationale
- [x] Finance-friendly marts exist for downstream consumption
- [x] dbt docs and lineage are generated

### GitHub

| Item | Value |
|------|-------|
| Branch | `feat/medallion-transformations` |
| Merge strategy | Squash merge into `main` |
| PR title | `feat(dbt): build bronze-silver-gold models for finops accounting pipeline` |
| Milestone | `Phase 2 - Analytics Engineering Pipeline` |
| Tag | `v0.2.0-transform` |
| Release | No - transformation logic only |

---

## Phase 3 - Quality, Orchestration and CI/CD

**Objective:** Add production discipline to the pipeline: enforce data quality,
orchestrate daily execution, improve observability, and ensure every code change
is validated automatically through GitHub Actions.

### Tasks

- [ ] **P3-01: Implement data quality controls**
  - [ ] dbt tests for uniqueness, non-nullness, accepted values, and relationships
  - [ ] Custom tests to ensure cost fields are never negative
  - [ ] Custom tests to ensure Gold classification values stay within the approved domain
  - [ ] Manifest checks to ensure raw batch completeness

- [ ] **P3-02: Orchestrate the full pipeline**
  - [ ] Create Dagster assets or jobs for generator, dbt layers, and exports
  - [ ] Add daily schedule
  - [ ] Add partition-aware run configuration
  - [ ] Capture run status and timestamps

- [ ] **P3-03: Add operational metadata and observability**
  - [ ] Persist run metadata such as row counts and data freshness
  - [ ] Log pipeline failures with actionable error messages
  - [ ] Document recovery path in `docs/runbooks/incident_response.md`
  - [ ] Optionally add lightweight notifications for failed runs

- [ ] **P3-04: Build CI/CD automation**
  - [ ] GitHub Actions for Python lint and tests
  - [ ] GitHub Actions for dbt parse, run, and test against fixture data
  - [ ] Pull request validation before merge
  - [ ] Optional release workflow on tag push

- [ ] **P3-05: Harden local developer workflow**
  - [ ] Add `pre-commit`
  - [ ] Add Ruff and SQLFluff
  - [ ] Add one-command local execution script
  - [ ] Document environment setup in `docs/contributing.md`

### Deliverables

- [x] Data quality rules exist for Bronze, Silver, and Gold
- [x] Dagster runs the pipeline end to end
- [x] Operational metadata is persisted and documented
- [x] GitHub Actions validate both Python and dbt work
- [x] Local developer workflow is reproducible

### GitHub

| Item | Value |
|------|-------|
| Branch | `feat/pipeline-rigor-and-automation` |
| Merge strategy | Squash merge into `main` |
| PR title | `feat(ops): add quality gates orchestration and ci for finops pipeline` |
| Milestone | `Phase 3 - Quality, Orchestration and CI/CD` |
| Tag | `v0.3.0-rigor` |
| Release | Yes - prerelease recommended |

---

## Phase 4 - Gold Product and ML Handoff

**Objective:** Turn the Gold layer into a versioned analytical product, formalize
the contract for downstream ML consumption, and prepare the second repository to
consume stable finance-ready features.

### Tasks

- [ ] **P4-01: Export Gold data as a versioned product**
  - [ ] Export selected Gold tables to `local_lake/gold/exports/`
  - [ ] Partition by snapshot date
  - [ ] Add semantic export versioning
  - [ ] Emit metadata manifest with schema, row counts, and freshness

- [ ] **P4-02: Define the ML handoff contract**
  - [ ] Document table grain, keys, and feature semantics
  - [ ] Define freshness expectation
  - [ ] Define backfill behavior
  - [ ] Define null handling and accepted value domains
  - [ ] Publish contract in `data/contracts/gold_ml_handoff.yml`

- [ ] **P4-03: Create bridge artifacts for Project 2**
  - [ ] Create `docs/ml_handoff.md`
  - [ ] Define how Project 2 reads the exported Gold data
  - [ ] Define initial forecasting target candidates
  - [ ] Define minimum features and train-validation split assumptions

- [ ] **P4-04: Specify MLOps bootstrap scope**
  - [ ] Outline second repository structure
  - [ ] Define MLflow integration expectations
  - [ ] Define baseline experiment tracking fields
  - [ ] Define deployment and serving assumptions at a high level

- [ ] **P4-05: Finalize portfolio documentation and release**
  - [ ] Finish architecture and runbook docs
  - [ ] Add demo-oriented README sections
  - [ ] Create release notes for `v0.4.0-ml-handoff`
  - [ ] Prepare `v1.0.0` once documentation and end-to-end validation are complete

### Deliverables

- [x] Gold exports are versioned and reproducible
- [x] ML handoff contract is explicit and documented
- [x] Project 2 bootstrap assumptions are captured
- [x] Portfolio-grade documentation exists
- [x] Release candidate and final release path are defined

### GitHub

| Item | Value |
|------|-------|
| Branch | `feat/gold-product-and-ml-handoff` |
| Merge strategy | Squash merge into `main` |
| PR title | `feat(export): publish versioned gold data product and ml handoff contract` |
| Milestone | `Phase 4 - Gold Product and ML Handoff` |
| Tag | `v0.4.0-ml-handoff` |
| Release | Yes - prerelease or release candidate |

---

## 10. Accounting Classification Rules Appendix

### Important Governance Note

This pipeline should produce an **accounting recommendation** based on explicit
business rules. It should not claim legal or statutory accounting authority on
its own. Final capitalization decisions remain subject to company policy and
finance review.

### Recommended Gold Classification Domain

- `opex`
- `capex_eligible`
- `shared_cost_review`
- `unclassified`

### Suggested Rule Inputs

| Input Field | Meaning |
|------------|---------|
| `capitalization_candidate` | Whether engineering tagged the resource as potentially capitalizable |
| `initiative_id` | Project or build initiative identifier |
| `initiative_stage` | `discovery`, `build`, `implementation`, `operate`, `support` |
| `asset_lifecycle` | `prototype`, `construction`, `production`, `maintenance` |
| `environment` | `dev`, `test`, `staging`, `prod`, `sandbox` |
| `owner_team` | Responsible engineering or platform team |
| `product_line` | Product or platform being funded |
| `shared_service_flag` | Whether the cost is shared broadly across domains |
| `policy_version` | Accounting policy version applied |

### Suggested Classification Logic

| Rule Group | Condition | Result |
|-----------|-----------|--------|
| Direct build cost | `capitalization_candidate = true` and `initiative_stage in ('build','implementation')` and `shared_service_flag = false` | `capex_eligible` |
| Shared platform baseline | Shared infrastructure with weak initiative mapping | `shared_cost_review` |
| Daily operations | `initiative_stage in ('operate','support')` | `opex` |
| Sandbox and experiments | `environment in ('sandbox','test')` without explicit approved initiative | `opex` |
| Missing critical tags | Null `initiative_id` or invalid accounting tags | `unclassified` or `shared_cost_review` |

### Recommended Gold Fields

- `classification_status`
- `classification_reason`
- `policy_version`
- `capitalization_candidate_flag`
- `initiative_id`
- `initiative_stage`
- `shared_service_flag`
- `amortization_months_default`
- `review_required_flag`
- `source_batch_id`

---

## 11. Data Contracts and Quality Standards

### Raw Contract - Minimum Fields

- time: `billing_period_start`, `usage_start_time`, `usage_end_time`, `invoice_date`
- billing identity: `cloud_provider`, `payer_account_id`, `linked_account_id`
- technical detail: `service`, `usage_type`, `operation`, `region`, `resource_id`
- finance detail: `currency_code`, `unblended_cost`, `blended_cost`, `discount_type`
- tags: `cost_center`, `owner_team`, `environment`, `product_line`, `capitalization_candidate`, `initiative_id`, `initiative_stage`, `asset_lifecycle`
- metadata: `generator_batch_id`, `source_file_name`, `generated_at`

### Mandatory Quality Rules

#### Bronze

- cost fields must parse as numeric
- composite raw key must be unique per generated line
- source manifest row count must match file contents

#### Silver

- timestamps must be in UTC
- boolean fields must be normalized
- invalid placeholder strings must be replaced deterministically
- tag domains must be standardized

#### Gold

- `classification_status` must be one of the approved values
- aggregated totals must reconcile against Silver within accepted tolerance
- no negative cost totals
- monthly summary primary keys must be unique

### Freshness and Runtime Expectations

- Raw drop frequency: daily
- Bronze to Gold runtime target: under 15 minutes locally on sample scale
- Freshness SLA for Gold export: latest successful daily run
- Failed run behavior: no overwrite of previous successful export version

---

## 12. GitHub Workflow Standards Appendix

### Branch Naming

- `feat/foundation-data-generation`
- `feat/silver-standardization`
- `feat/gold-accounting-rules`
- `feat/orchestration-dagster`
- `test/gold-quality-suite`
- `docs/ml-handoff-contract`
- `chore/github-automation`

### Conventional Commits

- `feat(data): add synthetic billing seasonality`
- `feat(dbt): create silver cost standardization models`
- `feat(gold): implement capex eligibility rules`
- `test(quality): add accepted value tests for gold classifications`
- `docs(ml): define downstream feature contract`
- `chore(ci): run pytest and dbt tests on pull requests`

### Pull Request Template

```md
## Description

## Related Issues

## Changes

## Validation

## Checklist
- [ ] Python tests passed
- [ ] dbt build passed
- [ ] Documentation updated
```

### Issue Template - Task

```md
## Context

## Tasks

## Definition of Done

## References
```

### Suggested PR Review Policy

- at least one review before merge
- CI must be green
- phase label and milestone must be assigned
- if Gold logic changes, accounting policy doc must be reviewed

---

## 13. GitHub Automation Scripts

These scripts create the labels, milestones, and initial issue backlog for the
project using the GitHub CLI.

### Script Locations

```text
scripts/
|-- setup_labels.ps1
|-- setup_milestones.ps1
|-- setup_issues.ps1
`-- setup_all.ps1
```

### Suggested Responsibilities

- `setup_labels.ps1`: create type, phase, priority, and status labels
- `setup_milestones.ps1`: create the four roadmap milestones
- `setup_issues.ps1`: create all issues listed in Section 14
- `setup_all.ps1`: run the three scripts in order

### Prerequisites

- GitHub CLI installed and authenticated with `gh auth login`
- repository already created on GitHub
- permissions to create issues and milestones

---

## 14. Issues Catalog

### Phase 1 Issues

---

#### Issue: `chore(repo): bootstrap repository structure docs and base tooling`

**Labels:** `infra`, `docs`, `phase-1`
**Milestone:** `Phase 1 - Foundation and Synthetic Data Generation`

**Body:**

```md
## Context

The project needs a clean and professional repository foundation before any data
engineering work begins. This includes the base documentation, dependency files,
gitignore rules, test skeleton, and GitHub collaboration templates.

## Tasks

- [ ] Create `README.md` with project overview and execution goals
- [ ] Create `requirements.txt` and `requirements-dev.txt`
- [ ] Create `.gitignore` for Python, DuckDB, local lake files, and environment files
- [ ] Add `LICENSE`
- [ ] Create `docs/`, `tests/`, `scripts/`, and `src/` skeletons
- [ ] Create GitHub issue template and PR template

## Definition of Done

- [ ] Repository is clone-ready and understandable
- [ ] Dependency files are committed
- [ ] Local artifacts are ignored properly
- [ ] GitHub templates exist and are usable

## References

- Section 3 - Repository Structure
- Section 12 - GitHub Workflow Standards Appendix
```

---

#### Issue: `chore(agent-workflow): define local assistant prompts and coding standards`

**Labels:** `infra`, `docs`, `phase-1`
**Milestone:** `Phase 1 - Foundation and Synthetic Data Generation`

**Body:**

```md
## Context

The repository should define a local assistant workflow from day zero so prompts,
code style, and review expectations stay consistent across repetitive tasks.

## Tasks

- [ ] Create `.claude/system_prompt.md`
- [ ] Create `.claude/project_context.md`
- [ ] Create `.claude/code_style.md`
- [ ] Add prompt templates for Python data tasks, dbt model creation, and reviews
- [ ] Document how team members should use and update these files

## Definition of Done

- [ ] `.claude/` contains reusable project guidance
- [ ] Prompt files reflect repository-specific standards
- [ ] The workflow is documented in `docs/contributing.md`

## References

- Phase 1 roadmap tasks
- Section 3 - Repository Structure
```

---

#### Issue: `feat(data-gen): implement synthetic cloud billing generator core`

**Labels:** `feature`, `data`, `phase-1`, `priority:high`
**Milestone:** `Phase 1 - Foundation and Synthetic Data Generation`

**Body:**

```md
## Context

This project depends on a realistic synthetic billing dataset that mimics a cloud
provider cost and usage export. The generator must create enough structure to
support Bronze, Silver, Gold, and future ML use cases.

## Tasks

- [ ] Create generator modules in `src/finops_capex/generators/`
- [ ] Generate at least 12 months of daily billing data
- [ ] Include compute, storage, database, network, and support services
- [ ] Generate provider-like fields such as service, usage_type, region, resource_id, account IDs
- [ ] Add cost metrics and billing timestamps
- [ ] Add unit tests for row shape and date coverage

## Definition of Done

- [ ] Generator produces stable and valid raw billing rows
- [ ] Output volume is sufficient for downstream transformations
- [ ] Tests validate schema and coverage

## References

- Section 2 - Architecture Overview
- Section 11 - Data Contracts and Quality Standards
```

---

#### Issue: `feat(data-gen): inject seasonality spikes discounts and imperfect tagging`

**Labels:** `feature`, `data`, `phase-1`
**Milestone:** `Phase 1 - Foundation and Synthetic Data Generation`

**Body:**

```md
## Context

Purely random billing data is not analytically valuable. The generator must
inject realistic business patterns so the later transformation and ML stages
have meaningful signals to work with.

## Tasks

- [ ] Add monthly seasonality profiles
- [ ] Add weekday versus weekend behavior
- [ ] Add anomalous spikes for releases or migrations
- [ ] Add discount and credit patterns
- [ ] Add incomplete or invalid tags for a controlled subset of rows
- [ ] Document all synthetic assumptions

## Definition of Done

- [ ] Dataset shows visible seasonality and anomalies
- [ ] Imperfect tagging exists but stays within expected rate
- [ ] Assumptions are documented and reproducible

## References

- Phase 1 roadmap tasks
- Section 1 - Project Success Criteria
```

---

#### Issue: `feat(tags): model infrastructure and accounting tags for cost classification`

**Labels:** `feature`, `data`, `phase-1`, `priority:high`
**Milestone:** `Phase 1 - Foundation and Synthetic Data Generation`

**Body:**

```md
## Context

The Gold layer can only produce meaningful accounting recommendations if the raw
data carries the right semantic tags. The synthetic generator must therefore
model both infrastructure ownership and accounting-policy-oriented metadata.

## Tasks

- [ ] Generate tags such as `cost_center`, `owner_team`, `environment`, `product_line`
- [ ] Generate accounting tags such as `capitalization_candidate`, `initiative_id`, `initiative_stage`, `asset_lifecycle`
- [ ] Add `policy_version` to generated rows
- [ ] Define valid values and invalid edge cases
- [ ] Add tests for accepted tag domains

## Definition of Done

- [ ] Required tags exist in generated data
- [ ] Edge cases exist for Silver cleaning and Gold review states
- [ ] Tag domains are documented

## References

- Section 10 - Accounting Classification Rules Appendix
- Section 11 - Data Contracts and Quality Standards
```

---

#### Issue: `feat(storage): persist raw billing files to versioned mock lake layout`

**Labels:** `feature`, `infra`, `phase-1`
**Milestone:** `Phase 1 - Foundation and Synthetic Data Generation`

**Body:**

```md
## Context

The pipeline needs a stable mock data lake layout that behaves like an object
storage landing zone. Raw files must be stored in a predictable partition scheme
and accompanied by manifest metadata.

## Tasks

- [ ] Save generator output to `local_lake/raw/cloud_costs/run_date=YYYY-MM-DD/`
- [ ] Prefer Parquet output and optionally emit CSV samples
- [ ] Create batch manifest with row counts and date boundaries
- [ ] Store sample subset in `data/sample/`
- [ ] Add integration test covering write path and manifest creation

## Definition of Done

- [ ] Raw landing zone is deterministic
- [ ] Each run emits files and manifest metadata
- [ ] Sample data exists for docs and CI fixtures

## References

- Section 3 - Repository Structure
- Section 11 - Data Contracts and Quality Standards
```

---

#### Issue: `docs(data): define raw data contract and generation assumptions`

**Labels:** `docs`, `data`, `phase-1`
**Milestone:** `Phase 1 - Foundation and Synthetic Data Generation`

**Body:**

```md
## Context

Without an explicit raw contract, downstream dbt models and tests will drift.
The project needs a written contract for fields, assumptions, and acceptable
synthetic edge cases.

## Tasks

- [ ] Create `data/contracts/raw_cloud_cost_usage.yml`
- [ ] Document field definitions and expected domains
- [ ] Document generation assumptions such as seasonality and anomaly behavior
- [ ] Document sample volumes and date coverage
- [ ] Link the contract from the README and roadmap

## Definition of Done

- [ ] Raw schema is formally documented
- [ ] Edge cases are explicitly listed
- [ ] Downstream model authors can depend on the contract

## References

- Section 11 - Data Contracts and Quality Standards
- Phase 1 roadmap tasks
```

### Phase 2 Issues

---

#### Issue: `chore(warehouse): bootstrap duckdb warehouse and dbt project`

**Labels:** `infra`, `feature`, `phase-2`, `priority:high`
**Milestone:** `Phase 2 - Analytics Engineering Pipeline`

**Body:**

```md
## Context

Phase 2 starts by establishing the local analytical platform: DuckDB as the
warehouse and dbt as the transformation framework.

## Tasks

- [ ] Create `dbt/dbt_project.yml`
- [ ] Configure `dbt-duckdb` profile
- [ ] Add source definitions for raw landing files
- [ ] Configure model directories for Bronze, Silver, Gold, and marts
- [ ] Add base macros or helper packages if needed

## Definition of Done

- [ ] `dbt debug` passes locally
- [ ] DuckDB database is created successfully
- [ ] Project structure matches the roadmap

## References

- Section 4 - Technology Stack
- Phase 2 roadmap tasks
```

---

#### Issue: `feat(bronze): ingest raw billing files into append-only bronze models`

**Labels:** `feature`, `data`, `phase-2`
**Milestone:** `Phase 2 - Analytics Engineering Pipeline`

**Body:**

```md
## Context

The Bronze layer should preserve the generated billing data with minimal logic
while making it queryable inside DuckDB.

## Tasks

- [ ] Create `brz_cloud_cost_usage`
- [ ] Ingest raw Parquet or CSV files from the mock lake
- [ ] Preserve original raw columns
- [ ] Add ingestion metadata such as source file and ingestion timestamp
- [ ] Keep Bronze free of business classification logic

## Definition of Done

- [ ] Raw files are queryable through Bronze models
- [ ] Append-only pattern is preserved
- [ ] Metadata columns support lineage and debugging

## References

- Section 2 - Medallion Layer Responsibilities
- Section 11 - Data Contracts and Quality Standards
```

---

#### Issue: `feat(silver): standardize billing schema timestamps and tag normalization`

**Labels:** `feature`, `data`, `phase-2`, `priority:high`
**Milestone:** `Phase 2 - Analytics Engineering Pipeline`

**Body:**

```md
## Context

The Silver layer is where raw billing data becomes analytically trustworthy.
Timestamps, numerics, booleans, and tags must be normalized before any finance
logic is applied.

## Tasks

- [ ] Create `stg_cloud_cost_usage`
- [ ] Normalize column names
- [ ] Cast timestamps and numeric fields correctly
- [ ] Convert operational timestamps to UTC
- [ ] Normalize boolean fields and tag domains
- [ ] Create intermediate enriched model for reusable downstream joins

## Definition of Done

- [ ] Silver data types are correct and consistent
- [ ] Tag values use standardized domains
- [ ] Models are reusable by Gold without re-cleaning raw fields

## References

- Phase 2 roadmap tasks
- Section 11 - Data Contracts and Quality Standards
```

---

#### Issue: `feat(gold): implement accounting classification rules for opex vs capex eligibility`

**Labels:** `feature`, `data`, `phase-2`, `priority:high`
**Milestone:** `Phase 2 - Analytics Engineering Pipeline`

**Body:**

```md
## Context

This is the core business-value issue of the project. The Gold layer must
convert clean cost lines into explainable accounting recommendations with
explicit reasoning and policy versioning.

## Tasks

- [ ] Create `fct_cost_classification`
- [ ] Implement classification domain: `opex`, `capex_eligible`, `shared_cost_review`, `unclassified`
- [ ] Add `classification_reason`
- [ ] Add `policy_version`
- [ ] Add `amortization_months_default` where applicable
- [ ] Add tests for accepted classification values

## Definition of Done

- [ ] Every Gold row has a classification status
- [ ] The classification is explainable from rule logic
- [ ] Policy versioning is visible in output

## References

- Section 10 - Accounting Classification Rules Appendix
- Phase 2 roadmap tasks
```

---

#### Issue: `feat(marts): build finance-ready summary marts and capitalization waterfall`

**Labels:** `feature`, `data`, `phase-2`
**Milestone:** `Phase 2 - Analytics Engineering Pipeline`

**Body:**

```md
## Context

Beyond row-level classification, the project needs summary tables that finance,
FinOps, and downstream consumers can use directly.

## Tasks

- [ ] Create monthly team-level cost summary mart
- [ ] Create initiative-level CAPEX candidate mart
- [ ] Create waterfall mart from raw cost to accounting recommendation
- [ ] Ensure marts reconcile back to lower-grain models
- [ ] Document mart grains and primary keys

## Definition of Done

- [ ] Summary marts are query-ready
- [ ] Aggregates reconcile to classified facts
- [ ] Mart grain and keys are documented

## References

- Section 2 - Recommended Core Entities
- Phase 2 roadmap tasks
```

---

#### Issue: `docs(dbt): document model lineage and business logic across bronze silver gold`

**Labels:** `docs`, `data`, `phase-2`
**Milestone:** `Phase 2 - Analytics Engineering Pipeline`

**Body:**

```md
## Context

The dbt project should be understandable by reviewers and future maintainers.
Model descriptions, lineage context, and business logic notes must be written,
not implied.

## Tasks

- [ ] Add model descriptions and column descriptions
- [ ] Generate dbt docs artifacts
- [ ] Document Bronze, Silver, and Gold responsibilities
- [ ] Link business logic to `docs/accounting_policy.md`
- [ ] Add usage notes for key marts

## Definition of Done

- [ ] dbt docs can be generated locally
- [ ] Key models have useful descriptions
- [ ] Business logic is discoverable from docs

## References

- Phase 2 roadmap tasks
- Section 3 - Repository Structure
```

### Phase 3 Issues

---

#### Issue: `test(data): implement data quality suite across bronze silver and gold`

**Labels:** `test`, `quality`, `phase-3`, `priority:high`
**Milestone:** `Phase 3 - Quality, Orchestration and CI/CD`

**Body:**

```md
## Context

The project needs robust data quality protections before it can claim production
discipline. Quality must be enforced at multiple layers, not just assumed.

## Tasks

- [ ] Add uniqueness tests for key models
- [ ] Add non-null tests for required columns
- [ ] Add accepted value tests for Gold classification fields
- [ ] Add custom tests for non-negative cost amounts
- [ ] Add relationship tests where dimensions and facts connect
- [ ] Add fixture-driven validation for edge cases

## Definition of Done

- [ ] Bronze, Silver, and Gold all have explicit test coverage
- [ ] Invalid classification values fail the pipeline
- [ ] Negative costs are blocked unless explicitly modeled as credits

## References

- Section 11 - Data Contracts and Quality Standards
- Phase 3 roadmap tasks
```

---

#### Issue: `feat(orchestration): orchestrate generator dbt and exports with dagster`

**Labels:** `feature`, `orchestration`, `phase-3`, `priority:high`
**Milestone:** `Phase 3 - Quality, Orchestration and CI/CD`

**Body:**

```md
## Context

To simulate a professional analytics platform, the full pipeline must run as a
scheduled workflow rather than a manual sequence of ad hoc commands.

## Tasks

- [ ] Create Dagster project under `orchestration/dagster_project/`
- [ ] Model generator, dbt runs, tests, and exports as assets or jobs
- [ ] Add daily schedule
- [ ] Add run configuration for date partitions
- [ ] Capture run metadata and failures
- [ ] Add integration test for the orchestrated path

## Definition of Done

- [ ] A daily job can run the full pipeline locally
- [ ] Failures are visible and actionable
- [ ] Orchestration flow matches the roadmap sequence

## References

- Section 2 - Orchestration Flow
- Section 4 - Technology Stack
```

---

#### Issue: `feat(observability): publish run metadata freshness and failure logging`

**Labels:** `feature`, `quality`, `phase-3`
**Milestone:** `Phase 3 - Quality, Orchestration and CI/CD`

**Body:**

```md
## Context

Operational visibility separates hobby pipelines from professional ones. Each
run should publish enough metadata to answer what ran, when it ran, and whether
the outputs are trustworthy.

## Tasks

- [ ] Store run timestamp, batch ID, row counts, and model status
- [ ] Add freshness markers for Gold exports
- [ ] Log failures with stage-specific context
- [ ] Document incident response path in `docs/runbooks/incident_response.md`
- [ ] Add simple success and failure summary output

## Definition of Done

- [ ] Every run produces metadata
- [ ] Freshness is visible for downstream consumers
- [ ] Failure investigation starts from one documented location

## References

- Phase 3 roadmap tasks
- Section 11 - Freshness and Runtime Expectations
```

---

#### Issue: `chore(ci): add github actions for python lint pytest and dbt validation`

**Labels:** `infra`, `test`, `phase-3`, `priority:high`
**Milestone:** `Phase 3 - Quality, Orchestration and CI/CD`

**Body:**

```md
## Context

Every push and pull request must validate both the Python side and the dbt side
of the project before merge.

## Tasks

- [ ] Create `.github/workflows/ci.yml`
- [ ] Run Ruff
- [ ] Run pytest
- [ ] Run SQLFluff
- [ ] Run `dbt parse`
- [ ] Run `dbt build` or `dbt test` against fixture data
- [ ] Fail fast on quality regressions

## Definition of Done

- [ ] Push and PR events trigger CI
- [ ] Python and SQL validation both run automatically
- [ ] Broken transformations or tests block merge

## References

- Phase 3 roadmap tasks
- Section 12 - GitHub Workflow Standards Appendix
```

---

#### Issue: `chore(tooling): add pre-commit sql linting and one-command local execution`

**Labels:** `infra`, `quality`, `phase-3`
**Milestone:** `Phase 3 - Quality, Orchestration and CI/CD`

**Body:**

```md
## Context

The developer workflow should catch quality issues before code ever reaches CI.
Local commands must be simple and repeatable.

## Tasks

- [ ] Configure `pre-commit`
- [ ] Add Ruff hooks
- [ ] Add SQLFluff hooks
- [ ] Add local command for end-to-end execution
- [ ] Document commands in `docs/contributing.md`

## Definition of Done

- [ ] Local hooks catch common style and quality issues
- [ ] A contributor can run the full validation flow with one documented command
- [ ] Developer onboarding is documented

## References

- Section 4 - Technology Stack
- Section 12 - GitHub Workflow Standards Appendix
```

### Phase 4 Issues

---

#### Issue: `feat(export): publish versioned gold exports with schema and freshness metadata`

**Labels:** `feature`, `data`, `phase-4`, `priority:high`
**Milestone:** `Phase 4 - Gold Product and ML Handoff`

**Body:**

```md
## Context

The Gold layer becomes a product only when it is exported in a stable, versioned,
and documented form that downstream systems can depend on.

## Tasks

- [ ] Export selected Gold tables to a versioned folder structure
- [ ] Partition by snapshot date
- [ ] Emit metadata manifest with schema, row counts, and freshness markers
- [ ] Preserve previous successful export versions
- [ ] Add validation that exported totals reconcile with warehouse tables

## Definition of Done

- [ ] Gold exports are reproducible and versioned
- [ ] Metadata manifest exists for every snapshot
- [ ] Exports are safe for downstream automation

## References

- Phase 4 roadmap tasks
- Section 11 - Freshness and Runtime Expectations
```

---

#### Issue: `docs(contract): define downstream ml handoff schema and semantic contract`

**Labels:** `docs`, `data`, `phase-4`, `priority:high`
**Milestone:** `Phase 4 - Gold Product and ML Handoff`

**Body:**

```md
## Context

The second repository should not have to reverse-engineer the meaning of Gold
tables. A formal handoff contract is required.

## Tasks

- [ ] Create `data/contracts/gold_ml_handoff.yml`
- [ ] Document table grain, keys, feature meanings, and accepted value domains
- [ ] Define freshness expectation and backfill behavior
- [ ] Define null handling and default behavior
- [ ] Link the contract in `docs/ml_handoff.md`

## Definition of Done

- [ ] Downstream consumers know exactly what each exported field means
- [ ] Contract includes freshness and schema expectations
- [ ] Changes to Gold exports can be reviewed against a written baseline

## References

- Section 11 - Data Contracts and Quality Standards
- Phase 4 roadmap tasks
```

---

#### Issue: `docs(ml): create bridge documentation for forecasting and mlops bootstrap`

**Labels:** `docs`, `feature`, `phase-4`
**Milestone:** `Phase 4 - Gold Product and ML Handoff`

**Body:**

```md
## Context

The ML repository should start from a concrete downstream plan rather than a vague
handoff. This project must define what gets forecast, how data is consumed, and
what MLOps assumptions are expected.

## Tasks

- [ ] Create `docs/ml_handoff.md`
- [ ] Propose first forecasting targets
- [ ] Define initial train-validation split assumptions
- [ ] Define expected experiment tracking fields for MLflow
- [ ] Document ingestion pattern for Project 2

## Definition of Done

- [ ] Project 2 can start with minimal ambiguity
- [ ] Forecasting targets and feature assumptions are explicit
- [ ] Handoff documentation is portfolio-ready

## References

- Phase 4 roadmap tasks
- Section 1 - Scope Boundary
```

---

#### Issue: `chore(mlops): specify second-repository bootstrap structure and release boundary`

**Labels:** `release`, `docs`, `phase-4`
**Milestone:** `Phase 4 - Gold Product and ML Handoff`

**Body:**

```md
## Context

The first repository should end with a clean boundary. The project needs a written
spec for what belongs in the second repository versus what remains owned here.

## Tasks

- [ ] Document the target repository boundary for Project 2
- [ ] Define which assets remain in this repository and which move downstream
- [ ] Document MLflow expectations at a high level
- [ ] Define release note language for the analytics-to-ML handoff

## Definition of Done

- [ ] Ownership boundary between repos is clear
- [ ] The ML repository bootstrap scope is documented
- [ ] Release notes reflect the handoff cleanly

## References

- Section 1 - Scope Boundary
- Phase 4 roadmap tasks
```

---

#### Issue: `docs(portfolio): finalize architecture runbooks and demo narrative`

**Labels:** `docs`, `release`, `phase-4`
**Milestone:** `Phase 4 - Gold Product and ML Handoff`

**Body:**

```md
## Context

This project is intended to be portfolio-grade. The documentation should tell a
clear story from synthetic billing through Gold export and ML handoff.

## Tasks

- [ ] Finalize `docs/architecture.md`
- [ ] Finalize `docs/accounting_policy.md`
- [ ] Finalize `docs/runbooks/local_execution.md`
- [ ] Add demo walkthrough to `README.md`
- [ ] Add architecture and lineage screenshots if available

## Definition of Done

- [ ] A reviewer can understand the project from docs alone
- [ ] Architecture and execution steps are clearly documented
- [ ] The repository reads as a complete portfolio artifact

## References

- Section 2 - Architecture Overview
- Section 3 - Repository Structure
```

---

#### Issue: `chore(release): create v1.0.0 analytical release after end-to-end validation`

**Labels:** `release`, `phase-4`
**Milestone:** `Phase 4 - Gold Product and ML Handoff`

**Body:**

```md
## Context

The final release should only happen once the full analytics pipeline is stable,
documented, and validated end to end.

## Tasks

- [ ] Ensure all Phase 1-4 issues are closed
- [ ] Ensure all milestones are complete
- [ ] Validate end-to-end run from raw generation to Gold export
- [ ] Create release notes
- [ ] Tag `v1.0.0`
- [ ] Publish GitHub release

## Definition of Done

- [ ] End-to-end validation has passed
- [ ] `v1.0.0` is tagged and released
- [ ] Documentation reflects the final system state

## References

- Section 5 - GitHub Semantic Guide
- Phase 4 roadmap tasks
```
