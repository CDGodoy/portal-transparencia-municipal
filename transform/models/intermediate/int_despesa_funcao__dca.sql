-- Despesa por função/subfunção a partir da DCA Anexo I-E (exercícios encerrados).
-- O anexo traz um bloco "exceto intra-orçamentárias" seguido do bloco intra-orçamentário;
-- usamos a ordem original das linhas (preservada na bronze) para descartar o segundo bloco
-- e evitar dupla contagem.
with base as (
    select *
    from {{ ref('stg_siconfi__dca') }}
    where anexo = 'DCA-Anexo I-E'
),
corte as (
    select cod_ibge, ano, coluna, min(ordem) as ordem_intra
    from base
    where conta ilike '%intra%' and conta not ilike '%exceto%'
    group by 1, 2, 3
),
linhas as (
    select b.*
    from base b
    left join corte c using (cod_ibge, ano, coluna)
    where c.ordem_intra is null or b.ordem < c.ordem_intra
),
classificadas as (
    select
        cod_ibge, ano, coluna, valor,
        case
            when regexp_matches(conta, '^\d{2}\.\d{3}\s*-') then 'subfuncao'
            when regexp_matches(conta, '^FU\d{2}\s*-') then 'subfuncao'
            when regexp_matches(conta, '^\d{2}\s*-') then 'funcao'
        end as nivel,
        case
            when regexp_matches(conta, '^FU\d{2}\s*-') then regexp_extract(conta, '^FU(\d{2})', 1)
            when regexp_matches(conta, '^\d{2}') then regexp_extract(conta, '^(\d{2})', 1)
        end as funcao_cod_raw,
        case
            when regexp_matches(conta, '^\d{2}\.\d{3}\s*-') then regexp_extract(conta, '^\d{2}\.(\d{3})', 1)
            when regexp_matches(conta, '^FU\d{2}\s*-') then '999'
        end as subfuncao_cod,
        trim(regexp_replace(conta, '^(FU)?[\d\.]+\s*-\s*', '')) as nome
    from linhas
)
select
    cod_ibge,
    ano,
    nivel,
    nullif(funcao_cod_raw, '') as funcao_cod,
    subfuncao_cod,
    case when subfuncao_cod = '999' then 'Demais subfunções' else max(nome) end as nome,
    sum(case when coluna = 'Despesas Empenhadas' then valor end) as despesa_empenhada,
    sum(case when coluna = 'Despesas Liquidadas' then valor end) as despesa_liquidada,
    sum(case when coluna = 'Despesas Pagas' then valor end) as despesa_paga,
    'DCA' as fonte
from classificadas
where nivel is not null
group by cod_ibge, ano, nivel, funcao_cod_raw, subfuncao_cod
