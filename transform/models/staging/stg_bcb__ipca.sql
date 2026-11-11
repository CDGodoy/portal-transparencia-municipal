-- IPCA: variação percentual mensal (série SGS 433 do Banco Central).
with src as (
    {{ read_bronze('bcb', 'ipca', {'data': 'VARCHAR', 'valor': 'VARCHAR'}) }}
)
select distinct
    strptime(data, '%d/%m/%Y')::date as mes,
    try_cast(valor as double) / 100.0 as variacao
from src
where try_cast(valor as double) is not null
