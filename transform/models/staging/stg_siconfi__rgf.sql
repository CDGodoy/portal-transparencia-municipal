-- RGF (Relatório de Gestão Fiscal) Anexo 01 — despesa com pessoal do Poder Executivo.
with src as (
    {{ read_bronze('siconfi', 'rgf', {
        'exercicio': 'INTEGER', 'periodo': 'INTEGER', 'periodicidade': 'VARCHAR',
        'cod_ibge': 'BIGINT', 'co_poder': 'VARCHAR', 'populacao': 'BIGINT', 'anexo': 'VARCHAR',
        'rotulo': 'VARCHAR', 'coluna': 'VARCHAR', 'cod_conta': 'VARCHAR', 'conta': 'VARCHAR',
        'valor': 'DOUBLE', '_ordem': 'INTEGER'
    }) }}
)
select
    cod_ibge,
    exercicio as ano,
    periodo,
    trim(periodicidade) as periodicidade,
    trim(coluna) as coluna,
    trim(cod_conta) as cod_conta,
    trim(conta) as conta,
    valor,
    _ordem as ordem
from src
where valor is not null
  and coalesce(co_poder, 'E') = 'E'
