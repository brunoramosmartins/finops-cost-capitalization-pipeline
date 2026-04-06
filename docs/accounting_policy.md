# Accounting Policy Notes

This repository encodes an **accounting recommendation layer**, not an
authoritative accounting determination. The objective is to make Gold outputs
explainable and reviewable by finance stakeholders.

## Inputs Used by the Recommendation Layer

- `capitalization_candidate`
- `initiative_id`
- `initiative_stage`
- `asset_lifecycle`
- `environment`
- `owner_team`
- `service`
- `accounting_policy_version`

## Phase 2 Rule Shape

The first Gold rule set follows these principles:

- direct build-oriented costs can become `capex_eligible`
- shared platform and shared support costs become `shared_cost_review`
- sandbox, test, operate, and support-oriented costs default to `opex`
- invalid or incomplete capitalization metadata becomes `unclassified`

## Current Service Defaults

The repository seed `dbt/seeds/accounting_policy_defaults.csv` defines a small
service-level policy layer used by Gold transformations:

- `AmazonEC2`: eligible when tags and initiative stage support capitalization
- `AmazonS3`: eligible when tags and initiative stage support capitalization
- `AmazonRDS`: eligible when tags and initiative stage support capitalization
- `AWSDataTransfer`: shared by default
- `AWSSupport`: shared by default

## Review Guidance

Treat Gold outputs as:

- analytically useful
- reproducible
- explainable
- reviewable

Do not treat them as a substitute for official accounting policy approval.
