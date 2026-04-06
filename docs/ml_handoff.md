# ML Handoff

## Purpose

Phase 4 turns the Gold layer into a versioned data product that a second
repository can consume without reverse-engineering this analytics codebase.

This document defines:

- which exported tables form the downstream interface
- which forecasting targets are recommended first
- how the second repository should be bootstrapped
- where the ownership boundary between repositories sits

## Exported Product

The formal contract lives in
[`data/contracts/gold_ml_handoff.yml`](../data/contracts/gold_ml_handoff.yml).

Exports are written under:

```text
local_lake/gold/ml_handoff/
  version=vX.Y.Z/
    snapshot_date=YYYY-MM-DD/
      analytics_gold/
      analytics_marts/
      export_manifest.json
```

The initial exported relations are:

- `analytics_gold.fct_cost_classification`
- `analytics_gold.fct_capex_candidate_costs`
- `analytics_marts.mart_monthly_finops_summary`
- `analytics_marts.mart_capitalization_waterfall`

## Recommended Forecasting Targets

The strongest starting point for Project 2 is monthly forecasting over the marts
rather than line-item forecasting.

Recommended first targets:

- `total_unblended_cost` by `billing_month`, `owner_team`, and `classification_status`
- `capex_eligible_cost_total` by `billing_month` and `owner_team`
- `review_cost_total` to predict upcoming manual review load

Why this is the right starting point:

- the data is already aggregated and reconciled
- the signal is less sparse than line-item exports
- it aligns with how finance and FinOps stakeholders consume the output

## Suggested Repository Boundary

This repository owns:

- synthetic raw data generation
- Bronze, Silver, Gold, and marts logic
- accounting policy logic and explainability
- export layout, manifests, and semantic contracts

The second repository should own:

- feature loading from the exported snapshot folders
- train and validation split policy
- model architecture and hyperparameter search
- MLflow experiment tracking
- model packaging, registry, and deployment

## Suggested Project 2 Bootstrap

Recommended top-level structure:

```text
finops-cost-forecasting-ml/
  conf/
  data_access/
  features/
  models/
  training/
  evaluation/
  serving/
  notebooks/
  tests/
  mlruns/ or MLflow backend config
  README.md
```

## Initial Modeling Path

Start simple before reaching for deep learning.

Recommended progression:

1. baseline seasonal naive forecast on `mart_monthly_finops_summary`
2. tree-based regressor or linear model with lag features
3. PyTorch temporal model only after the baseline is clearly documented

## MLflow Expectations

At minimum, Project 2 should track:

- export version consumed
- snapshot date consumed
- target definition
- feature set version
- model family
- train and validation date range
- error metrics such as MAE, RMSE, and MAPE

## Change Management

Any breaking schema or semantic change to the exported Gold product should be handled by:

1. updating `data/contracts/gold_ml_handoff.yml`
2. documenting the change in this handoff file
3. issuing a new prerelease tag for the analytics repository

That keeps the downstream ML repository pinned to an explicit export version.
