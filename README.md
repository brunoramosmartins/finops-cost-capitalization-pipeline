# finops-cost-capitalization-pipeline

Portfolio-grade Analytics Engineering project that simulates cloud billing data,
builds a local-first FinOps pipeline, and prepares the foundation for OPEX versus
CAPEX-oriented cost classification.

## Current Status

Phase 1 is implemented as the repository foundation and synthetic data generation
layer. The project currently provides:

- a documented repository structure and contribution workflow
- assistant guidance under `docs/assistant/`
- project-specific Codex skills under `.agents/skills/`
- a synthetic cloud billing generator implemented in Python
- partitioned raw output in a mock local data lake
- a raw data contract for downstream Bronze ingestion

## Quick Start

1. Create a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements-dev.txt
```

3. Generate a raw synthetic billing batch:

```bash
python scripts/generate_billing_data.py --days 365 --output-format parquet
```

4. Run tests:

```bash
pytest
```

## Repository Guide

- [ROADMAP.md](ROADMAP.md): full phased project plan
- [docs/architecture.md](docs/architecture.md): architectural notes
- [docs/contributing.md](docs/contributing.md): local development workflow
- [docs/assistant/project_context.md](docs/assistant/project_context.md): assistant-facing project context
- [data/contracts/raw_cloud_cost_usage.yml](data/contracts/raw_cloud_cost_usage.yml): raw data contract

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full project plan, including phases,
milestones, issue catalog, architecture, and the ML handoff strategy.

## GitHub Bootstrap

Use the Bash automation scripts to prepare the remote GitHub repository with
labels, milestones, and issues derived from the roadmap.

```bash
bash scripts/setup_labels.sh --repo owner/repo
bash scripts/setup_milestones.sh --repo owner/repo
bash scripts/setup_issues.sh --repo owner/repo
bash scripts/setup_all.sh --repo owner/repo
```

The issue bootstrap reads the issue catalog directly from `ROADMAP.md`, so the
roadmap remains the single source of truth for backlog creation.
