{{ config(materialized="table") }}

select
    usage.line_item_id,
    usage.billing_period_start_utc,
    usage.usage_start_time_utc,
    usage.usage_end_time_utc,
    usage.invoice_date,
    usage.cloud_provider,
    usage.payer_account_id,
    usage.linked_account_id,
    usage.service,
    policy.service_family,
    usage.usage_type,
    usage.operation,
    usage.region,
    usage.resource_id,
    usage.line_item_type,
    usage.usage_amount,
    usage.currency_code,
    usage.unblended_cost,
    usage.blended_cost,
    usage.discount_type,
    usage.cost_center,
    usage.owner_team,
    usage.environment,
    usage.product_line,
    usage.capitalization_candidate_raw,
    usage.capitalization_candidate_flag,
    usage.initiative_id,
    usage.initiative_stage,
    usage.asset_lifecycle,
    usage.accounting_policy_version,
    usage.generator_batch_id,
    usage.generated_at_utc,
    usage.source_file_name,
    usage.run_date,
    usage.ingestion_timestamp_utc,
    usage.tag_quality_status,
    coalesce(usage.shared_service_flag, false) or coalesce(policy.shared_service_default, false) as shared_service_flag_effective,
    coalesce(policy.shared_service_default, false) as shared_service_default,
    coalesce(policy.capex_service_eligible, false) as capex_service_eligible,
    coalesce(policy.amortization_months_default, 0) as amortization_months_default,
    case
        when usage.line_item_type in ('Credit', 'Discount') then 'billing_adjustment'
        when usage.tag_quality_status = 'invalid_capitalization_flag' then 'invalid_capitalization_metadata'
        when usage.tag_quality_status = 'missing_critical_tags' then 'missing_critical_tags'
        when usage.shared_service_flag or policy.shared_service_default then 'shared_service'
        when
            usage.capitalization_candidate_flag
            and usage.initiative_stage in ('build', 'implementation')
            and coalesce(usage.environment, 'prod') in ('prod', 'staging')
            and coalesce(policy.capex_service_eligible, false)
            then 'direct_build_cost'
        when usage.initiative_stage in ('operate', 'support') then 'operate_support'
        when coalesce(usage.environment, 'prod') in ('sandbox', 'test') then 'non_production'
        else 'other'
    end as accounting_signal
from
    {{ ref('stg_cloud_cost_usage') }} as usage
left join {{ ref('accounting_policy_defaults') }} as policy
    on
        usage.service = policy.service
