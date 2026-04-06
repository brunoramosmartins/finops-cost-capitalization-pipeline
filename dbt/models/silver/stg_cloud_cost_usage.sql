{{ config(materialized="table") }}

with normalized as (
    select
        line_item_id,
        cast(billing_period_start as timestamp) as billing_period_start_utc,
        cast(usage_start_time as timestamp) as usage_start_time_utc,
        cast(usage_end_time as timestamp) as usage_end_time_utc,
        cast(invoice_date as date) as invoice_date,
        lower(trim(cloud_provider)) as cloud_provider,
        trim(payer_account_id) as payer_account_id,
        trim(linked_account_id) as linked_account_id,
        trim(service) as service,
        trim(usage_type) as usage_type,
        trim(operation) as operation,
        lower(trim(region)) as region,
        trim(resource_id) as resource_id,
        trim(line_item_type) as line_item_type,
        cast(usage_amount as double) as usage_amount,
        upper(trim(currency_code)) as currency_code,
        cast(unblended_cost as double) as unblended_cost,
        cast(blended_cost as double) as blended_cost,
        lower(trim(coalesce(discount_type, 'none'))) as discount_type,
        nullif(trim(cost_center), '') as cost_center,
        nullif(trim(owner_team), '') as owner_team,
        lower(nullif(trim(environment), '')) as environment,
        lower(nullif(trim(product_line), '')) as product_line,
        lower(nullif(trim(capitalization_candidate), '')) as capitalization_candidate_raw,
        nullif(trim(initiative_id), '') as initiative_id,
        lower(nullif(trim(initiative_stage), '')) as initiative_stage,
        lower(nullif(trim(asset_lifecycle), '')) as asset_lifecycle,
        trim(accounting_policy_version) as accounting_policy_version,
        trim(generator_batch_id) as generator_batch_id,
        cast(generated_at as timestamp) as generated_at_utc,
        source_file_name,
        cast(run_date as date) as run_date,
        cast(ingestion_timestamp as timestamp) as ingestion_timestamp_utc
    from {{ ref('brz_cloud_cost_usage') }}
)

select
    *,
    case
        when capitalization_candidate_raw = 'true' then true
        when capitalization_candidate_raw = 'false' then false
        else null
    end as capitalization_candidate_flag,
    case
        when owner_team is null or initiative_id is null then 'missing_critical_tags'
        when capitalization_candidate_raw is not null and capitalization_candidate_raw not in ('true', 'false') then 'invalid_capitalization_flag'
        when environment is null then 'missing_environment'
        else 'complete'
    end as tag_quality_status,
    case
        when service in ('AWSDataTransfer', 'AWSSupport') then true
        when owner_team = 'core-infra' then true
        else false
    end as shared_service_flag
from normalized
