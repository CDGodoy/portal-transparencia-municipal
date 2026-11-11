-- Dimensão de municípios monitorados (seed de configuração + população mais recente).
with pop as (
    select cod_ibge, populacao
    from {{ ref('int_rreo__anexo01') }}
    where populacao is not null
    qualify row_number() over (partition by cod_ibge order by ano desc) = 1
)
select
    m.cod_ibge,
    m.nome,
    m.uf,
    m.cnpj,
    m.slug,
    m.destaque,
    p.populacao as populacao_recente
from {{ ref('municipios') }} m
left join pop p using (cod_ibge)
