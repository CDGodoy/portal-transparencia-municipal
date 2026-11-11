-- Na DCA, a soma das subfunções deve bater com o valor da função (tolerância de R$ 1).
{{ config(severity='warn') }}
with f as (
    select cod_ibge, ano, funcao_cod, despesa_liquidada
    from {{ ref('fct_despesa_funcao') }}
    where nivel = 'funcao' and fonte = 'DCA'
),
s as (
    select cod_ibge, ano, funcao_cod, sum(despesa_liquidada) as soma
    from {{ ref('fct_despesa_funcao') }}
    where nivel = 'subfuncao' and fonte = 'DCA'
    group by 1, 2, 3
)
select f.*, s.soma
from f join s using (cod_ibge, ano, funcao_cod)
where abs(f.despesa_liquidada - s.soma) > 1
