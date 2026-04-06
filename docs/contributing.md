# Contributing

## Local Setup

1. Create a Python virtual environment.
2. Install runtime dependencies with `pip install -r requirements.txt`.
3. Install development dependencies with `pip install -r requirements-dev.txt`.
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
python scripts/generate_billing_data.py --days 365
```

This command creates:

- raw Parquet files under `local_lake/raw/cloud_costs/run_date=YYYY-MM-DD/`
- a batch manifest JSON file
- a sample CSV file under `data/sample/`

## GitHub Workflow

- issues should be created from the roadmap
- changes should be linked to the correct milestone and phase label
- PR descriptions should include validation details
