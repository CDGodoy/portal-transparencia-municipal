// Contratos de dados gerados por `portal export` (src/portal_etl/export.py).

export interface MunicipioIndice {
  cod_ibge: number;
  nome: string;
  uf: string;
  slug: string;
  destaque: boolean;
  populacao: number | null;
  anos: number[];
}

export interface Execucao {
  ano: number;
  bimestre: number;
  completo: boolean;
  populacao: number | null;
  receita_prevista_inicial: number | null;
  receita_prevista_atualizada: number | null;
  receita_realizada: number | null;
  dotacao_inicial: number | null;
  dotacao_atualizada: number | null;
  despesa_empenhada: number | null;
  despesa_liquidada: number | null;
  despesa_paga: number | null;
  resultado_orcamentario: number | null;
  fator_real: number | null;
  receita_realizada_real: number | null;
  despesa_liquidada_real: number | null;
  receita_per_capita_real: number | null;
  despesa_per_capita_real: number | null;
}

export interface Receita {
  ano: number;
  categoria: string;
  grupo: "propria" | "transferencia" | "credito";
  ordem: number;
  realizado: number;
  previsto: number;
  realizado_real: number | null;
}

export interface Natureza {
  ano: number;
  grupo: string;
  ordem: number;
  dotacao: number | null;
  liquidado: number | null;
  liquidado_real: number | null;
}

export interface Funcao {
  ano: number;
  nivel: "funcao" | "subfuncao";
  funcao_cod: string;
  funcao: string;
  subfuncao_cod: string | null;
  subfuncao: string | null;
  empenhado: number | null;
  liquidado: number | null;
  pago: number | null;
  liquidado_real: number | null;
  fonte: "DCA" | "RREO";
}

export interface Pessoal {
  ano: number;
  periodicidade: string;
  periodo: number;
  dtp: number;
  rcl: number | null;
  pct: number | null;
  limite_maximo: number | null;
  limite_prudencial: number | null;
  limite_alerta: number | null;
  situacao: string;
}

export interface ContratoResumo {
  ano: number;
  n: number;
  valor: number;
  valor_real: number | null;
}

export interface Fornecedor {
  ano: number | null;
  documento: string | null;
  nome: string;
  n: number;
  valor: number;
}

export interface Contrato {
  id: string;
  data: string | null;
  ano: number;
  fornecedor: string;
  documento: string | null;
  categoria: string;
  objeto: string;
  valor: number;
  unidade: string | null;
}

export interface Achado {
  ano: number | null;
  severidade: "aviso" | "info";
  regra: string;
  descricao: string;
}

export interface MunicipioDados extends MunicipioIndice {
  execucao: Execucao[];
  receitas: Receita[];
  natureza: Natureza[];
  funcoes: Funcao[];
  pessoal: Pessoal[];
  contratos: {
    resumo: ContratoResumo[];
    categorias: { ano: number; categoria: string; n: number; valor: number }[];
    fornecedores: Fornecedor[];
    lista: Contrato[];
  };
  qualidade: Achado[];
}

export interface Indicador {
  cod_ibge: number;
  nome: string;
  ano: number;
  exercicio_completo: boolean;
  populacao: number | null;
  receita_per_capita_real: number | null;
  despesa_per_capita_real: number | null;
  pct_pessoal: number | null;
  pct_investimento: number | null;
  pct_saude: number | null;
  pct_educacao: number | null;
  pct_dependencia_transferencias: number | null;
  pct_receita_propria: number | null;
  pct_pessoal_rcl: number | null;
  pct_resultado_orcamentario: number | null;
}

export interface Meta {
  versao: string;
  gerado_em: string;
  ultima_ingestao: string | null;
  ipca_referencia: string | null;
  testes: { total: number; pass?: number; warn?: number; fail?: number } | null;
  total_achados_qualidade: number;
  fontes: { nome: string; itens: string; url: string }[];
}
