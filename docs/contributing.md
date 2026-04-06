# Contributing

## Local Setup

1. Create a Python virtual environment.
2. Activate the environment.
3. Install the project in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

4. Install local Git hooks:

```bash
pre-commit install
```

5. Run tests with `pytest`.

## Repository Standards

- Keep documentation aligned with implementation.
- Treat `ROADMAP.md` as the planning source of truth.
- Do not commit local analytical artifacts such as DuckDB databases or generated lake outputs.
- Prefer deterministic generation logic so sample data and tests remain stable.
- Keep assistant-facing guidance in `docs/assistant/` and reusable Codex skills in `.agents/skills/`.

## Phase 1 Workflow

Use the generator script from the repository root:

```bash
finops-generate --days 365
```

This command creates:

- raw Parquet files under `local_lake/raw/cloud_costs/run_date=YYYY-MM-DD/`
- a batch manifest JSON file
- a sample CSV file under `data/sample/`

## Phase 2 Workflow

After generating raw data, run dbt locally:

```bash
export DBT_PROFILES_DIR="$(pwd)/dbt"
dbt seed --project-dir dbt
dbt run --project-dir dbt
dbt test --project-dir dbt
```

The default dbt profile writes to `warehouse/finops.duckdb`.

## Phase 3 Workflow

Use the full local pipeline command when you want generator, dbt, and runtime
metadata to run together:

```bash
finops-run-pipeline --days 90
```

For pre-merge validation:

```bash
pre-commit run --all-files
ruff check .
pytest
```

## Phase 4 Workflow

Use the versioned export command when you want to publish the latest Gold
product for downstream ML consumption:

```bash
finops-export-gold --snapshot-date 2026-04-06
```

This writes:

- versioned Parquet files under `local_lake/gold/ml_handoff/`
- an export manifest with schema, row counts, and freshness metadata

## GitHub Workflow

- issues should be created from the roadmap
- changes should be linked to the correct milestone and phase label
- PR descriptions should include validation details
- CI must stay green for Python quality and analytics pipeline jobs
