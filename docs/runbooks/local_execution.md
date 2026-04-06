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

## Troubleshooting

### Missing Parquet support

Install the project dependencies with:

```bash
pip install -e ".[dev]"
```

### Import errors

Ensure the command is executed from the repository root so `src/` is resolvable.
