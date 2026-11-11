-- As categorias de receita devem somar exatamente o total realizado (o residual garante isso).
select e.cod_ibge, e.ano, e.receita_realizada, sum(r.receita_realizada) as soma
from {{ ref('fct_execucao_anual') }} e
join {{ ref('fct_receita_origem') }} r using (cod_ibge, ano)
group by 1, 2, 3
having abs(e.receita_realizada - sum(r.receita_realizada)) > 1
