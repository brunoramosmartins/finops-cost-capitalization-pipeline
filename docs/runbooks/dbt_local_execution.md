# dbt Local Execution

## Prerequisites

- install the project with `pip install -e ".[dev]"`
- generate at least one raw synthetic billing batch

## Recommended Commands

From the repository root:

```bash
export DBT_PROFILES_DIR=dbt
dbt seed --project-dir dbt
dbt run --project-dir dbt --select bronze
dbt run --project-dir dbt --select silver
dbt run --project-dir dbt --select gold marts
dbt test --project-dir dbt
```

## Expected Local Output

- DuckDB database file at `warehouse/finops.duckdb`
- Bronze, Silver, Gold, and mart schemas materialized inside DuckDB
- seed-backed accounting defaults loaded into the `reference` schema

## Notes

- Bronze reads directly from Parquet files in `local_lake/raw/cloud_costs/`
- the default dbt vars expect Phase 1 outputs in Parquet format
- if no raw Parquet files exist, Bronze models will fail as expected
