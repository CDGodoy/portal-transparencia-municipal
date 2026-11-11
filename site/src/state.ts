import type { Indicador, Meta, MunicipioDados, MunicipioIndice } from "./types";

export interface Estado {
  municipios: MunicipioIndice[];
  indicadores: Indicador[];
  meta: Meta;
  mun: MunicipioDados;
  ano: number;
  /** true = valores corrigidos pelo IPCA; false = nominais (como publicados) */
  real: boolean;
}

/** Escolhe nominal ou corrigido pela inflação conforme o estado. */
export function val(e: Estado, nominal: number | null, real: number | null): number | null {
  return e.real ? real : nominal;
}

export function rotuloValores(e: Estado): string {
  return e.real ? "em reais de hoje (IPCA)" : "valores nominais";
}
