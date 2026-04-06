# Incident Response Runbook

## Purpose

This runbook describes how to investigate a failed local or CI pipeline run.

## Primary Investigation Artifacts

- latest raw manifest under `local_lake/raw/cloud_costs/run_date=YYYY-MM-DD/manifest.json`
- latest pipeline run summary under `local_lake/metadata/pipeline_runs/run_date=YYYY-MM-DD/run_summary.json`
- dbt logs under `dbt/logs/dbt.log`
- dbt execution artifacts under `dbt/target/`
- local warehouse file at `warehouse/finops.duckdb`

## Investigation Sequence

1. Confirm the failing stage from `run_summary.json`.
2. If generation failed, validate the generator profile and raw output paths.
3. If dbt failed, inspect `dbt/logs/dbt.log` and the compiled SQL under `dbt/target/compiled/`.
4. If data quality failed, query the affected model directly in DuckDB.
5. Confirm whether the issue is code, configuration, or data-shape related.

## Useful Validation Commands

```bash
python -c "import json; from pathlib import Path; print(json.loads(Path('local_lake/metadata/pipeline_runs').glob('run_date=*/run_summary.json').__iter__().__next__().read_text()))"
python -c "import duckdb; con=duckdb.connect('warehouse/finops.duckdb'); print(con.execute('show all tables').fetchdf().to_string(index=False))"
```

## Typical Failure Classes

- raw files missing: generator did not produce the expected partition
- dbt parse or lint failure: SQL structure or templating regression
- dbt model failure: schema, path, or SQL logic regression
- dbt test failure: business rule or data contract regression
- warehouse mismatch: Bronze and Gold counts or mart reconciliations diverged
