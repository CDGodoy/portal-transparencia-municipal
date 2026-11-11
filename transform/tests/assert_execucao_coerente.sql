{{ config(severity='warn') }}
-- Estágios da despesa: pago <= liquidado <= empenhado (com folga de R$ 1 para arredondamento).
select cod_ibge, ano, despesa_empenhada, despesa_liquidada, despesa_paga
from {{ ref('fct_execucao_anual') }}
where despesa_liquidada > despesa_empenhada + 1
   or despesa_paga > despesa_liquidada + 1
