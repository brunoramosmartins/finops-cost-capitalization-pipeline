# dbt Model Authoring

## When To Use

Use this skill when the task involves:

- Bronze, Silver, or Gold dbt model creation
- source definitions and schema YAML
- tests, descriptions, and lineage-oriented model design

## What To Check First

- `ROADMAP.md`
- `docs/accounting_policy.md`
- `data/contracts/`
- `dbt/` project structure

## Working Rules

- make model grain explicit
- document assumptions in schema YAML
- add tests for keys, accepted values, and important nullability constraints
- avoid embedding unclear accounting assumptions without documenting them

## Expected Outputs

- dbt SQL model changes
- schema YAML updates
- documentation and tests aligned with the transformation
