-- Execução orçamentária consolidada por município e ano (grão: cod_ibge × ano).
-- Usa o total "exceto intra-orçamentárias" para não contar duas vezes repasses internos
-- (ex.: contribuição patronal ao instituto de previdência do próprio município).
with a1 as (
    select * from {{ ref('int_rreo__anexo01') }}
),
receita as (
    select cod_ibge, ano,
        max(case when medida = 'receita_prevista_inicial' then valor end) as receita_prevista_inicial,
        max(case when medida = 'receita_prevista_atualizada' then valor end) as receita_prevista_atualizada,
        max(case when medida = 'receita_realizada' then valor end) as receita_realizada
    from a1 where cod_conta = 'ReceitasExcetoIntraOrcamentarias'
    group by 1, 2
),
despesa as (
    select cod_ibge, ano,
        max(case when medida = 'dotacao_inicial' then valor end) as dotacao_inicial,
        max(case when medida = 'dotacao_atualizada' then valor end) as dotacao_atualizada,
        max(case when medida = 'despesa_empenhada' then valor end) as despesa_empenhada,
        max(case when medida = 'despesa_liquidada' then valor end) as despesa_liquidada,
        max(case when medida = 'despesa_paga' then valor end) as despesa_paga
    from a1 where cod_conta = 'DespesasExcetoIntraOrcamentarias'
    group by 1, 2
),
periodo as (
    select cod_ibge, ano, max(periodo) as bimestre_referencia, max(populacao) as populacao
    from a1 group by 1, 2
)
select
    p.cod_ibge,
    p.ano,
    p.bimestre_referencia,
    p.bimestre_referencia = 6 as exercicio_completo,
    p.populacao,
    r.receita_prevista_inicial,
    r.receita_prevista_atualizada,
    r.receita_realizada,
    d.dotacao_inicial,
    d.dotacao_atualizada,
    d.despesa_empenhada,
    d.despesa_liquidada,
    d.despesa_paga,
    r.receita_realizada - d.despesa_liquidada as resultado_orcamentario,
    f.fator_real,
    r.receita_realizada * f.fator_real as receita_realizada_real,
    d.despesa_liquidada * f.fator_real as despesa_liquidada_real,
    r.receita_realizada * f.fator_real / nullif(p.populacao, 0) as receita_per_capita_real,
    d.despesa_liquidada * f.fator_real / nullif(p.populacao, 0) as despesa_per_capita_real
from periodo p
left join receita r using (cod_ibge, ano)
left join despesa d using (cod_ibge, ano)
left join {{ ref('int_ipca__fatores') }} f using (ano)
