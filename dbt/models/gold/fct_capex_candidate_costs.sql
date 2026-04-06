{{ config(materialized="table") }}

select
    line_item_id,
    usage_start_time_utc,
    linked_account_id,
    service,
    service_family,
    owner_team,
    product_line,
    initiative_id,
    initiative_stage,
    asset_lifecycle,
    policy_version,
    amortization_months_default,
    unblended_cost,
    blended_cost,
    classification_reason
from {{ ref('fct_cost_classification') }}
where classification_status = 'capex_eligible'
