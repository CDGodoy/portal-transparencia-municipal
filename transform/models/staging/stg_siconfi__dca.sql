-- DCA (Declaração de Contas Anuais) — balanço do exercício encerrado.
with src as (
    {{ read_bronze('siconfi', 'dca', {
        'exercicio': 'INTEGER', 'cod_ibge': 'BIGINT', 'populacao': 'BIGINT', 'anexo': 'VARCHAR',
        'rotulo': 'VARCHAR', 'coluna': 'VARCHAR', 'cod_conta': 'VARCHAR', 'conta': 'VARCHAR',
        'valor': 'DOUBLE', '_ordem': 'INTEGER'
    }) }}
)
select
    cod_ibge,
    exercicio as ano,
    anexo,
    trim(rotulo) as rotulo,
    trim(coluna) as coluna,
    trim(cod_conta) as cod_conta,
    trim(conta) as conta,
    valor,
    _ordem as ordem
from src
where valor is not null
