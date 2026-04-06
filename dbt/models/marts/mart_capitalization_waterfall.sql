{{ config(materialized="table") }}

select
    cast(date_trunc('month', usage_start_time_utc) as date) as billing_month,
    service_family,
    classification_status,
    classification_reason,
    count(*) as line_item_count,
    sum(unblended_cost) as total_unblended_cost,
    sum(blended_cost) as total_blended_cost
from {{ ref('fct_cost_classification') }}
group by 1, 2, 3, 4
