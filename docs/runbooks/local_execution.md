# Local Execution Runbook

## Generate Synthetic Billing Data

From the repository root:

```bash
finops-generate --days 365 --output-format parquet
```

Optional flags:

- `--run-date YYYY-MM-DD`
- `--sample-size 250`
- `--seed 42`

## Expected Outputs

- partitioned raw billing files in `local_lake/raw/cloud_costs/`
- a manifest in the same partition
- a sample CSV for documentation and lightweight inspection

## Run the Full Local Pipeline

To execute generation, dbt validation, and metadata publication together:

```bash
finops-run-pipeline --days 90
```

Expected additional output:

- `local_lake/metadata/pipeline_runs/run_date=YYYY-MM-DD/run_summary.json`
- refreshed dbt artifacts under `dbt/target/`
- validated warehouse contents in `warehouse/finops.duckdb`
- versioned Gold exports under `local_lake/gold/ml_handoff/version=vX.Y.Z/snapshot_date=YYYY-MM-DD/`

## Export Only

To publish the current warehouse state without rerunning generation and dbt:

```bash
finops-export-gold --snapshot-date 2026-04-06
```

Expected output:

- exported Gold and mart tables in Parquet
- `export_manifest.json` with row counts, schema, and freshness metadata

## Troubleshooting

### Missing Parquet support

Install the project dependencies with:

```bash
pip install -e ".[dev]"
```

### Import errors

Ensure the command is executed from the repository root so `src/` is resolvable.

### dbt profile resolution

If running dbt manually, point the profile directory to the repository-local config:

```bash
export DBT_PROFILES_DIR="$(pwd)/dbt"
```
