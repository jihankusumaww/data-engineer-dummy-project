{% macro cents_to_dollars(column_name, precision=2) %}
    round(({{ column_name }}::double) / 100, {{ precision }})
{% endmacro %}
