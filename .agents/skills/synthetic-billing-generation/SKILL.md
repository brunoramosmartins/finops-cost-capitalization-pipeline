# Synthetic Billing Generation

## When To Use

Use this skill when the task involves:

- synthetic cloud billing generation
- provider-like raw schema design
- seasonality, anomalies, or discount modeling
- batch manifests and local mock lake output

## What To Check First

- `ROADMAP.md`
- `data/contracts/raw_cloud_cost_usage.yml`
- `conf/generator_profiles.yml`
- `src/finops_capex/generators/`
- `src/finops_capex/ingestion/`

## Working Rules

- keep the raw layer provider-like and transformation-light
- document new fields in the raw contract
- preserve deterministic behavior for tests whenever possible
- treat manifest output as part of the data product, not an afterthought

## Expected Outputs

- code changes in generator or ingestion modules
- updated contract or documentation when schema changes
- tests covering shape, coverage, and write-path behavior
