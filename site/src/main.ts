import "./style.css";
import { descartarGraficos } from "./charts";
import { h, limpar } from "./dom";
import { comparativo, contratos, despesa, evolucao, pessoal, receita, resumo, sobre } from "./sections";
import type { Estado } from "./state";
import type { Indicador, Meta, MunicipioDados, MunicipioIndice } from "./types";

const BASE = import.meta.env.BASE_URL;
const app = document.getElementById("app")!;
const cache = new Map<number, MunicipioDados>();

async function json<T>(caminho: string): Promise<T> {
  const r = await fetch(`${BASE}data/${caminho}`, { cache: "no-cache" });
  if (!r.ok) throw new Error(`Falha ao carregar ${caminho} (${r.status})`);
  return r.json() as Promise<T>;
}

async function carregarMunicipio(cod: number): Promise<MunicipioDados> {
  if (!cache.has(cod)) cache.set(cod, await json<MunicipioDados>(`municipios/${cod}.json`));
  return cache.get(cod)!;
}

/** #/5221858/2024/real */
function lerRota(): { cod?: number; ano?: number; real?: boolean } {
  const [cod, ano, modo] = location.hash.replace(/^#\/?/, "").split("/");
  return {
    cod: cod ? Number(cod) : undefined,
    ano: ano ? Number(ano) : undefined,
    real: modo ? modo === "real" : undefined,
  };
}

function anoPadrao(m: MunicipioDados): number {
  const completos = m.execucao.filter((x) => x.completo).map((x) => x.ano);
  return completos.length ? Math.max(...completos) : Math.max(...m.anos);
}

let estado: Estado | null = null;

function barraFiltros(e: Estado): HTMLElement {
  const munSel = h("select", { id: "f-mun", class: "select", "aria-label": "Município" },
    ...e.municipios.filter((m) => m.anos.length).map((m) =>
      h("option", { value: String(m.cod_ibge), selected: m.cod_ibge === e.mun.cod_ibge }, `${m.nome} — ${m.uf}`)));
  munSel.addEventListener("change", () => navegar(Number(munSel.value), undefined, e.real));

  const anos = [...e.mun.execucao].sort((a, b) => b.ano - a.ano);
  const anoSel = h("select", { id: "f-ano", class: "select", "aria-label": "Ano" },
    ...anos.map((x) => h("option", { value: String(x.ano), selected: x.ano === e.ano },
      x.completo ? String(x.ano) : `${x.ano} (parcial)`)));
  anoSel.addEventListener("change", () => navegar(e.mun.cod_ibge, Number(anoSel.value), e.real));

  const toggle = h("div", { class: "segmentado", role: "radiogroup", "aria-label": "Tipo de valor" },
    ...[["nominal", "Valores nominais"], ["real", "Corrigidos pela inflação"]].map(([k, rot]) => {
      const ativo = (k === "real") === e.real;
      return h("button", {
        type: "button", role: "radio", "aria-checked": ativo ? "true" : "false",
        class: ativo ? "ativo" : "",
        onclick: () => navegar(e.mun.cod_ibge, e.ano, k === "real"),
      }, rot);
    }));

  return h("div", { class: "filtros", role: "toolbar", "aria-label": "Filtros" },
    h("label", { class: "filtro" }, h("span", null, "Município"), munSel),
    h("label", { class: "filtro" }, h("span", null, "Ano"), anoSel),
    h("div", { class: "filtro" }, h("span", null, "Valores"), toggle));
}

function nav(): HTMLElement {
  const itens = [["resumo", "Resumo"], ["evolucao", "Evolução"], ["despesa", "Despesas"],
    ["receita", "Receitas"], ["pessoal", "Pessoal"], ["contratos", "Contratos"],
    ["comparativo", "Comparação"], ["sobre", "Sobre os dados"]];
  return h("nav", { class: "nav", "aria-label": "Seções" },
    ...itens.map(([id, rot]) => h("a", { href: `#${id}`, onclick: (ev: Event) => {
      ev.preventDefault();
      document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
    } }, rot)));
}

function render(): void {
  if (!estado) return;
  const e = estado;
  descartarGraficos();
  limpar(app);
  document.title = `${e.mun.nome} · Portal da Transparência Municipal`;
  app.append(
    h("header", { class: "topo" },
      h("div", { class: "topo-inner" },
        h("p", { class: "marca" }, "Portal da Transparência Municipal"),
        h("h1", null, e.mun.nome, h("span", { class: "uf" }, ` — ${e.mun.uf}`)),
        h("p", { class: "topo-sub" },
          "Orçamento, gastos, pessoal e contratos da prefeitura, com dados oficiais do Tesouro Nacional e do PNCP."))),
    h("div", { class: "faixa" }, h("div", { class: "faixa-inner" }, barraFiltros(e), nav())),
    h("main", { class: "conteudo" },
      resumo(e), evolucao(e), despesa(e), receita(e), pessoal(e), contratos(e), comparativo(e), sobre(e)),
    h("footer", { class: "rodape" },
      h("p", null, "Projeto independente de engenharia de dados. Dados públicos: SICONFI (Tesouro Nacional), PNCP e Banco Central.")),
  );
}

async function navegar(cod?: number, ano?: number, real?: boolean): Promise<void> {
  if (!estado) return;
  app.classList.add("carregando"); // mantém o quadro anterior enquanto carrega
  try {
    const mun = await carregarMunicipio(cod ?? estado.mun.cod_ibge);
    const anoOk = ano && mun.anos.includes(ano) ? ano : anoPadrao(mun);
    const scroll = window.scrollY;
    estado = { ...estado, mun, ano: anoOk, real: real ?? estado.real };
    history.replaceState(null, "", `#/${mun.cod_ibge}/${anoOk}/${estado.real ? "real" : "nominal"}`);
    render();
    window.scrollTo({ top: scroll });
  } finally {
    app.classList.remove("carregando");
  }
}

async function iniciar(): Promise<void> {
  try {
    const [municipios, indicadores, meta] = await Promise.all([
      json<MunicipioIndice[]>("municipios.json"),
      json<Indicador[]>("comparativo.json"),
      json<Meta>("meta.json"),
    ]);
    const disponiveis = municipios.filter((m) => m.anos.length);
    if (!disponiveis.length) throw new Error("Nenhum município com dados ainda.");
    const rota = lerRota();
    const inicial = disponiveis.find((m) => m.cod_ibge === rota.cod) ??
      disponiveis.find((m) => m.destaque) ?? disponiveis[0];
    const mun = await carregarMunicipio(inicial.cod_ibge);
    const ano = rota.ano && mun.anos.includes(rota.ano) ? rota.ano : anoPadrao(mun);
    estado = { municipios, indicadores, meta, mun, ano, real: rota.real ?? false };
    render();
  } catch (err) {
    limpar(app);
    app.append(h("div", { class: "erro" }, h("h1", null, "Não foi possível carregar os dados"),
      h("p", null, String((err as Error).message))));
  }
}

window.addEventListener("hashchange", () => {
  const r = lerRota();
  if (estado && (r.cod !== estado.mun.cod_ibge || r.ano !== estado.ano || r.real !== estado.real)) {
    void navegar(r.cod, r.ano, r.real);
  }
});
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", render);

void iniciar();
