-- Contratos publicados no PNCP. Um contrato pode reaparecer em janelas diferentes ou ser
-- retificado; mantemos apenas a versão mais recente de cada número de controle.
with src as (
    {{ read_bronze('pncp', 'contratos', {
        'numeroControlePNCP': 'VARCHAR', 'cod_ibge': 'BIGINT', 'anoContrato': 'INTEGER',
        'niFornecedor': 'VARCHAR', 'nomeRazaoSocialFornecedor': 'VARCHAR',
        'tipoPessoa': 'VARCHAR', 'categoriaProcesso': 'JSON', 'tipoContrato': 'JSON',
        'objetoContrato': 'VARCHAR', 'valorInicial': 'DOUBLE', 'valorGlobal': 'DOUBLE',
        'dataAssinatura': 'VARCHAR', 'dataVigenciaInicio': 'VARCHAR',
        'dataVigenciaFim': 'VARCHAR', 'dataPublicacaoPncp': 'VARCHAR',
        'dataAtualizacao': 'VARCHAR', 'unidadeOrgao': 'JSON'
    }) }}
),
tipado as (
    select
        numeroControlePNCP as numero_controle_pncp,
        cod_ibge,
        anoContrato as ano_contrato,
        try_cast(dataAssinatura as date) as data_assinatura,
        try_cast(dataVigenciaInicio as date) as vigencia_inicio,
        try_cast(dataVigenciaFim as date) as vigencia_fim,
        try_cast(dataPublicacaoPncp as timestamp) as publicado_em,
        try_cast(dataAtualizacao as timestamp) as atualizado_em,
        regexp_replace(coalesce(niFornecedor, ''), '[^0-9]', '', 'g') as fornecedor_documento,
        upper(trim(nomeRazaoSocialFornecedor)) as fornecedor_nome,
        tipoPessoa as fornecedor_tipo_pessoa,
        categoriaProcesso ->> '$.nome' as categoria,
        tipoContrato ->> '$.nome' as tipo_contrato,
        trim(regexp_replace(objetoContrato, '\s+', ' ', 'g')) as objeto,
        coalesce(valorGlobal, valorInicial) as valor_global,
        unidadeOrgao ->> '$.nomeUnidade' as unidade_nome
    from src
    where numeroControlePNCP is not null
)
select *
from tipado
qualify row_number() over (
    partition by numero_controle_pncp
    order by atualizado_em desc nulls last, publicado_em desc nulls last
) = 1
