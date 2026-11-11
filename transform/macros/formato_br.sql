{# Formata número no padrão brasileiro dentro do SQL: 1234567.8 -> '1.234.567,8' #}
{% macro numero_br(expr, casas=0) -%}
replace(replace(replace(printf('%,.{{ casas }}f', {{ expr }}), ',', '#'), '.', ','), '#', '.')
{%- endmacro %}
