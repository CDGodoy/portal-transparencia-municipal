-- Despesa total com pessoal (DTP) x Receita Corrente Líquida e limites da LRF
-- (grão: cod_ibge × ano × periodicidade × período).
-- A coluna percentual mudou de nome ("% sobre a RCL" → "% sobre a RCL Ajustada").
with base as (
    select * from {{ ref('stg_siconfi__rgf') }}
),
pivotado as (
    select
        cod_ibge, ano, periodicidade, periodo,
        max(case when cod_conta = 'DespesaComPessoalTotal' and coluna = 'Valor' then valor end) as dtp,
        max(case when cod_conta = 'DespesaComPessoalTotal' and coluna ilike '% sobre a RCL%' then valor end) as dtp_pct_rcl,
        max(case when cod_conta = 'ReceitaCorrenteLiquidaAjustada' and coluna = 'Valor' then valor end) as rcl_ajustada,
        max(case when cod_conta = 'ReceitaCorrenteLiquidaLimiteLegal' and coluna = 'Valor' then valor end) as rcl,
        max(case when cod_conta = 'LimiteMaximoDespesaComPessoalTotal' and coluna ilike '% sobre a RCL%' then valor end) as limite_maximo_pct,
        max(case when cod_conta = 'LimitePrudencialDespesaComPessoalTotal' and coluna ilike '% sobre a RCL%' then valor end) as limite_prudencial_pct,
        max(case when cod_conta = 'LimiteDeAlertaDespesaComPessoalTotal' and coluna ilike '% sobre a RCL%' then valor end) as limite_alerta_pct
    from base
    group by all
)
select
    cod_ibge, ano, periodicidade, periodo,
    dtp,
    coalesce(rcl_ajustada, rcl) as rcl,
    coalesce(dtp_pct_rcl, round(100 * dtp / nullif(coalesce(rcl_ajustada, rcl), 0), 2)) as dtp_pct_rcl,
    limite_maximo_pct,
    limite_prudencial_pct,
    limite_alerta_pct,
    -- Limites legais para o Executivo municipal (art. 20, III, b e art. 22 da LRF).
    case
        when coalesce(dtp_pct_rcl, 100 * dtp / nullif(coalesce(rcl_ajustada, rcl), 0)) > 54 then 'acima do limite máximo'
        when coalesce(dtp_pct_rcl, 100 * dtp / nullif(coalesce(rcl_ajustada, rcl), 0)) > 51.3 then 'acima do limite prudencial'
        when coalesce(dtp_pct_rcl, 100 * dtp / nullif(coalesce(rcl_ajustada, rcl), 0)) > 48.6 then 'acima do limite de alerta'
        else 'dentro dos limites'
    end as situacao
from pivotado
where dtp is not null
