-- Fatores para converter valores nominais de cada ano em reais do último mês disponível.
-- Fluxos anuais (receitas e despesas) são deflacionados pelo índice MÉDIO do ano.
with indice as (
    select
        mes,
        exp(sum(ln(1 + variacao)) over (order by mes rows unbounded preceding)) as indice
    from {{ ref('stg_bcb__ipca') }}
),
referencia as (
    select mes as mes_referencia, indice as indice_referencia
    from indice
    order by mes desc
    limit 1
),
anual as (
    select year(mes) as ano, avg(indice) as indice_medio
    from indice
    group by 1
)
select
    a.ano,
    r.indice_referencia / a.indice_medio as fator_real,
    r.mes_referencia
from anual a
cross join referencia r
