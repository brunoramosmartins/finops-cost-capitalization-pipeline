# Architecture

## Phase 1 Scope

Phase 1 establishes the repository foundation and the synthetic data generation
layer required for the rest of the pipeline.

Current implemented building blocks:

- repository-level standards and contribution guidance
- assistant guidance in `docs/assistant/`
- Codex-oriented reusable skills in `.agents/skills/`
- synthetic billing generator implemented in Python
- local mock data lake writer with batch manifest output
- raw data contract for downstream Bronze ingestion

## Data Flow

```text
YAML profile -> Python generator -> pandas DataFrame -> local_lake/raw partition
                                         |
                                         +-> sample CSV + manifest
```

## Next Architectural Step

Phase 2 will consume the generated raw files from `local_lake/raw/cloud_costs/`
and load them into DuckDB through dbt Bronze models.
