with usage_counts as (
    select
        generator_batch_id as batch_id,
        count(*) as usage_row_count
    from {{ ref('brz_cloud_cost_usage') }}
    group by 1
)

select
    manifest.batch_id,
    manifest.row_count as manifest_row_count,
    usage_counts.usage_row_count
from
    {{ ref('brz_generation_manifest') }} as manifest
left join usage_counts
    on
        manifest.batch_id = usage_counts.batch_id
where
    usage_counts.batch_id is null
    or manifest.row_count <> usage_counts.usage_row_count
