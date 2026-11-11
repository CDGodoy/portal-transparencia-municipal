-- Despesa liquidada por grupo de natureza (grão: cod_ibge × ano × grupo_natureza).
select
    a1.cod_ibge,
    a1.ano,
    m.grupo_natureza,
    m.ordem,
    max(case when medida = 'dotacao_atualizada' then valor end) as dotacao_atualizada,
    max(case when medida = 'despesa_liquidada' then valor end) as despesa_liquidada,
    max(case when medida = 'despesa_liquidada' then valor end) * max(f.fator_real) as despesa_liquidada_real
from {{ ref('int_rreo__anexo01') }} a1
join {{ ref('map_despesas_natureza') }} m using (cod_conta)
left join {{ ref('int_ipca__fatores') }} f using (ano)
group by all
