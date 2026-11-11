-- Despesa por função a partir do RREO Anexo 02, usada para anos ainda sem DCA (ano corrente).
-- O anexo não traz o código da função; casamos o nome com a tabela oficial de funções
-- (sem acentos e sem diferenciar caixa).
with base as (
    select *
    from {{ ref('stg_siconfi__rreo') }}
    where anexo = 'RREO-Anexo 02'
      and rotulo ilike '%exceto%'
),
vigente as (
    select cod_ibge, ano, max(periodo) as periodo from base group by 1, 2
),
funcoes as (
    select funcao_cod, funcao_nome, lower(strip_accents(funcao_nome)) as chave
    from {{ ref('funcoes_governo') }}
)
select
    b.cod_ibge,
    b.ano,
    'funcao' as nivel,
    f.funcao_cod,
    cast(null as varchar) as subfuncao_cod,
    f.funcao_nome as nome,
    max(case when b.coluna ilike 'DESPESAS EMPENHADAS ATÉ%' then b.valor end) as despesa_empenhada,
    max(case when b.coluna ilike 'DESPESAS LIQUIDADAS ATÉ%' then b.valor end) as despesa_liquidada,
    cast(null as double) as despesa_paga,
    'RREO' as fonte
from base b
join vigente v using (cod_ibge, ano, periodo)
join funcoes f on lower(strip_accents(trim(b.conta))) = f.chave
group by all
