import { h } from "./dom";
import { pct } from "./format";

export function secao(id: string, titulo: string, subtitulo: string, ...conteudo: Node[]) {
  return h("section", { class: "secao", id, "aria-labelledby": `${id}-t` },
    h("header", { class: "secao-cab" },
      h("h2", { id: `${id}-t` }, titulo),
      h("p", { class: "secao-sub" }, subtitulo)),
    ...conteudo);
}

export function cartao(...conteudo: (Node | string | null)[]) {
  return h("div", { class: "cartao" }, ...conteudo);
}

export function tituloGrafico(t: string, sub?: string) {
  return h("div", { class: "graf-cab" }, h("h3", null, t), sub ? h("p", null, sub) : null);
}

export function areaGrafico(altura = 320) {
  return h("div", { class: "graf", style: `height:${altura}px` });
}

export interface Tile {
  rotulo: string;
  valor: string;
  detalhe?: string;
  status?: "good" | "warning" | "serious" | "critical";
  statusTexto?: string;
}

export function tiles(itens: Tile[]) {
  return h("div", { class: "tiles" }, ...itens.map((t) =>
    h("div", { class: "tile" },
      h("div", { class: "tile-rotulo" }, t.rotulo),
      h("div", { class: "tile-valor" }, t.valor),
      t.status
        ? h("div", { class: `tile-status st-${t.status}` },
            h("span", { class: "st-icone", "aria-hidden": "true" },
              t.status === "good" ? "✓" : t.status === "critical" ? "✕" : "!"),
            t.statusTexto ?? "")
        : null,
      t.detalhe ? h("div", { class: "tile-detalhe" }, t.detalhe) : null)));
}

export interface Parte {
  nome: string;
  valor: number;
  cor: string;
  rotuloEscuro?: boolean;
}

/** Barra segmentada alta (parte-do-todo, ≤ 6 partes) com legenda e rótulos internos que cabem. */
export function barraSegmentada(partes: Parte[], formatar: (v: number) => string) {
  const total = partes.reduce((s, p) => s + Math.max(p.valor, 0), 0) || 1;
  const visiveis = partes.filter((p) => p.valor > 0);
  const barra = h("div", {
    class: "segbar",
    role: "img",
    "aria-label": visiveis
      .map((p) => `${p.nome}: ${formatar(p.valor)} (${((100 * p.valor) / total).toFixed(0)}%)`)
      .join("; "),
  }, ...visiveis.map((p) => {
    const share = (100 * p.valor) / total;
    const bloco = h("div", {
      class: `seg${p.rotuloEscuro ? " seg-escuro" : ""}`,
      style: `flex-basis:${share}%;background:${p.cor}`,
      title: `${p.nome}: ${formatar(p.valor)} (${pct(share)})`,
      tabindex: 0,
    });
    if (share >= 9) bloco.append(h("span", null, pct(share, 0)));
    return bloco;
  }));
  const legenda = h("ul", { class: "legenda" }, ...visiveis.map((p) =>
    h("li", null,
      h("span", { class: "leg-sw", style: `background:${p.cor}` }),
      h("span", { class: "leg-nome" }, p.nome),
      h("span", { class: "leg-val" }, `${formatar(p.valor)} · ${pct((100 * p.valor) / total)}`))));
  return h("div", { class: "segbar-wrap" }, barra, legenda);
}

export function aviso(texto: string, tipo: "info" | "aviso" = "info") {
  return h("p", { class: `nota nota-${tipo}` },
    h("span", { class: "nota-icone", "aria-hidden": "true" }, tipo === "aviso" ? "!" : "i"),
    texto);
}
