-- Receita realizada por origem (grão: cod_ibge × ano × categoria).
-- O layout do RREO mudou em 2018 (ex.: "Transferências Intergovernamentais" foi aberta em
-- União/Estados/Outras). O mapeamento em seed cobre os dois layouts e a diferença para o
-- total vira "Outras receitas", garantindo que as categorias sempre somem o total.
with a1 as (
    select * from {{ ref('int_rreo__anexo01') }}
    where medida in ('receita_realizada', 'receita_prevista_atualizada')
),
total as (
    select cod_ibge, ano,
        max(case when medida = 'receita_realizada' then valor end) as realizado,
        max(case when medida = 'receita_prevista_atualizada' then valor end) as previsto
    from a1 where cod_conta = 'ReceitasExcetoIntraOrcamentarias'
    group by 1, 2
),
mapeado as (
    select a1.cod_ibge, a1.ano, m.categoria, m.grupo, m.ordem,
        sum(case when medida = 'receita_realizada' then valor else 0 end) as realizado,
        sum(case when medida = 'receita_prevista_atualizada' then valor else 0 end) as previsto
    from a1
    join {{ ref('map_receitas_rreo') }} m using (cod_conta)
    group by all
),
residual as (
    select t.cod_ibge, t.ano,
        'Outras receitas' as categoria, 'propria' as grupo, 99 as ordem,
        t.realizado - coalesce(sum(m.realizado), 0) as realizado,
        t.previsto - coalesce(sum(m.previsto), 0) as previsto
    from total t
    left join mapeado m using (cod_ibge, ano)
    group by t.cod_ibge, t.ano, t.realizado, t.previsto
),
unido as (
    select * from mapeado
    union all
    select * from residual
)
select
    u.cod_ibge, u.ano, u.categoria, u.grupo, u.ordem,
    round(u.realizado, 2) as receita_realizada,
    round(u.previsto, 2) as receita_prevista,
    round(u.realizado * f.fator_real, 2) as receita_realizada_real
from unido u
left join {{ ref('int_ipca__fatores') }} f using (ano)
where abs(u.realizado) > 0.005 or abs(u.previsto) > 0.005
