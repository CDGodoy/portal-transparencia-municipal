-- Anexo 01 do RREO no bimestre mais recente disponível de cada ano, com as colunas do
-- relatório normalizadas para medidas estáveis. Os rótulos das colunas mudam entre layouts
-- (ex.: "(a)", "(e)", "(h)"), então casamos pelo prefixo.
with base as (
    select * from {{ ref('stg_siconfi__rreo') }}
    where anexo = 'RREO-Anexo 01'
),
vigente as (
    select cod_ibge, ano, max(periodo) as periodo
    from base
    group by 1, 2
),
medidas as (
    select
        b.cod_ibge,
        b.ano,
        b.periodo,
        b.populacao,
        b.cod_conta,
        b.conta,
        case
            when b.coluna ilike 'PREVISÃO INICIAL%' then 'receita_prevista_inicial'
            when b.coluna ilike 'PREVISÃO ATUALIZADA%' then 'receita_prevista_atualizada'
            when b.coluna ilike 'Até o Bimestre%' then 'receita_realizada'
            when b.coluna ilike 'DOTAÇÃO INICIAL%' then 'dotacao_inicial'
            when b.coluna ilike 'DOTAÇÃO ATUALIZADA%' then 'dotacao_atualizada'
            when b.coluna ilike 'DESPESAS EMPENHADAS ATÉ%' then 'despesa_empenhada'
            when b.coluna ilike 'DESPESAS LIQUIDADAS ATÉ%' then 'despesa_liquidada'
            when b.coluna ilike 'DESPESAS PAGAS ATÉ%' then 'despesa_paga'
        end as medida,
        b.valor
    from base b
    join vigente v using (cod_ibge, ano, periodo)
)
select
    cod_ibge, ano, periodo, cod_conta, medida,
    max(conta) as conta,
    max(populacao) as populacao,
    -- a mesma conta não deve se repetir; se repetir, os valores são iguais
    max(valor) as valor
from medidas
where medida is not null
group by all
