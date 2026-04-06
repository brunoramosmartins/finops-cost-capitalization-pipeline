{{ config(materialized="table") }}

select
    line_item_id,
    cost_center,
    owner_team,
    environment,
    product_line,
    capitalization_candidate_raw,
    capitalization_candidate_flag,
    initiative_id,
    initiative_stage,
    asset_lifecycle,
    accounting_policy_version,
    tag_quality_status,
    shared_service_flag
from {{ ref('stg_cloud_cost_usage') }}
