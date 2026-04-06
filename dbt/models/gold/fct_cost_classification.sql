{{ config(materialized="table") }}

select
    line_item_id,
    billing_period_start_utc,
    usage_start_time_utc,
    usage_end_time_utc,
    invoice_date,
    cloud_provider,
    payer_account_id,
    linked_account_id,
    service,
    service_family,
    usage_type,
    operation,
    region,
    resource_id,
    line_item_type,
    usage_amount,
    currency_code,
    unblended_cost,
    blended_cost,
    discount_type,
    cost_center,
    owner_team,
    environment,
    product_line,
    capitalization_candidate_flag,
    initiative_id,
    initiative_stage,
    asset_lifecycle,
    accounting_policy_version as policy_version,
    generator_batch_id,
    generated_at_utc,
    run_date,
    tag_quality_status,
    shared_service_flag_effective as shared_service_flag,
    capex_service_eligible,
    amortization_months_default,
    accounting_signal,
    case
        when accounting_signal = 'direct_build_cost' then 'capex_eligible'
        when accounting_signal = 'shared_service' then 'shared_cost_review'
        when accounting_signal in ('billing_adjustment', 'operate_support', 'non_production') then 'opex'
        when accounting_signal in ('invalid_capitalization_metadata', 'missing_critical_tags') then 'unclassified'
        else 'opex'
    end as classification_status,
    case
        when accounting_signal = 'direct_build_cost' then 'capitalization_candidate_with_build_stage_and_eligible_service'
        when accounting_signal = 'shared_service' then 'shared_or_platform_cost_requires_review'
        when accounting_signal = 'billing_adjustment' then 'discount_or_credit_treated_as_operational_adjustment'
        when accounting_signal = 'operate_support' then 'operate_or_support_stage_defaults_to_opex'
        when accounting_signal = 'non_production' then 'sandbox_or_test_environment_defaults_to_opex'
        when accounting_signal = 'invalid_capitalization_metadata' then 'capitalization_flag_is_invalid'
        when accounting_signal = 'missing_critical_tags' then 'initiative_or_owner_metadata_missing'
        else 'default_operational_treatment'
    end as classification_reason,
    case
        when accounting_signal = 'direct_build_cost' then false
        when accounting_signal = 'shared_service' then true
        when accounting_signal in ('invalid_capitalization_metadata', 'missing_critical_tags') then true
        else false
    end as review_required_flag
from {{ ref('int_cost_enriched') }}
