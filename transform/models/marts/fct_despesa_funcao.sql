-- Despesa por função de governo (saúde, educação…) e subfunção.
-- Fonte preferencial: DCA (balanço anual, exercício encerrado). Para anos sem DCA
-- (ano corrente), usa o RREO Anexo 02 no bimestre mais recente, só no nível de função.
with dca as (
    select * from {{ ref('int_despesa_funcao__dca') }}
),
rreo as (
    select r.*
    from {{ ref('int_despesa_funcao__rreo') }} r
    where not exists (
        select 1 from dca d where d.cod_ibge = r.cod_ibge and d.ano = r.ano
    )
),
unido as (
    select * from dca
    union all
    select * from rreo
)
select
    u.cod_ibge,
    u.ano,
    u.nivel,
    u.funcao_cod,
    coalesce(fg.funcao_nome, u.nome) as funcao_nome,
    u.subfuncao_cod,
    case when u.nivel = 'subfuncao' then u.nome end as subfuncao_nome,
    u.despesa_empenhada,
    u.despesa_liquidada,
    u.despesa_paga,
    u.despesa_liquidada * f.fator_real as despesa_liquidada_real,
    u.fonte
from unido u
left join {{ ref('funcoes_governo') }} fg using (funcao_cod)
left join {{ ref('int_ipca__fatores') }} f using (ano)
