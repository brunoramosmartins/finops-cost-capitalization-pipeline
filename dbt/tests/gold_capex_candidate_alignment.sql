select
    candidate.line_item_id,
    classification.classification_status
from
    {{ ref('fct_capex_candidate_costs') }} as candidate
left join {{ ref('fct_cost_classification') }} as classification
    on
        candidate.line_item_id = classification.line_item_id
where
    classification.line_item_id is null
    or classification.classification_status <> 'capex_eligible'
