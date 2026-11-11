"""Gera uma camada bronze de AMOSTRA para testes e desenvolvimento offline.

Os valores de Valparaíso de Goiás (2016, 2024, 2026) são recortes reais das respostas do
SICONFI/PNCP. O município "Luziânia" e a série de IPCA anterior a 2024 são SINTÉTICOS,
apenas para exercitar a lógica de comparação e deflação. Nunca use isso como dado real.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from portal_etl.bronze import BronzeStore  # noqa: E402

VALP = 5221858
LUZ = 5212501

R_PREV_INI, R_PREV_ATU, R_REAL = "PREVISÃO INICIAL", "PREVISÃO ATUALIZADA (a)", "Até o Bimestre (c)"
D_DOT_INI, D_DOT_ATU = "DOTAÇÃO INICIAL (d)", "DOTAÇÃO ATUALIZADA (e)"
D_EMP, D_LIQ = "DESPESAS EMPENHADAS ATÉ O BIMESTRE (f)", "DESPESAS LIQUIDADAS ATÉ O BIMESTRE (h)"
D_PAG = "DESPESAS PAGAS ATÉ O BIMESTRE (j)"


def _rreo1(ente, ano, periodo, pop, receitas, despesas, nome="Valparaíso de Goiás"):
    base = {
        "exercicio": ano, "demonstrativo": "RREO", "periodo": periodo, "periodicidade": "B",
        "instituicao": f"Prefeitura Municipal de {nome} - GO", "cod_ibge": ente, "uf": "GO",
        "populacao": pop, "anexo": "RREO-Anexo 01", "esfera": "M", "rotulo": "Padrão",
    }
    rows = []
    for cod, conta, ini, atu, real in receitas:
        for col, v in ((R_PREV_INI, ini), (R_PREV_ATU, atu), (R_REAL, real)):
            rows.append({**base, "coluna": col, "cod_conta": cod, "conta": conta, "valor": v})
    for cod, conta, dini, datu, emp, liq, pag in despesas:
        cols = ((D_DOT_INI, dini), (D_DOT_ATU, datu), (D_EMP, emp), (D_LIQ, liq), (D_PAG, pag))
        for col, v in cols:
            rows.append({**base, "coluna": col, "cod_conta": cod, "conta": conta, "valor": v})
    return rows


RREO1_2016 = _rreo1(VALP, 2016, 6, 153255, [
    ("ReceitasExcetoIntraOrcamentarias", "RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)",
     498156570.44, 535251515.57, 289696993.10),
    ("ReceitaTributaria", "RECEITA TRIBUTÁRIA", 133147579.79, 134035759.15, 50138378.87),
    ("Impostos", "Impostos", 125633305.50, 125633305.50, 47696051.84),
    ("Taxas", "Taxas", 7514274.29, 8402453.65, 2442327.03),
    ("ReceitaDeContribuicoes", "RECEITA DE CONTRIBUIÇÕES", 9852858.90, 18758909.70, 11083875.18),
    ("ReceitaPatrimonial", "RECEITA PATRIMONIAL", 14478718.52, 22507314.50, 12638394.54),
    ("TransferenciasCorrentes", "TRANSFERÊNCIAS CORRENTES", 270570885.24, 286580070.55,
     200898728.61),
    ("TransferenciasCorrentesIntergovernamentais", "Transferências Intergovernamentais",
     254735885.24, 269773950.04, 198043637.28),
    ("TransferenciasCorrentesDeConvenios", "Transferências de Convênios", 15835000.00,
     16806120.51, 2855091.33),
    ("TransferenciasDeCapitalIntergovernamentais", "Transferências Intergovernamentais",
     5279273.59, 6975441.09, 1834825.37),
    ("TransferenciasDeCapitalDeConvenios", "Transferências de Convênios", 32899405.64,
     32899405.64, 9015201.88),
], [
    ("DespesasExcetoIntraOrcamentarias", "DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (VIII)",
     493646488.10, 489789520.29, 271724561.29, 269715465.66, 265483562.68),
    ("PessoalEEncargosSociais", "PESSOAL E ENCARGOS SOCIAIS", 163662000.00, 168775881.23,
     133860836.70, 133546779.18, 133425408.59),
    ("OutrasDespesasCorrentes", "OUTRAS DESPESAS CORRENTES", 177260587.28, 202674459.82,
     116621561.96, 115608448.98, 112763564.32),
    ("Investimentos", "INVESTIMENTOS", 124693000.00, 108101955.98, 14893368.05, 14211442.92,
     12945795.19),
    ("AmortizacaoDaDivida", "AMORTIZAÇÃO DA DÍVIDA", 8910000.00, 10064032.19, 6348794.58,
     6348794.58, 6348794.58),
])

RREO1_2024 = _rreo1(VALP, 2024, 6, 196967, [
    ("ReceitasExcetoIntraOrcamentarias", "RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)",
     673217776.71, 1490571121.99, 737974469.00),
    ("Impostos", "Impostos", 110000000.00, 110000000.00, 108355840.00),
    ("Taxas", "Taxas", 9000000.00, 9000000.00, 9365734.00),
    ("ReceitaDeContribuicoes", "CONTRIBUIÇÕES", 30000000.00, 30000000.00, 33259165.00),
    ("ReceitaPatrimonial", "RECEITA PATRIMONIAL", 20000000.00, 20000000.00, 28430416.00),
    ("TransferenciasCorrentesDaUniaoEDeSuasEntidades",
     "Transferências da União e de suas Entidades", 240000000.00, 250000000.00, 256712352.00),
    ("TransferenciasCorrentesDosEstadosEDoDistritoFederalEDeSuasEntidades",
     "Transferências dos Estados e do Distrito Federal", 45000000.00, 45000000.00, 40106646.00),
    ("TransferenciasCorrentesDeOutrasInstituicoesPublicas",
     "Transferências de Outras Instituições Públicas", 180000000.00, 185000000.00, 191757157.00),
    ("ReceitasDeOperacoesDeCredito", "OPERAÇÕES DE CRÉDITO", 0.0, 25000000.00, 20403923.00),
    ("TransferenciasDeCapitalDaUniaoEDeSuasEntidades",
     "Transferências da União e de suas Entidades", 10000000.00, 20000000.00, 16446568.00),
    ("TransferenciasDeCapitalDosEstadosEDoDistritoFederalEDeSuasEntidades",
     "Transferências dos Estados e do Distrito Federal", 1000000.00, 2000000.00, 1581189.00),
], [
    ("DespesasExcetoIntraOrcamentarias", "DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (VIII)",
     663487969.06, 1480000000.00, 735746585.26, 734729841.00, 720000000.00),
    ("PessoalEEncargosSociais", "PESSOAL E ENCARGOS SOCIAIS", 330000000.00, 345000000.00,
     337500000.00, 336943222.00, 330000000.00),
    ("OutrasDespesasCorrentes", "OUTRAS DESPESAS CORRENTES", 250000000.00, 300000000.00,
     293000000.00, 292408223.00, 285000000.00),
    ("Investimentos", "INVESTIMENTOS", 70000000.00, 120000000.00, 90000000.00, 89485489.00,
     89000000.00),
    ("AmortizacaoDaDivida", "AMORTIZAÇÃO DA DÍVIDA", 13000000.00, 16000000.00, 15892906.00,
     15892906.00, 15892906.00),
])

RREO1_2026_4 = _rreo1(VALP, 2026, 4, 218416, [
    ("ReceitasExcetoIntraOrcamentarias", "RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)",
     900000000.00, 950000000.00, 560000000.00),
    ("Impostos", "Impostos", 130000000.00, 130000000.00, 80000000.00),
    ("TransferenciasCorrentesDaUniaoEDeSuasEntidades",
     "Transferências da União e de suas Entidades", 300000000.00, 300000000.00, 200000000.00),
], [
    ("DespesasExcetoIntraOrcamentarias", "DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (VIII)",
     890000000.00, 940000000.00, 600000000.00, 520000000.00, 500000000.00),
    ("PessoalEEncargosSociais", "PESSOAL E ENCARGOS SOCIAIS", 420000000.00, 430000000.00,
     300000000.00, 290000000.00, 285000000.00),
])

RREO1_LUZ_2024 = _rreo1(LUZ, 2024, 6, 221262, [
    ("ReceitasExcetoIntraOrcamentarias", "RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)",
     800000000.00, 820000000.00, 810000000.00),
    ("Impostos", "Impostos", 150000000.00, 150000000.00, 140000000.00),
], [
    ("DespesasExcetoIntraOrcamentarias", "DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (VIII)",
     800000000.00, 820000000.00, 790000000.00, 780000000.00, 770000000.00),
    ("PessoalEEncargosSociais", "PESSOAL E ENCARGOS SOCIAIS", 400000000.00, 410000000.00,
     405000000.00, 400000000.00, 398000000.00),
    ("Investimentos", "INVESTIMENTOS", 50000000.00, 60000000.00, 40000000.00, 35000000.00,
     34000000.00),
], nome="Luziânia")


def _rreo2(ente, ano, periodo, linhas):
    base = {
        "exercicio": ano, "demonstrativo": "RREO", "periodo": periodo, "periodicidade": "B",
        "instituicao": "Prefeitura Municipal de Valparaíso de Goiás - GO", "cod_ibge": ente,
        "uf": "GO", "populacao": 218416, "anexo": "RREO-Anexo 02", "esfera": "M",
        "rotulo": "Total das Despesas Exceto Intra-Orçamentárias", "cod_conta": "RREO2TotalDespesas",
    }
    rows = []
    for conta, dot, emp, liq in linhas:
        for col, v in (("DOTAÇÃO ATUALIZADA (a)", dot),
                       ("DESPESAS EMPENHADAS ATÉ O BIMESTRE (b)", emp),
                       ("DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)", liq)):
            rows.append({**base, "coluna": col, "conta": conta, "valor": v})
    # bloco intra-orçamentário que deve ser ignorado
    rows.append({**base, "rotulo": "Total das Despesas Intra-Orçamentárias", "coluna":
                 "DESPESAS LIQUIDADAS ATÉ O BIMESTRE (d)", "conta": "Previdência Social",
                 "valor": 999.0})
    return rows


RREO2_2026_4 = _rreo2(VALP, 2026, 4, [
    ("DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)", 940000000.00, 600000000.00, 520000000.00),
    ("Saúde", 200000000.00, 130000000.00, 115000000.00),
    ("Atenção Básica", 180000000.00, 120000000.00, 105000000.00),
    ("Educação", 330000000.00, 210000000.00, 185000000.00),
    ("Ensino Fundamental", 250000000.00, 160000000.00, 140000000.00),
    ("Urbanismo", 150000000.00, 90000000.00, 70000000.00),
    ("Administração", 80000000.00, 50000000.00, 45000000.00),
    ("FU04 - Administração Geral", 70000000.00, 45000000.00, 40000000.00),
])


def _dca_ie(ente, ano, linhas):
    base = {
        "exercicio": ano, "instituicao": "Prefeitura Municipal de Valparaíso de Goiás - GO",
        "cod_ibge": ente, "uf": "GO", "anexo": "DCA-Anexo I-E",
        "rotulo": "Total Geral da Despesa por Função", "cod_conta": "TotalDespesas",
        "populacao": 196967,
    }
    rows = []
    for col in ("Despesas Empenhadas", "Despesas Liquidadas", "Despesas Pagas"):
        fator = {"Despesas Empenhadas": 1.01, "Despesas Liquidadas": 1.0,
                 "Despesas Pagas": 0.98}[col]
        for conta, v in linhas:
            rows.append({**base, "coluna": col, "conta": conta, "valor": round(v * fator, 2)})
    return rows


DCA_IE_2024 = _dca_ie(VALP, 2024, [
    ("Despesas Exceto Intraorçamentárias", 734729841.00),
    ("04 - Administração", 61075602.00),
    ("04.122 - Administração Geral", 50681106.00),
    ("FU04 - Demais Subfunções", 10394496.00),
    ("10 - Saúde", 154036353.00),
    ("10.301 - Atenção Básica", 141339894.00),
    ("10.302 - Assistência Hospitalar e Ambulatorial", 12696459.00),
    ("12 - Educação", 262975663.00),
    ("12.361 - Ensino Fundamental", 200534578.00),
    ("12.365 - Educação Infantil", 62441085.00),
    ("15 - Urbanismo", 132945018.00),
    ("15.451 - Infraestrutura Urbana", 64976096.00),
    ("15.452 - Serviços Urbanos", 67968922.00),
    ("28 - Encargos Especiais", 123697205.00),
    ("28.843 - Serviço da Dívida Interna", 123697205.00),
    ("Despesas Intraorçamentárias", 14668513.00),
    ("09 - Previdência Social", 14668513.00),
    ("09.272 - Previdência do Regime Estatutário", 14668513.00),
])


def _rgf(ente, ano, periodo, linhas, col_pct="% sobre a RCL Ajustada"):
    base = {
        "exercicio": ano, "periodo": periodo, "periodicidade": "Q",
        "instituicao": "Prefeitura Municipal de Valparaíso de Goiás - GO", "cod_ibge": ente,
        "uf": "GO", "co_poder": "E", "populacao": 196967, "anexo": "RGF-Anexo 01", "esfera": "M",
        "rotulo": "Padrão",
    }
    rows = []
    for cod, conta, valor, pct in linhas:
        rows.append({**base, "coluna": "Valor", "cod_conta": cod, "conta": conta, "valor": valor})
        if pct is not None:
            rows.append({**base, "coluna": col_pct, "cod_conta": cod, "conta": conta, "valor": pct})
    return rows


RGF_2024 = _rgf(VALP, 2024, 3, [
    ("ReceitaCorrenteLiquidaLimiteLegal", "RECEITA CORRENTE LIQUIDA - RCL (IV)", 655275536.65, None),
    ("ReceitaCorrenteLiquidaAjustada", "= RECEITA CORRENTE LÍQUIDA AJUSTADA", 654275536.65, None),
    ("DespesaComPessoalTotal", "DESPESA TOTAL COM PESSOAL - DTP (VI)", 320234187.81, 48.94),
    ("LimiteMaximoDespesaComPessoalTotal", "LIMITE MÁXIMO (VII)", 353308789.79, 54.0),
    ("LimitePrudencialDespesaComPessoalTotal", "LIMITE PRUDENCIAL (VIII)", 335643350.30, 51.3),
    ("LimiteDeAlertaDespesaComPessoalTotal", "LIMITE DE ALERTA (IX)", 317977910.81, 48.6),
])

RGF_2016 = _rgf(VALP, 2016, 3, [
    ("ReceitaCorrenteLiquidaLimiteLegal", "RECEITA CORRENTE LIQUIDA - RCL (IV)", 278639466.0, None),
    ("DespesaComPessoalTotal", "DESPESA TOTAL COM PESSOAL - DTP (V)", 133372062.0, 48.0),
    ("LimiteMaximoDespesaComPessoalTotal", "LIMITE MÁXIMO (VI)", 167183680.0, 60.0),
    ("LimitePrudencialDespesaComPessoalTotal", "LIMITE PRUDENCIAL (VII)", 158824496.0, 57.0),
    ("LimiteDeAlertaDespesaComPessoalTotal", "LIMITE DE ALERTA (VIII)", 150465312.0, 54.0),
], col_pct="% sobre a RCL")


def _contrato(seq, ano, fornecedor, ni, cat, objeto, valor, data, unidade):
    return {
        "numeroControlePNCP": f"01616319000109-2-{seq:06d}/{ano}",
        "anoContrato": ano, "sequencialContrato": seq,
        "orgaoEntidade": {"cnpj": "01616319000109", "razaoSocial": "MUNICIPIO DE VALPARAISO DE GOIAS"},
        "niFornecedor": ni, "nomeRazaoSocialFornecedor": fornecedor, "tipoPessoa": "PJ",
        "categoriaProcesso": {"id": 8, "nome": cat},
        "tipoContrato": {"id": 1, "nome": "Contrato (termo inicial)"},
        "objetoContrato": objeto, "valorInicial": valor, "valorGlobal": valor,
        "dataAssinatura": data, "dataVigenciaInicio": data, "dataVigenciaFim": f"{ano}-12-31",
        "dataPublicacaoPncp": f"{data}T10:00:00", "dataAtualizacao": f"{data}T10:00:00",
        "unidadeOrgao": {"codigoIbge": "5221858", "nomeUnidade": unidade},
        "cod_ibge": VALP,
    }


CONTRATOS_2025 = [
    _contrato(1, 2025, "MIKAEL BARBOSA SOCIEDADE INDIVIDUAL DE ADVOCACIA", "23963933000180",
              "Serviços", "ASSESSORIA E CONSULTORIA JURIDICA PARA O FUNDO MUNICIPAL DE MEIO "
              "AMBIENTE", 126000.0, "2025-01-16", "FMMA FUNDO MUNICIPAL DO MEIO AMBIENTE"),
    _contrato(119, 2025, "BEM TE VI CONSTRUCOES E REFORMAS LTDA", "23131656000149", "Obras",
              "OBRA DE RECUPERACAO DO PISO DO ESTACIONAMENTO DA PRACA CENTRAL DO JARDIM CEU AZUL",
              111835.39, "2025-12-03", "SECRETARIA MUNICIPAL DE INFRAESTRUTURA"),
    _contrato(120, 2025, "LEAO CONSTRUTORA E SERVICOS LTDA", "27851023000166", "Serviços",
              "LOCACAO DE ROLO COMPACTADOR LISO", 250000.0, "2025-12-05",
              "SECRETARIA MUNICIPAL DE INFRAESTRUTURA"),
]
# Retificação: mesmo contrato publicado de novo com valor atualizado (deve deduplicar)
CONTRATO_RETIFICADO = {**CONTRATOS_2025[2], "valorGlobal": 300000.0,
                       "dataAtualizacao": "2026-02-01T09:00:00"}


def _ipca():
    rows = []
    reais = {  # 2024-2026: valores reais da série SGS 433
        2024: [0.42, 0.83, 0.16, 0.38, 0.46, 0.21, 0.38, -0.02, 0.44, 0.56, 0.39, 0.52],
        2025: [0.16, 1.31, 0.56, 0.43, 0.26, 0.24, 0.26, -0.11, 0.48, 0.09, 0.18, 0.33],
        2026: [0.33, 0.70, 0.88, 0.67, 0.58, 0.16, 0.07, -0.32, 0.82],
    }
    for ano in range(2015, 2027):
        meses = reais.get(ano, [0.4] * 12)  # sintético antes de 2024
        for m, v in enumerate(meses, start=1):
            rows.append({"data": f"01/{m:02d}/{ano}", "valor": f"{v:.2f}"})
    return rows


def build(root: Path) -> Path:
    store = BronzeStore(root)
    w = store.write
    w("siconfi", "rreo", {"anexo": "RREO-Anexo 01", "cod_ibge": VALP, "ano": 2016, "periodo": 6},
      RREO1_2016, "fixture")
    w("siconfi", "rreo", {"anexo": "RREO-Anexo 01", "cod_ibge": VALP, "ano": 2024, "periodo": 6},
      RREO1_2024, "fixture")
    # período antigo de 2026 que deve ser ignorado em favor do bimestre mais recente
    w("siconfi", "rreo", {"anexo": "RREO-Anexo 01", "cod_ibge": VALP, "ano": 2026, "periodo": 3},
      [{**r, "periodo": 3, "valor": r["valor"] * 0.7} for r in RREO1_2026_4], "fixture")
    w("siconfi", "rreo", {"anexo": "RREO-Anexo 01", "cod_ibge": VALP, "ano": 2026, "periodo": 4},
      RREO1_2026_4, "fixture")
    w("siconfi", "rreo", {"anexo": "RREO-Anexo 02", "cod_ibge": VALP, "ano": 2026, "periodo": 4},
      RREO2_2026_4, "fixture")
    w("siconfi", "rreo", {"anexo": "RREO-Anexo 01", "cod_ibge": LUZ, "ano": 2024, "periodo": 6},
      RREO1_LUZ_2024, "fixture")
    w("siconfi", "dca", {"anexo": "DCA-Anexo I-E", "cod_ibge": VALP, "ano": 2024}, DCA_IE_2024,
      "fixture")
    w("siconfi", "rgf", {"cod_ibge": VALP, "ano": 2024, "periodicidade": "Q", "periodo": 3},
      RGF_2024, "fixture")
    w("siconfi", "rgf", {"cod_ibge": VALP, "ano": 2016, "periodicidade": "Q", "periodo": 3},
      RGF_2016, "fixture")
    w("pncp", "contratos", {"cod_ibge": VALP, "ano_publicacao": 2025}, CONTRATOS_2025, "fixture")
    w("pncp", "contratos", {"cod_ibge": VALP, "ano_publicacao": 2026}, [CONTRATO_RETIFICADO],
      "fixture")
    w("bcb", "ipca", {"serie": 433}, _ipca(), "fixture")
    store.save()
    return root


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "bronze"
    build(out)
    print(f"Bronze de amostra gerada em {out}")
