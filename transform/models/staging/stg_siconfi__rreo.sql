-- RREO (Relatório Resumido de Execução Orçamentária), anexos 01 e 02, um registro por célula.
with src as (
    {{ read_bronze('siconfi', 'rreo', {
        'exercicio': 'INTEGER', 'periodo': 'INTEGER', 'cod_ibge': 'BIGINT',
        'instituicao': 'VARCHAR', 'populacao': 'BIGINT', 'anexo': 'VARCHAR',
        'rotulo': 'VARCHAR', 'coluna': 'VARCHAR', 'cod_conta': 'VARCHAR',
        'conta': 'VARCHAR', 'valor': 'DOUBLE', '_ordem': 'INTEGER', '_source_url': 'VARCHAR'
    }) }}
)
select
    cod_ibge,
    exercicio as ano,
    periodo,
    anexo,
    trim(rotulo) as rotulo,
    trim(coluna) as coluna,
    trim(cod_conta) as cod_conta,
    trim(conta) as conta,
    valor,
    populacao,
    _ordem as ordem
from src
where valor is not null
