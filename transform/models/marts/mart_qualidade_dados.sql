-- Achados de qualidade de dados exibidos publicamente no portal ("Sobre os dados").
-- Os dados vêm declarados pelos próprios municípios; inconsistências aqui não significam
-- irregularidade, apenas que o número deve ser lido com cautela.
{% set tol = var('tolerancia_reconciliacao') %}
with ex as (
    select * from {{ ref('fct_execucao_anual') }}
),
ano_atual as (
    select max(ano) as ano_max from ex
),
dca_total as (
    select cod_ibge, ano, sum(despesa_liquidada) as liquidada_dca
    from {{ ref('fct_despesa_funcao') }}
    where nivel = 'funcao' and fonte = 'DCA'
    group by 1, 2
),
achados as (
    -- 1. RREO x DCA: o mesmo total declarado em dois relatórios deveria bater.
    select ex.cod_ibge, ex.ano, 'aviso' as severidade, 'reconciliacao_rreo_dca' as regra,
        'Despesa liquidada difere ' || {{ numero_br('100 * abs(ex.despesa_liquidada - d.liquidada_dca) / ex.despesa_liquidada', 1) }}
            || '% entre RREO (R$ ' || {{ numero_br('ex.despesa_liquidada') }}
            || ') e DCA (R$ ' || {{ numero_br('d.liquidada_dca') }} || ').' as descricao
    from ex join dca_total d using (cod_ibge, ano)
    where ex.exercicio_completo
      and abs(ex.despesa_liquidada - d.liquidada_dca) > {{ tol }} * ex.despesa_liquidada

    union all
    -- 2. Limite máximo da LRF para o Executivo municipal é 54% da RCL.
    select cod_ibge, ano, 'aviso', 'limite_lrf_inconsistente',
        'RGF declara limite máximo de ' || {{ numero_br('limite_maximo_pct', 1) }} || '% da RCL (o legal é 54%).'
    from {{ ref('fct_pessoal_lrf') }}
    where limite_maximo_pct is not null and abs(limite_maximo_pct - 54) > 0.01
    qualify row_number() over (partition by cod_ibge, ano order by periodo desc) = 1

    union all
    -- 3. Exercício passado sem o RREO do 6º bimestre.
    select cod_ibge, ano, 'aviso', 'exercicio_incompleto',
        printf('Último RREO disponível é do %dº bimestre; o ano não está fechado.', bimestre_referencia)
    from ex, ano_atual
    where not exercicio_completo and ex.ano < ano_atual.ano_max

    union all
    -- 4. Receita muito abaixo da previsão costuma indicar envio parcial dos dados.
    select cod_ibge, ano, 'info', 'receita_muito_abaixo_previsto',
        'Receita realizada foi ' || {{ numero_br('100 * receita_realizada / receita_prevista_atualizada') }}
            || '% da previsão atualizada: previsão superestimada ou envio incompleto.'
    from ex
    where exercicio_completo
      and receita_realizada < 0.6 * receita_prevista_atualizada

    union all
    -- 5. Lacunas: anos sem RREO entre o primeiro e o último ano com dados do município.
    select m.cod_ibge, a.ano, 'aviso', 'ano_sem_dados', 'Nenhum RREO encontrado no SICONFI para o ano.'
    from (select cod_ibge, min(ano) as ano_min from ex group by 1) m
    cross join (select distinct ano from ex) a
    where a.ano > m.ano_min
      and not exists (select 1 from ex where ex.cod_ibge = m.cod_ibge and ex.ano = a.ano)

    union all
    -- 6. Município configurado sem nenhum dado.
    select m.cod_ibge, cast(null as integer), 'aviso', 'municipio_sem_dados',
        'Nenhum relatório do município foi encontrado no SICONFI.'
    from {{ ref('municipios') }} m
    where not exists (select 1 from ex where ex.cod_ibge = m.cod_ibge)
)
select a.*, m.nome as municipio
from achados a
join {{ ref('municipios') }} m using (cod_ibge)
order by a.cod_ibge, a.ano, a.regra
