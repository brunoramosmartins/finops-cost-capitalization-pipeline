# FinOps Accounting Review

## When To Use

Use this skill when the task involves:

- OPEX versus CAPEX recommendation logic
- accounting-related tag interpretation
- review of Gold classification rules
- finance-facing documentation of rule rationale

## What To Check First

- `ROADMAP.md`
- `docs/accounting_policy.md`
- `conf/accounting_policy.yml`
- Gold model specifications and tests

## Working Rules

- frame outputs as accounting recommendations, not authoritative accounting conclusions
- require explicit rationale for classification rules
- distinguish shared-cost review cases from true direct-capex candidates
- document policy versioning whenever rule behavior changes

## Expected Outputs

- clarified rule logic
- policy documentation updates
- test coverage for classification domains and edge cases
