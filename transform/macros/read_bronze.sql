{#
  Lê um dataset da camada bronze (NDJSON.gz) com um CONTRATO DE SCHEMA explícito.

  - `columns` define nome -> tipo DuckDB: campos novos que a API passar a enviar são
    ignorados e campos ausentes viram NULL, então mudanças de layout não quebram o pipeline.
  - Se ainda não houver arquivos (ex.: primeira execução sem PNCP), devolve uma relação vazia
    com o mesmo schema, em vez de falhar.
#}
{% macro read_bronze(source, dataset, columns) %}
  {%- set pattern = var('bronze_dir') ~ '/' ~ source ~ '/' ~ dataset ~ '/**/*.ndjson.gz' -%}
  {%- set has_files = true -%}
  {%- if execute -%}
    {%- set res = run_query("select count(*) from glob('" ~ pattern ~ "')") -%}
    {%- set has_files = res.columns[0].values()[0] > 0 -%}
  {%- endif -%}
  {%- if has_files -%}
    select *
    from read_json(
      '{{ pattern }}',
      format = 'newline_delimited',
      columns = {
        {%- for name, type in columns.items() %}
        '{{ name }}': '{{ type }}'{{ "," if not loop.last }}
        {%- endfor %}
      },
      filename = true,
      hive_partitioning = false
    )
  {%- else -%}
    select
      {%- for name, type in columns.items() %}
      cast(null as {{ type }}) as "{{ name }}",
      {%- endfor %}
      cast(null as varchar) as filename
    where false
  {%- endif -%}
{% endmacro %}
