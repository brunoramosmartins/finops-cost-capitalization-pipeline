# Contributing

## Local Setup

1. Create a Python virtual environment.
2. Activate the environment.
3. Install the project in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

4. Run tests with `pytest`.

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
export DBT_PROFILES_DIR=dbt
dbt seed --project-dir dbt
dbt run --project-dir dbt
dbt test --project-dir dbt
```

The default dbt profile writes to `warehouse/finops.duckdb`.

## GitHub Workflow

- issues should be created from the roadmap
- changes should be linked to the correct milestone and phase label
- PR descriptions should include validation details
