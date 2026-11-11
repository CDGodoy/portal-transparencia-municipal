-- Indicadores comparáveis entre municípios (grão: cod_ibge × ano). Valores per capita em
-- reais constantes; participações em % da despesa liquidada ou da receita realizada.
with ex as (
    select * from {{ ref('fct_execucao_anual') }}
),
nat as (
    select cod_ibge, ano,
        sum(case when grupo_natureza = 'Pessoal e encargos' then despesa_liquidada end) as pessoal,
        sum(case when grupo_natureza like 'Investimentos%' then despesa_liquidada end) as investimentos
    from {{ ref('fct_despesa_natureza') }}
    group by 1, 2
),
fun as (
    select cod_ibge, ano,
        sum(case when funcao_cod = '10' then despesa_liquidada end) as saude,
        sum(case when funcao_cod = '12' then despesa_liquidada end) as educacao,
        sum(despesa_liquidada) as total_funcoes
    from {{ ref('fct_despesa_funcao') }}
    where nivel = 'funcao'
    group by 1, 2
),
rec as (
    select cod_ibge, ano,
        sum(case when grupo = 'transferencia' then receita_realizada end) as transferencias,
        sum(case when grupo = 'propria' then receita_realizada end) as propria
    from {{ ref('fct_receita_origem') }}
    group by 1, 2
),
lrf as (
    select cod_ibge, ano, dtp_pct_rcl
    from {{ ref('fct_pessoal_lrf') }}
    qualify row_number() over (partition by cod_ibge, ano order by periodo desc) = 1
)
select
    ex.cod_ibge,
    ex.ano,
    ex.exercicio_completo,
    ex.populacao,
    round(ex.receita_per_capita_real, 2) as receita_per_capita_real,
    round(ex.despesa_per_capita_real, 2) as despesa_per_capita_real,
    round(100 * nat.pessoal / nullif(ex.despesa_liquidada, 0), 2) as pct_pessoal,
    round(100 * nat.investimentos / nullif(ex.despesa_liquidada, 0), 2) as pct_investimento,
    round(100 * fun.saude / nullif(coalesce(fun.total_funcoes, ex.despesa_liquidada), 0), 2) as pct_saude,
    round(100 * fun.educacao / nullif(coalesce(fun.total_funcoes, ex.despesa_liquidada), 0), 2) as pct_educacao,
    round(100 * rec.transferencias / nullif(ex.receita_realizada, 0), 2) as pct_dependencia_transferencias,
    round(100 * rec.propria / nullif(ex.receita_realizada, 0), 2) as pct_receita_propria,
    round(lrf.dtp_pct_rcl, 2) as pct_pessoal_rcl,
    round(100 * ex.resultado_orcamentario / nullif(ex.receita_realizada, 0), 2) as pct_resultado_orcamentario
from ex
left join nat using (cod_ibge, ano)
left join fun using (cod_ibge, ano)
left join rec using (cod_ibge, ano)
left join lrf using (cod_ibge, ano)
