const brlFull = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 0,
});
const num1 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 });
const num0 = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 0 });

/** R$ 737,9 mi · R$ 1,49 bi · R$ 82 mil — compacto para títulos e rótulos. */
export function brl(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  const a = Math.abs(v);
  const s = v < 0 ? "−" : "";
  if (a >= 1e9) return `${s}R$ ${num1.format(a / 1e9).replace(/,0$/, "")} bi`;
  if (a >= 1e6) return `${s}R$ ${num1.format(a / 1e6).replace(/,0$/, "")} mi`;
  if (a >= 1e4) return `${s}R$ ${num0.format(a / 1e3)} mil`;
  return `${s}${brlFull.format(a)}`;
}

/** Valor completo, para tabelas. */
export function brlCompleto(v: number | null | undefined): string {
  if (v == null || Number.isNaN(v)) return "—";
  return brlFull.format(v);
}

export function pct(v: number | null | undefined, digits = 1): string {
  if (v == null || Number.isNaN(v)) return "—";
  return `${v.toLocaleString("pt-BR", { maximumFractionDigits: digits, minimumFractionDigits: digits })}%`;
}

export function inteiro(v: number | null | undefined): string {
  if (v == null) return "—";
  return num0.format(v);
}

/** Eixos: 0 · 200 mi · 400 mi · 1 bi */
export function eixoBRL(v: number): string {
  const a = Math.abs(v);
  if (a === 0) return "0";
  if (a >= 1e9) return `${num1.format(v / 1e9).replace(/,0$/, "")} bi`;
  if (a >= 1e6) return `${num0.format(v / 1e6)} mi`;
  if (a >= 1e3) return `${num0.format(v / 1e3)} mil`;
  return num0.format(v);
}

export function dataBR(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso);
  return d.toLocaleDateString("pt-BR");
}

export function mesAno(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(`${iso.slice(0, 10)}T12:00:00`);
  return d.toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
}

export function titulo(s: string): string {
  // Nomes de fornecedores chegam em CAIXA ALTA; deixamos legível sem perder siglas curtas.
  const minusculas = new Set(["de", "da", "do", "das", "dos", "e", "em", "para", "a", "o"]);
  return s
    .toLowerCase()
    .split(/\s+/)
    .map((w, i) => {
      if (i > 0 && minusculas.has(w)) return w;
      if (/^(ltda|me|epp|eireli|s\/a|sa|s\.a\.?)$/.test(w)) return w.toUpperCase();
      return w.charAt(0).toUpperCase() + w.slice(1);
    })
    .join(" ");
}
