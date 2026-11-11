# Dicionário de dados — camada gold

Todos os valores monetários estão em R$. Colunas com sufixo `_real` estão em **reais constantes**
(corrigidas pelo IPCA médio do ano até o último mês disponível); as demais são **nominais**, como
publicadas. Totais excluem operações **intra-orçamentárias**.

## `fct_execucao_anual` — município × ano

| Coluna | Descrição |
|---|---|
| `cod_ibge` | Código IBGE do município (7 dígitos) |
| `ano` | Exercício |
| `bimestre_referencia` | Último bimestre do RREO disponível (6 = ano fechado) |
| `exercicio_completo` | `true` se `bimestre_referencia = 6` |
| `populacao` | Estimativa do IBGE informada no RREO |
| `receita_prevista_inicial` / `receita_prevista_atualizada` | Previsão na LOA e após créditos/reestimativas |
| `receita_realizada` | Receita arrecadada até o bimestre |
| `dotacao_inicial` / `dotacao_atualizada` | Orçamento autorizado para despesas |
| `despesa_empenhada` | Valor reservado/comprometido |
| `despesa_liquidada` | Bem ou serviço entregue e reconhecido (medida principal de "gasto") |
| `despesa_paga` | Valor efetivamente pago |
| `resultado_orcamentario` | `receita_realizada − despesa_liquidada` |
| `fator_real` | Multiplicador IPCA para reais de hoje |
| `receita_per_capita_real` / `despesa_per_capita_real` | Em reais de hoje por habitante |

## `fct_receita_origem` — município × ano × categoria

| Coluna | Descrição |
|---|---|
| `categoria` | Origem (ex.: "Impostos (IPTU, ISS, ITBI, IRRF)", "Transferências da União…", "Outras receitas") |
| `grupo` | `propria`, `transferencia` ou `credito` |
| `receita_realizada` / `receita_prevista` | Valores da categoria |

As categorias somam exatamente `fct_execucao_anual.receita_realizada` (teste
`assert_receita_categorias_somam_total`).

## `fct_despesa_natureza` — município × ano × grupo

`grupo_natureza`: Pessoal e encargos · Juros da dívida · Custeio e serviços · Investimentos ·
Inversões financeiras · Amortização da dívida. Medidas: `dotacao_atualizada`, `despesa_liquidada`.

## `fct_despesa_funcao` — município × ano × função × subfunção

| Coluna | Descrição |
|---|---|
| `nivel` | `funcao` ou `subfuncao` |
| `funcao_cod` / `funcao_nome` | Função de governo (Portaria MOG 42/1999), ex.: 10 Saúde, 12 Educação |
| `subfuncao_cod` / `subfuncao_nome` | Subfunção; `999` = "Demais subfunções" |
| `despesa_empenhada` / `despesa_liquidada` / `despesa_paga` | Valores |
| `fonte` | `DCA` (balanço anual, exercício encerrado) ou `RREO` (ano corrente, só função) |

## `fct_pessoal_lrf` — município × ano × período

| Coluna | Descrição |
|---|---|
| `periodicidade` / `periodo` | `Q` quadrimestral (1–3) ou `S` semestral (1–2) |
| `dtp` | Despesa total com pessoal (últimos 12 meses) |
| `rcl` | Receita corrente líquida (ajustada, quando disponível) |
| `dtp_pct_rcl` | `dtp / rcl` em % |
| `limite_*_pct` | Limites declarados no relatório (máximo 54%, prudencial 51,3%, alerta 48,6%) |
| `situacao` | Classificação segundo os limites legais |

## `fct_contratos` — contrato (PNCP)

`numero_controle_pncp` (chave), `ano`, `data_assinatura`, `vigencia_inicio/fim`,
`fornecedor_documento`, `fornecedor_nome`, `categoria` (Obras, Serviços, Compras…), `objeto`,
`valor_global` (valor total previsto no contrato, **não** o pago), `unidade_nome`.
Retificações são deduplicadas mantendo a versão mais recente.

## `mart_indicadores` — município × ano

`receita_per_capita_real`, `despesa_per_capita_real`, `pct_pessoal`, `pct_investimento`,
`pct_saude`, `pct_educacao`, `pct_dependencia_transferencias`, `pct_receita_propria`,
`pct_pessoal_rcl`, `pct_resultado_orcamentario`.

## `mart_qualidade_dados` — achado

| Regra | Significado |
|---|---|
| `reconciliacao_rreo_dca` | Despesa liquidada difere mais de 1% entre RREO (6º bim.) e DCA |
| `limite_lrf_inconsistente` | RGF declara limite máximo diferente de 54% |
| `pessoal_rcl_implausivel` | RGF declara despesa com pessoal acima de 100% (ou negativa) da RCL |
| `exercicio_incompleto` | Ano passado sem RREO do 6º bimestre |
| `receita_muito_abaixo_previsto` | Arrecadação < 60% da previsão atualizada |
| `ano_sem_dados` | Lacuna de RREO entre anos com dados |
| `municipio_sem_dados` | Município configurado sem nenhum relatório |
