{{ config(materialized="table") }}

select
    cast(date_trunc('month', usage_start_time_utc) as date) as billing_month,
    owner_team,
    product_line,
    classification_status,
    count(*) as line_item_count,
    sum(unblended_cost) as total_unblended_cost,
    sum(blended_cost) as total_blended_cost,
    sum(case when review_required_flag then unblended_cost else 0 end) as review_cost_total,
    sum(case when classification_status = 'capex_eligible' then unblended_cost else 0 end) as capex_eligible_cost_total,
    sum(case when classification_status = 'opex' then unblended_cost else 0 end) as opex_cost_total
from {{ ref('fct_cost_classification') }}
group by 1, 2, 3, 4
