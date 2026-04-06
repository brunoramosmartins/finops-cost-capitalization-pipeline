with gold_aggregated as (
    select
        cast(date_trunc('month', usage_start_time_utc) as date) as billing_month,
        owner_team,
        product_line,
        classification_status,
        count(*) as expected_line_item_count,
        sum(unblended_cost) as expected_total_unblended_cost
    from {{ ref('fct_cost_classification') }}
    group by 1, 2, 3, 4
)

select
    mart.billing_month,
    mart.owner_team,
    mart.product_line,
    mart.classification_status,
    mart.line_item_count,
    gold_aggregated.expected_line_item_count,
    mart.total_unblended_cost,
    gold_aggregated.expected_total_unblended_cost
from {{ ref('mart_monthly_finops_summary') }} as mart
left join gold_aggregated
    on mart.billing_month = gold_aggregated.billing_month
   and coalesce(mart.owner_team, '') = coalesce(gold_aggregated.owner_team, '')
   and coalesce(mart.product_line, '') = coalesce(gold_aggregated.product_line, '')
   and mart.classification_status = gold_aggregated.classification_status
where gold_aggregated.billing_month is null
   or mart.line_item_count <> gold_aggregated.expected_line_item_count
   or abs(mart.total_unblended_cost - gold_aggregated.expected_total_unblended_cost) > 0.0001
