-- Contratos (PNCP) por município — grão: contrato.
select
    c.numero_controle_pncp,
    c.cod_ibge,
    coalesce(year(c.data_assinatura), c.ano_contrato) as ano,
    c.data_assinatura,
    c.vigencia_inicio,
    c.vigencia_fim,
    c.fornecedor_documento,
    c.fornecedor_nome,
    c.fornecedor_tipo_pessoa,
    coalesce(c.categoria, 'Não informado') as categoria,
    c.tipo_contrato,
    c.objeto,
    c.valor_global,
    c.valor_global * f.fator_real as valor_global_real,
    c.unidade_nome
from {{ ref('stg_pncp__contratos') }} c
left join {{ ref('int_ipca__fatores') }} f on f.ano = coalesce(year(c.data_assinatura), c.ano_contrato)
where c.valor_global is not null
