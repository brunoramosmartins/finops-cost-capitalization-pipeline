{{ config(materialized="table") }}

select
    batch_id,
    run_date,
    row_count,
    start_date,
    end_date,
    file_format,
    data_file,
    sample_file,
    current_timestamp as ingestion_timestamp
from read_json_auto('{{ var("raw_manifest_glob") }}', union_by_name = true)
