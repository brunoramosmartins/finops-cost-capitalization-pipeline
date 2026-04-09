# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versioning aligns with [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for the Python package and export contract labels.

## [Unreleased]

### Added

- Pytest integration smoke that runs `dbt seed`, `dbt run`, and `dbt test` against an isolated DuckDB file and a synthetic Parquet batch (see `tests/integration/test_dbt_pipeline_e2e.py`).
- Optional `FINOPS_DUCKDB_PATH` environment variable in `dbt/profiles.yml` to override the DuckDB file path (default remains `warehouse/finops.duckdb` relative to the repository root when you run dbt from that root).
- `pythonpath = ["."]` in pytest configuration so `orchestration.*` imports resolve consistently (including Windows).

### Fixed

- Gold exporter unit test no longer asserts a 24-hour freshness window against fixed fixture timestamps (avoids failures when the calendar moves forward).

## [0.4.0] - 2026-04-06

### Summary

- Local-first FinOps pipeline: synthetic billing, Bronze/Silver/Gold dbt models, versioned Gold export for ML handoff, Dagster job definitions, and CI across Python, SQL, and dbt.

### Contracts

- Raw billing shape: [`data/contracts/raw_cloud_cost_usage.yml`](data/contracts/raw_cloud_cost_usage.yml).
- Gold ML handoff: [`data/contracts/gold_ml_handoff.yml`](data/contracts/gold_ml_handoff.yml).

**Breaking changes** to those YAML contracts or to exported table lists in `conf/pipeline.yml` / `finops_capex` should bump the package version and be called out under `## [x.y.z]` with a `### Changed` or `### Removed` subsection.
