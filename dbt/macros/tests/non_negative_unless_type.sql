{% test non_negative_unless_type(model, column_name, type_column, exempt_types) %}
select *
from {{ model }}
where {{ column_name }} < 0
  and coalesce({{ type_column }}, '') not in (
    {% for exempt_type in exempt_types %}
      '{{ exempt_type }}'{% if not loop.last %}, {% endif %}
    {% endfor %}
  )
{% endtest %}
