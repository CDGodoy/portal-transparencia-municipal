type Child = Node | string | number | null | undefined | false;
type Attrs = Record<string, string | number | boolean | EventListener | undefined>;

/** Cria elementos com texto via textContent (nunca innerHTML com dados das APIs). */
export function h<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Attrs | null = null,
  ...children: Child[]
): HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v === undefined || v === false) continue;
      if (k.startsWith("on") && typeof v === "function") {
        el.addEventListener(k.slice(2).toLowerCase(), v as EventListener);
      } else if (k === "class") {
        el.className = String(v);
      } else if (v === true) {
        el.setAttribute(k, "");
      } else {
        el.setAttribute(k, String(v));
      }
    }
  }
  for (const c of children) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

/** Tabela acessível — todo gráfico tem uma, para que nenhum valor dependa do hover. */
export function tabela(
  colunas: { titulo: string; numerica?: boolean }[],
  linhas: (string | number)[][],
  resumo = "Ver dados em tabela",
): HTMLDetailsElement {
  const thead = h("thead", null, h("tr", null, ...colunas.map((c) =>
    h("th", { scope: "col", class: c.numerica ? "num" : "" }, c.titulo))));
  const tbody = h("tbody", null, ...linhas.map((l) =>
    h("tr", null, ...l.map((v, i) => h("td", { class: colunas[i]?.numerica ? "num" : "" }, v)))));
  return h("details", { class: "tabela" },
    h("summary", null, resumo),
    h("div", { class: "tabela-scroll" }, h("table", null, thead, tbody)));
}

export function limpar(el: Element): void {
  while (el.firstChild) el.removeChild(el.firstChild);
}
