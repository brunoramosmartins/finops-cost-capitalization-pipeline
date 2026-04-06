# CI/CD Runbook

## Workflow Goals

The repository CI is designed to validate three risk areas on every push and pull request:

- Python quality with `ruff` and `pytest`
- dbt model quality with `sqlfluff`
- end-to-end analytical integrity with generated raw data plus `dbt seed`, `dbt run`, and `dbt test`

## GitHub Actions Jobs

### `python-quality`

- install the project with `pip install -e ".[dev]"`
- run `ruff check .`
- run `pytest`

### `analytics-pipeline`

- install the project with `pip install -e ".[dev]"`
- generate a synthetic raw batch with `finops-generate`
- lint SQL with `sqlfluff`
- import Dagster definitions
- run `dbt debug`
- run `dbt seed`, `dbt run`, and `dbt test`
- run `finops-export-gold` to validate the downstream handoff product

## Local Parity Commands

From the repository root:

```bash
pre-commit run --all-files
finops-run-pipeline --days 90
finops-export-gold --snapshot-date 2026-04-06
```

## Failure Handling

- inspect the failing GitHub Actions step first
- if dbt failed, download the uploaded `dbt-logs` artifact
- review the latest run metadata under `local_lake/metadata/pipeline_runs/`
- reproduce locally using the exact branch state and `finops-run-pipeline`
