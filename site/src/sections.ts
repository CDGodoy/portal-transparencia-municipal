import { base, chave, eixoCategoria, eixoValor, esc, grafico } from "./charts";
import {
  areaGrafico,
  aviso,
  barraSegmentada,
  cartao,
  secao,
  tiles,
  tituloGrafico,
  type Parte,
} from "./components";
import { h, tabela } from "./dom";
import { brl, brlCompleto, dataBR, eixoBRL, inteiro, mesAno, pct, titulo } from "./format";
import { rotuloValores, val, type Estado } from "./state";
import { lerTema } from "./theme";
import type { Execucao, Indicador } from "./types";

const REPO_URL: string = import.meta.env.VITE_REPO_URL ?? "";

function execAno(e: Estado): Execucao | undefined {
  return e.mun.execucao.find((x) => x.ano === e.ano);
}

function rotuloAno(x: Execucao | undefined, ano: number): string {
  if (!x) return String(ano);
  return x.completo ? String(ano) : `${ano} (até o ${x.bimestre}º bimestre)`;
}

/* ------------------------------------------------------------------ resumo */
export function resumo(e: Estado): HTMLElement {
  const x = execAno(e);
  if (!x) return secao("resumo", "Resumo", "Sem dados para o ano selecionado.");
  const t = lerTema();
  const receita = val(e, x.receita_realizada, x.receita_realizada_real);
  const despesa = val(e, x.despesa_liquidada, x.despesa_liquidada_real);
  const execReceita = x.receita_prevista_atualizada
    ? (100 * (x.receita_realizada ?? 0)) / x.receita_prevista_atualizada
    : null;
  const execDespesa = x.dotacao_atualizada
    ? (100 * (x.despesa_liquidada ?? 0)) / x.dotacao_atualizada
    : null;
  const resultado = x.resultado_orcamentario ?? 0;
  const resultadoV = e.real ? resultado * (x.fator_real ?? 1) : resultado;
  const lrf = ultimoPessoal(e, e.ano);
  const status = lrf ? statusLrf(lrf.pct) : null;
  const porHab = e.real
    ? x.despesa_per_capita_real
    : x.populacao
      ? (x.despesa_liquidada ?? 0) / x.populacao
      : null;

  const frase = h("p", { class: "hero-frase" },
    `Em ${rotuloAno(x, e.ano)}, a Prefeitura de ${e.mun.nome} arrecadou `,
    h("strong", null, brl(receita)),
    " e gastou ",
    h("strong", null, brl(despesa)),
    ".");

  const hero = h("div", { class: "hero" },
    h("div", { class: "hero-rotulo" }, `Despesa liquidada · ${rotuloValores(e)}`),
    h("div", { class: "hero-valor" }, brl(despesa)),
    frase);

  void t;
  return secao("resumo", "Resumo do ano",
    "Quanto a prefeitura arrecadou, quanto gastou e como está a saúde fiscal.",
    cartao(hero,
      tiles([
        {
          rotulo: "Receita arrecadada",
          valor: brl(receita),
          detalhe: execReceita != null
            ? `${pct(execReceita, 0)} da previsão atualizada (${brl(e.real ? (x.receita_prevista_atualizada ?? 0) * (x.fator_real ?? 1) : x.receita_prevista_atualizada)})`
            : undefined,
        },
        {
          rotulo: "Orçamento executado",
          valor: pct(execDespesa, 0),
          detalhe: `Liquidado de ${brl(e.real ? (x.dotacao_atualizada ?? 0) * (x.fator_real ?? 1) : x.dotacao_atualizada)} autorizados`,
        },
        {
          rotulo: "Gasto por habitante",
          valor: brl(porHab),
          detalhe: x.populacao ? `${inteiro(x.populacao)} habitantes (estimativa IBGE)` : undefined,
        },
        {
          rotulo: resultadoV >= 0 ? "Superávit orçamentário" : "Déficit orçamentário",
          valor: brl(Math.abs(resultadoV)),
          detalhe: "Receita arrecadada menos despesa liquidada",
        },
        lrf
          ? {
              rotulo: "Pessoal / receita corrente líquida",
              valor: pct(lrf.pct),
              status: status!.chave,
              statusTexto: status!.texto,
              detalhe: `RGF ${lrf.periodo}º ${lrf.periodicidade === "Q" ? "quadrimestre" : "semestre"} · limite máximo 54%`,
            }
          : { rotulo: "Pessoal / receita corrente líquida", valor: "—", detalhe: "RGF não disponível" },
      ]),
      !x.completo
        ? aviso(`Exercício em andamento: valores acumulados até o ${x.bimestre}º bimestre de ${e.ano}.`)
        : null));
}

function ultimoPessoal(e: Estado, ano: number) {
  const lista = e.mun.pessoal.filter((p) => p.ano === ano);
  return lista.sort((a, b) => b.periodo - a.periodo)[0];
}

function statusLrf(p: number | null) {
  const v = p ?? 0;
  if (v > 54) return { chave: "critical" as const, texto: "Acima do limite máximo da LRF" };
  if (v > 51.3) return { chave: "serious" as const, texto: "Acima do limite prudencial" };
  if (v > 48.6) return { chave: "warning" as const, texto: "Acima do limite de alerta" };
  return { chave: "good" as const, texto: "Dentro dos limites da LRF" };
}

/* ---------------------------------------------------------------- evolução */
export function evolucao(e: Estado): HTMLElement {
  const dados = e.mun.execucao;
  const anos = dados.map((d) => (d.completo ? String(d.ano) : `${d.ano}*`));
  const rec = dados.map((d) => val(e, d.receita_realizada, d.receita_realizada_real));
  const des = dados.map((d) => val(e, d.despesa_liquidada, d.despesa_liquidada_real));
  const el = areaGrafico(340);
  const sel = dados.findIndex((d) => d.ano === e.ano);

  const card = cartao(
    tituloGrafico("Receita arrecadada × despesa liquidada", `Por ano, ${rotuloValores(e)}. * ano em andamento (parcial).`),
    el,
    tabela(
      [{ titulo: "Ano" }, { titulo: "Receita arrecadada", numerica: true },
       { titulo: "Despesa liquidada", numerica: true }, { titulo: "Resultado", numerica: true }],
      dados.map((_d, i) => [anos[i], brlCompleto(rec[i]), brlCompleto(des[i]),
        brlCompleto((rec[i] ?? 0) - (des[i] ?? 0))]),
    ),
  );

  queueMicrotask(() => grafico(el, (t) => ({
    ...base(t),
    color: [t.series[0], t.series[1]],
    legend: { top: 0, left: 0, icon: "roundRect", itemWidth: 14, itemHeight: 3,
      textStyle: { color: t.textSecondary } },
    grid: { left: 8, right: 16, top: 40, bottom: 8, containLabel: true },
    xAxis: { ...eixoCategoria(t, anos), boundaryGap: false },
    yAxis: eixoValor(t),
    tooltip: {
      ...(base(t).tooltip as object), trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: t.axis, width: 1 } },
      formatter: (ps: { axisValue: string; color: string; seriesName: string; value: number }[]) =>
        `<div style="font-weight:600;margin-bottom:4px">${esc(ps[0].axisValue)}</div>` +
        ps.map((p) => `<div>${chave(p.color)}<strong>${brl(p.value)}</strong> <span style="color:${t.textSecondary}">${esc(p.seriesName)}</span></div>`).join(""),
    },
    series: [
      { name: "Receita arrecadada", type: "line", data: rec, smooth: false, symbol: "circle",
        symbolSize: 8, lineStyle: { width: 2 }, itemStyle: { borderColor: t.surface, borderWidth: 2 },
        markLine: sel >= 0 ? { symbol: "none", silent: true, label: { show: false },
          lineStyle: { color: t.axis, type: "solid", width: 1 }, data: [{ xAxis: sel }] } : undefined },
      { name: "Despesa liquidada", type: "line", data: des, symbol: "circle", symbolSize: 8,
        lineStyle: { width: 2 }, itemStyle: { borderColor: t.surface, borderWidth: 2 } },
    ],
  })));

  return secao("evolucao", "Evolução", "Como receitas e despesas mudaram ao longo dos anos.", card);
}

/* ----------------------------------------------------------------- despesa */
export function despesa(e: Estado): HTMLElement {
  const t = lerTema();
  const nat = e.mun.natureza.filter((n) => n.ano === e.ano && (n.liquidado ?? 0) > 0);
  const partes: Parte[] = nat.map((n, i) => ({
    nome: n.grupo,
    valor: val(e, n.liquidado, n.liquidado_real) ?? 0,
    cor: t.series[i % t.series.length],
    rotuloEscuro: false,
  }));

  const funcoes = e.mun.funcoes
    .filter((f) => f.ano === e.ano && f.nivel === "funcao" && (f.liquidado ?? 0) > 0)
    .sort((a, b) => (b.liquidado ?? 0) - (a.liquidado ?? 0));
  const totalFun = funcoes.reduce((s, f) => s + (f.liquidado ?? 0), 0);
  const fonteRreo = funcoes.some((f) => f.fonte === "RREO");

  const elFun = areaGrafico(Math.max(220, funcoes.length * 34 + 30));
  const elSub = areaGrafico(200);
  const subWrap = h("div", { class: "sub-wrap" });
  const subTitulo = h("div", { class: "bloco" });

  function mostrarSub(cod: string) {
    const subs = e.mun.funcoes
      .filter((f) => f.ano === e.ano && f.nivel === "subfuncao" && f.funcao_cod === cod && (f.liquidado ?? 0) > 0)
      .sort((a, b) => (b.liquidado ?? 0) - (a.liquidado ?? 0));
    const nome = funcoes.find((f) => f.funcao_cod === cod)?.funcao ?? "";
    subTitulo.replaceChildren(tituloGrafico(`Detalhe: ${nome}`, "Subfunções — em que, dentro da área, o dinheiro foi gasto."));
    if (!subs.length) {
      subWrap.replaceChildren(aviso(fonteRreo
        ? "O detalhamento por subfunção só existe no balanço anual (DCA), publicado após o fim do exercício."
        : "Sem subfunções informadas para esta área."));
      return;
    }
    elSub.style.height = `${Math.max(120, subs.length * 34 + 30)}px`;
    subWrap.replaceChildren(elSub);
    barrasHorizontais(elSub, subs.map((s) => s.subfuncao ?? "—"),
      subs.map((s) => val(e, s.liquidado, s.liquidado_real) ?? 0), t.series[0]);
  }

  const card = cartao(
    tituloGrafico("Por tipo de gasto", `Despesa liquidada por natureza, ${rotuloValores(e)}.`),
    partes.length ? barraSegmentada(partes, brl) : aviso("Sem dados de natureza da despesa para o ano."),
    h("hr"),
    tituloGrafico("Por área de governo", "Funções de governo, da maior para a menor. Clique numa barra para ver o detalhe."),
    funcoes.length ? elFun : aviso("Sem dados por função para o ano."),
    fonteRreo ? aviso("Ano sem balanço anual (DCA): valores do RREO Anexo 2, no bimestre mais recente.") : null,
    subTitulo,
    subWrap,
    tabela(
      [{ titulo: "Área (função)" }, { titulo: "Liquidado", numerica: true }, { titulo: "Participação", numerica: true }],
      funcoes.map((f) => [f.funcao, brlCompleto(val(e, f.liquidado, f.liquidado_real)),
        pct((100 * (f.liquidado ?? 0)) / (totalFun || 1))]),
    ),
  );

  if (funcoes.length) {
    queueMicrotask(() => {
      const inst = barrasHorizontais(elFun, funcoes.map((f) => f.funcao),
        funcoes.map((f) => val(e, f.liquidado, f.liquidado_real) ?? 0), t.series[0],
        funcoes.map((f) => (100 * (f.liquidado ?? 0)) / (totalFun || 1)));
      inst.on("click", (p) => mostrarSub(funcoes[(p as { dataIndex: number }).dataIndex].funcao_cod));
      mostrarSub(funcoes[0].funcao_cod);
    });
  }

  return secao("despesa", "Para onde vai o dinheiro", "Despesa liquidada: o serviço foi entregue e a prefeitura reconheceu a dívida com o fornecedor.", card);
}

/** Espaço à esquerda para os rótulos: cabe o maior nome, até 40% da largura do gráfico. */
function larguraRotulos(nomes: string[], el: HTMLElement): number {
  const maior = Math.max(...nomes.map((x) => x.length), 4);
  const limite = Math.max(120, (el.clientWidth || 800) * 0.4);
  return Math.round(Math.min(limite, maior * 6.6 + 16));
}

/** Barras horizontais ranqueadas (uma cor só — sem rampa em categorias nominais). */
function barrasHorizontais(el: HTMLElement, nomes: string[], valores: number[], cor: string,
  participacao?: number[], destaque?: number) {
  const n = [...nomes].reverse();
  const v = [...valores].reverse();
  const p = participacao ? [...participacao].reverse() : undefined;
  const dIdx = destaque != null ? nomes.length - 1 - destaque : -1;
  const esq = larguraRotulos(n, el);
  return grafico(el, (t) => ({
    ...base(t),
    grid: { left: esq, right: 110, top: 4, bottom: 4, containLabel: false },
    xAxis: { ...eixoValor(t), show: false },
    yAxis: { type: "category", data: n, axisTick: { show: false }, axisLine: { show: false },
      axisLabel: { color: t.textSecondary, fontSize: 12, width: esq - 12, overflow: "truncate" } },
    tooltip: { ...(base(t).tooltip as object), trigger: "item",
      formatter: (x: { name: string; value: number; dataIndex: number }) =>
        `<strong>${brl(x.value)}</strong>${p ? ` · ${pct(p[x.dataIndex])}` : ""}<br><span style="color:${t.textSecondary}">${esc(x.name)}</span>` },
    series: [{
      type: "bar", barMaxWidth: 20, cursor: "pointer",
      data: v.map((val, i) => ({
        value: val,
        itemStyle: { color: dIdx >= 0 && i !== dIdx ? t.neutro : cor, borderRadius: [0, 4, 4, 0] },
      })),
      label: { show: true, position: "right", color: t.textSecondary, fontSize: 12,
        formatter: (x: { value: number; dataIndex: number }) => p ? `${brl(x.value)} · ${pct(p[x.dataIndex], 0)}` : brl(x.value) },
      emphasis: { itemStyle: { opacity: 0.85 } },
    }],
  }));
}

/* ----------------------------------------------------------------- receita */
export function receita(e: Estado): HTMLElement {
  const t = lerTema();
  const rec = e.mun.receitas.filter((r) => r.ano === e.ano && r.realizado > 0);
  const soma = (g: string) => rec.filter((r) => r.grupo === g)
    .reduce((s, r) => s + (val(e, r.realizado, r.realizado_real) ?? 0), 0);
  const partes: Parte[] = [
    { nome: "Arrecadação própria", valor: soma("propria"), cor: t.series[0] },
    { nome: "Transferências (União, Estado, FUNDEB)", valor: soma("transferencia"), cor: t.series[1] },
    { nome: "Empréstimos", valor: soma("credito"), cor: t.series[2] },
  ];
  const total = partes.reduce((s, p) => s + p.valor, 0) || 1;
  const cats = [...rec].sort((a, b) => b.realizado - a.realizado);
  const el = areaGrafico(Math.max(200, cats.length * 34 + 30));

  queueMicrotask(() => {
    if (cats.length) {
      barrasHorizontais(el, cats.map((c) => c.categoria),
        cats.map((c) => val(e, c.realizado, c.realizado_real) ?? 0), t.series[0],
        cats.map((c) => (100 * c.realizado) / (cats.reduce((s, x) => s + x.realizado, 0) || 1)));
    }
  });

  return secao("receita", "De onde vem o dinheiro",
    `${pct((100 * partes[1].valor) / total, 0)} da receita de ${e.ano} veio de transferências de outros governos.`,
    cartao(
      tituloGrafico("Origem da receita", `Receita arrecadada, ${rotuloValores(e)}.`),
      barraSegmentada(partes, brl),
      h("hr"),
      tituloGrafico("Por categoria", "Impostos municipais, repasses e outras receitas."),
      cats.length ? el : aviso("Sem dados de receita para o ano."),
      e.ano <= 2017
        ? aviso("Até 2017 o RREO não separava transferências da União e do Estado; elas aparecem como “intergovernamentais”.")
        : null,
      tabela([{ titulo: "Categoria" }, { titulo: "Arrecadado", numerica: true }, { titulo: "Previsto", numerica: true }],
        cats.map((c) => [c.categoria, brlCompleto(val(e, c.realizado, c.realizado_real)), brlCompleto(c.previsto)])),
    ));
}

/* ----------------------------------------------------------------- pessoal */
export function pessoal(e: Estado): HTMLElement {
  const porAno = new Map<number, (typeof e.mun.pessoal)[number]>();
  for (const p of e.mun.pessoal) {
    const atual = porAno.get(p.ano);
    if (!atual || p.periodo > atual.periodo) porAno.set(p.ano, p);
  }
  const serie = [...porAno.values()].sort((a, b) => a.ano - b.ano);
  if (!serie.length) {
    return secao("pessoal", "Gasto com pessoal e a LRF", "", cartao(aviso("RGF não disponível para este município.")));
  }
  const el = areaGrafico(320);
  const atual = porAno.get(e.ano);
  const st = atual ? statusLrf(atual.pct) : null;

  queueMicrotask(() => grafico(el, (t) => ({
    ...base(t),
    color: [t.series[0]],
    grid: { left: 8, right: 120, top: 16, bottom: 8, containLabel: true },
    xAxis: { ...eixoCategoria(t, serie.map((s) => String(s.ano))), boundaryGap: false },
    yAxis: { ...eixoValor(t, (v) => `${v}%`), min: 30, max: 60 },
    tooltip: { ...(base(t).tooltip as object), trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: t.axis, width: 1 } },
      formatter: (ps: { dataIndex: number }[]) => {
        const s = serie[ps[0].dataIndex];
        return `<div style="font-weight:600">${s.ano} · ${s.periodo}º ${s.periodicidade === "Q" ? "quadrimestre" : "semestre"}</div>` +
          `<div><strong>${pct(s.pct)}</strong> da RCL</div><div style="color:${t.textSecondary}">${brl(s.dtp)} de ${brl(s.rcl)}</div>`;
      } },
    series: [{
      name: "Despesa com pessoal / RCL", type: "line", data: serie.map((s) => s.pct),
      symbol: "circle", symbolSize: 8, lineStyle: { width: 2 },
      itemStyle: { borderColor: t.surface, borderWidth: 2 },
      markLine: {
        symbol: "none", silent: true,
        label: { position: "end", color: t.textSecondary, fontSize: 11, formatter: "{b}" },
        data: [
          { name: "Alerta 48,6%", yAxis: 48.6, lineStyle: { color: t.status.warning, type: "solid", width: 1 } },
          { name: "Prudencial 51,3%", yAxis: 51.3, lineStyle: { color: t.status.serious, type: "solid", width: 1 } },
          { name: "Máximo 54%", yAxis: 54, lineStyle: { color: t.status.critical, type: "solid", width: 1 } },
        ],
      },
    }],
  })));

  return secao("pessoal", "Gasto com pessoal e a LRF",
    "A Lei de Responsabilidade Fiscal limita a despesa com pessoal do Executivo municipal a 54% da receita corrente líquida (RCL).",
    cartao(
      atual && st
        ? h("div", { class: "medidor" },
            h("div", { class: "medidor-cab" },
              h("span", { class: "medidor-valor" }, pct(atual.pct)),
              h("span", { class: `tile-status st-${st.chave}` },
                h("span", { class: "st-icone", "aria-hidden": "true" }, st.chave === "good" ? "✓" : "!"), st.texto)),
            h("div", { class: "medidor-trilho", role: "img", "aria-label": `${pct(atual.pct)} da RCL; limite máximo 54%` },
              h("div", { class: `medidor-fill st-bg-${st.chave}`, style: `width:${Math.min(100, ((atual.pct ?? 0) / 60) * 100)}%` }),
              ...[48.6, 51.3, 54].map((l) => h("div", { class: "medidor-marca", style: `left:${(l / 60) * 100}%` }))),
            h("div", { class: "medidor-legenda" }, "0%", h("span", null, "marcas: alerta 48,6% · prudencial 51,3% · máximo 54%"), "60%"))
        : aviso(`Sem RGF para ${e.ano}.`),
      tituloGrafico("Histórico", "Despesa total com pessoal em % da RCL — último período informado de cada ano."),
      el,
      tabela([{ titulo: "Ano" }, { titulo: "Período" }, { titulo: "Despesa com pessoal", numerica: true },
        { titulo: "RCL", numerica: true }, { titulo: "% RCL", numerica: true }, { titulo: "Situação" }],
        serie.map((s) => [s.ano, `${s.periodo}º ${s.periodicidade === "Q" ? "quadr." : "sem."}`,
          brlCompleto(s.dtp), brlCompleto(s.rcl), pct(s.pct), s.situacao])),
    ));
}

/* --------------------------------------------------------------- contratos */
export function contratos(e: Estado): HTMLElement {
  const t = lerTema();
  const c = e.mun.contratos;
  if (!c.resumo.length) {
    return secao("contratos", "Contratos", "Contratos publicados no PNCP.",
      cartao(aviso("Nenhum contrato deste município foi encontrado no PNCP.")));
  }
  const temAno = c.resumo.some((r) => r.ano === e.ano);
  const anoRef = temAno ? e.ano : null;
  const res = temAno ? c.resumo.find((r) => r.ano === e.ano)! : {
    ano: 0, n: c.resumo.reduce((s, r) => s + r.n, 0), valor: c.resumo.reduce((s, r) => s + r.valor, 0),
    valor_real: c.resumo.reduce((s, r) => s + (r.valor_real ?? 0), 0),
  };
  const forn = c.fornecedores.filter((f) => f.ano === anoRef).slice(0, 10);
  const cats = c.categorias.filter((x) => (anoRef ? x.ano === anoRef : true));
  const catAgg = new Map<string, number>();
  for (const x of cats) catAgg.set(x.categoria, (catAgg.get(x.categoria) ?? 0) + x.valor);
  const partes: Parte[] = [...catAgg.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6)
    .map(([nome, valor], i) => ({ nome, valor, cor: t.series[i] }));

  const el = areaGrafico(Math.max(160, forn.length * 34 + 20));
  queueMicrotask(() => {
    if (forn.length) barrasHorizontais(el, forn.map((f) => titulo(f.nome)), forn.map((f) => f.valor), t.series[0]);
  });

  // Lista pesquisável
  const busca = h("input", { type: "search", placeholder: "Buscar por fornecedor, objeto ou CNPJ…",
    "aria-label": "Buscar contratos", class: "busca" });
  const corpo = h("tbody");
  const contador = h("p", { class: "contador" });
  const lista = c.lista.filter((x) => (anoRef ? x.ano === anoRef : true));
  function renderLista() {
    const q = busca.value.trim().toLowerCase();
    const filtrada = lista.filter((x) => !q ||
      `${x.fornecedor} ${x.objeto} ${x.documento ?? ""} ${x.unidade ?? ""}`.toLowerCase().includes(q));
    corpo.replaceChildren(...filtrada.slice(0, 60).map((x) => h("tr", null,
      h("td", { class: "nowrap" }, dataBR(x.data)),
      h("td", null, h("div", { class: "forn" }, titulo(x.fornecedor)), h("div", { class: "doc" }, x.documento ?? "")),
      h("td", null, h("div", null, x.objeto), h("div", { class: "doc" }, `${x.categoria}${x.unidade ? ` · ${titulo(x.unidade)}` : ""}`)),
      h("td", { class: "num nowrap" }, brlCompleto(x.valor)))));
    contador.textContent = `${inteiro(Math.min(60, filtrada.length))} de ${inteiro(filtrada.length)} contratos exibidos${lista.length < res.n ? ` (lista limitada aos ${lista.length} mais recentes)` : ""}.`;
  }
  busca.addEventListener("input", renderLista);
  renderLista();

  return secao("contratos", "Contratos e fornecedores",
    "Contratos publicados pela prefeitura no Portal Nacional de Contratações Públicas (PNCP).",
    cartao(
      !temAno ? aviso(`Sem contratos publicados no PNCP em ${e.ano}; exibindo todos os anos disponíveis.`) : null,
      tiles([
        { rotulo: "Contratos publicados", valor: inteiro(res.n), detalhe: anoRef ? `Assinados em ${anoRef}` : "Todos os anos" },
        { rotulo: "Valor contratado", valor: brl(e.real ? res.valor_real : res.valor), detalhe: "Soma do valor global dos contratos" },
        forn[0] ? { rotulo: "Maior fornecedor", valor: brl(forn[0].valor), detalhe: titulo(forn[0].nome) } : { rotulo: "Maior fornecedor", valor: "—" },
      ]),
      partes.length ? h("div", { class: "bloco" }, tituloGrafico("Por tipo de contratação"), barraSegmentada(partes, brl)) : null,
      h("hr"),
      tituloGrafico("Maiores fornecedores", "Soma do valor global dos contratos (valores nominais)."),
      forn.length ? el : aviso("Sem fornecedores no período."),
      tabela([{ titulo: "Fornecedor" }, { titulo: "CNPJ/CPF" }, { titulo: "Contratos", numerica: true }, { titulo: "Valor", numerica: true }],
        forn.map((f) => [titulo(f.nome), f.documento ?? "—", f.n, brlCompleto(f.valor)])),
      h("hr"),
      tituloGrafico("Lista de contratos"),
      busca,
      h("div", { class: "tabela-scroll" }, h("table", { class: "contratos" },
        h("thead", null, h("tr", null, h("th", null, "Assinatura"), h("th", null, "Fornecedor"),
          h("th", null, "Objeto"), h("th", { class: "num" }, "Valor"))), corpo)),
      contador,
      aviso("Valor global = valor total previsto no contrato, não o valor efetivamente pago. CPFs de pessoas físicas são parcialmente ocultados (LGPD)."),
    ));
}

/* ------------------------------------------------------------- comparativo */
const METRICAS: { chave: keyof Indicador; nome: string; formato: (v: number) => string; desc: string }[] = [
  { chave: "despesa_per_capita_real", nome: "Gasto por habitante", formato: brl, desc: "Despesa liquidada ÷ população, em reais de hoje." },
  { chave: "receita_per_capita_real", nome: "Receita por habitante", formato: brl, desc: "Receita arrecadada ÷ população, em reais de hoje." },
  { chave: "pct_saude", nome: "% gasto em saúde", formato: (v) => pct(v), desc: "Função Saúde ÷ despesa total por função." },
  { chave: "pct_educacao", nome: "% gasto em educação", formato: (v) => pct(v), desc: "Função Educação ÷ despesa total por função." },
  { chave: "pct_investimento", nome: "% em investimentos", formato: (v) => pct(v), desc: "Obras e equipamentos ÷ despesa liquidada." },
  { chave: "pct_pessoal_rcl", nome: "Pessoal / RCL (LRF)", formato: (v) => pct(v), desc: "Despesa com pessoal em % da receita corrente líquida." },
  { chave: "pct_dependencia_transferencias", nome: "Dependência de transferências", formato: (v) => pct(v), desc: "Transferências ÷ receita arrecadada." },
];

export function comparativo(e: Estado): HTMLElement {
  const t = lerTema();
  const sel = h("select", { "aria-label": "Indicador", class: "select" },
    ...METRICAS.map((m, i) => h("option", { value: String(i) }, m.nome)));
  const desc = h("p", { class: "graf-desc" });
  const el = areaGrafico(320);
  const nota = h("div");
  const tab = h("div");

  function render() {
    const m = METRICAS[Number(sel.value)];
    desc.textContent = m.desc;
    const linhas = e.indicadores
      .filter((i) => i.ano === e.ano && i[m.chave] != null)
      .sort((a, b) => (b[m.chave] as number) - (a[m.chave] as number));
    const faltando = e.municipios.filter((mu) => mu.anos.length && !linhas.some((l) => l.cod_ibge === mu.cod_ibge));
    nota.replaceChildren(faltando.length
      ? aviso(`Sem dados de ${e.ano} para: ${faltando.map((f) => f.nome).join(", ")}.`) : document.createTextNode(""));
    tab.replaceChildren(tabela([{ titulo: "Município" }, { titulo: m.nome, numerica: true }],
      linhas.map((l) => [l.nome, m.formato(l[m.chave] as number)])));
    echartsRender(linhas, m);
  }

  function echartsRender(linhas: Indicador[], m: (typeof METRICAS)[number]) {
    el.style.height = `${Math.max(160, linhas.length * 36 + 20)}px`;
    const idx = linhas.findIndex((l) => l.cod_ibge === e.mun.cod_ibge);
    return barrasHorizontaisFormat(el, linhas.map((l) => l.nome), linhas.map((l) => l[m.chave] as number),
      t.series[0], idx, m.formato);
  }

  sel.addEventListener("change", render);
  queueMicrotask(render);

  return secao("comparativo", "Comparação com o Entorno do DF",
    `Como ${e.mun.nome} se compara aos municípios vizinhos em ${e.ano}.`,
    cartao(h("div", { class: "controle-linha" }, h("label", null, "Indicador ", sel)), desc, el, nota, tab));
}

function barrasHorizontaisFormat(el: HTMLElement, nomes: string[], valores: number[], cor: string,
  destaque: number, fmt: (v: number) => string) {
  const n = [...nomes].reverse();
  const v = [...valores].reverse();
  const d = destaque >= 0 ? nomes.length - 1 - destaque : -1;
  const esq = larguraRotulos(n, el);
  return grafico(el, (t) => ({
    ...base(t),
    grid: { left: esq, right: 100, top: 4, bottom: 4, containLabel: false },
    xAxis: { ...eixoValor(t), show: false },
    yAxis: { type: "category", data: n, axisTick: { show: false }, axisLine: { show: false },
      axisLabel: { width: esq - 12, overflow: "truncate",
        formatter: (s: string) => (n.indexOf(s) === d ? `{b|${s}}` : `{a|${s}}`),
        rich: { a: { fontSize: 12, color: t.textSecondary },
          b: { fontSize: 12, fontWeight: 700, color: t.textPrimary } } } },
    tooltip: { ...(base(t).tooltip as object), trigger: "item",
      formatter: (x: { name: string; value: number }) => `<strong>${fmt(x.value)}</strong><br>${esc(x.name)}` },
    series: [{
      type: "bar", barMaxWidth: 20,
      data: v.map((val, i) => ({ value: val, itemStyle: { color: i === d ? cor : t.neutro, borderRadius: [0, 4, 4, 0] } })),
      label: { show: true, position: "right", color: t.textSecondary, fontSize: 12,
        formatter: (x: { value: number }) => fmt(x.value) },
    }],
  }));
}

/* --------------------------------------------------------------- sobre */
export function sobre(e: Estado): HTMLElement {
  const m = e.meta;
  const achados = e.mun.qualidade;
  const etapas = [
    ["APIs públicas", "SICONFI · PNCP · BCB"],
    ["Bronze", "JSON bruto versionado, ingestão incremental"],
    ["dbt + DuckDB", "staging → intermediate → gold, testes de qualidade"],
    ["JSON estático", "um arquivo por município"],
    ["Este site", "GitHub Pages, atualizado pelo GitHub Actions"],
  ];
  return secao("sobre", "Sobre os dados", "De onde vêm os números, como são tratados e o que observar.",
    cartao(
      h("ol", { class: "fluxo", "aria-label": "Fluxo do pipeline de dados" },
        ...etapas.map(([a, b]) => h("li", null, h("strong", null, a), h("span", null, b)))),
      h("div", { class: "sobre-grid" },
        h("div", null,
          h("h3", null, "Fontes"),
          h("ul", { class: "lista" }, ...m.fontes.map((f) =>
            h("li", null, h("a", { href: f.url, target: "_blank", rel: "noopener" }, f.nome), ` — ${f.itens}`)))),
        h("div", null,
          h("h3", null, "Atualização"),
          h("ul", { class: "lista" },
            h("li", null, `Dados coletados em ${dataBR(m.ultima_ingestao ?? m.gerado_em)}`),
            h("li", null, `Inflação (IPCA) até ${mesAno(m.ipca_referencia)}`),
            m.testes ? h("li", null, `${inteiro(m.testes.pass ?? 0)} de ${inteiro(m.testes.total)} testes de qualidade aprovados na última execução`) : null,
            h("li", null, `Versão do pipeline ${m.versao}`)))),
      h("h3", null, "Como ler os números"),
      h("ul", { class: "lista" },
        h("li", null, "Valores consolidados da prefeitura, sem operações intra-orçamentárias (repasses entre órgãos do próprio município), para não contar o mesmo real duas vezes."),
        h("li", null, "Despesa liquidada = o bem ou serviço foi entregue. É diferente de empenhada (reservada) e de paga."),
        h("li", null, "Valores “em reais de hoje” corrigem cada ano pelo IPCA médio do ano até o último mês disponível."),
        h("li", null, "Despesa por área usa o balanço anual (DCA) nos anos encerrados e o RREO no ano corrente."),
        h("li", null, "Os dados são declarados pela própria prefeitura ao Tesouro Nacional; erros de envio aparecem aqui como foram enviados.")),
      h("h3", null, `Achados de qualidade — ${e.mun.nome}`),
      achados.length
        ? h("ul", { class: "achados" }, ...achados.map((a) =>
            h("li", { class: `achado achado-${a.severidade}` },
              h("span", { class: "achado-ano" }, a.ano ? String(a.ano) : "—"),
              h("span", null, a.descricao))))
        : h("p", null, "Nenhuma inconsistência detectada pelas regras automáticas."),
      h("p", { class: "disclaimer" },
        "Projeto independente e sem vínculo com a prefeitura ou qualquer órgão público. ",
        REPO_URL ? h("a", { href: REPO_URL, target: "_blank", rel: "noopener" }, "Código-fonte no GitHub") : null,
        REPO_URL ? " · " : null,
        h("a", { href: `${import.meta.env.BASE_URL}dbt/`, target: "_blank", rel: "noopener" }, "Documentação técnica do modelo de dados (dbt)"),
        "."),
    ));
}

export { eixoBRL };
