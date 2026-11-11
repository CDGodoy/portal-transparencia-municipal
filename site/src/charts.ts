import { BarChart, LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  MarkAreaComponent,
  MarkLineComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";
import { eixoBRL } from "./format";
import { lerTema, type Tema } from "./theme";

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkLineComponent,
  MarkAreaComponent,
  SVGRenderer,
]);

const instancias = new Set<echarts.ECharts>();

export function descartarGraficos(): void {
  for (const c of instancias) c.dispose();
  instancias.clear();
}

const ro = new ResizeObserver((entries) => {
  for (const e of entries) {
    const inst = echarts.getInstanceByDom(e.target as HTMLElement);
    inst?.resize();
  }
});

export function grafico(el: HTMLElement, opcoes: (t: Tema) => EChartsCoreOption): echarts.ECharts {
  const anterior = echarts.getInstanceByDom(el);
  if (anterior) {
    instancias.delete(anterior);
    anterior.dispose();
  }
  const inst = echarts.init(el, null, { renderer: "svg" });
  inst.setOption(opcoes(lerTema()));
  instancias.add(inst);
  ro.observe(el);
  return inst;
}

/** Base comum: grade em hairline sólida e recessiva, tipografia do sistema, tooltip sóbrio. */
export function base(t: Tema): EChartsCoreOption {
  return {
    animationDuration: 400,
    textStyle: { fontFamily: "inherit", color: t.textSecondary },
    tooltip: {
      backgroundColor: t.surface,
      borderColor: t.grid,
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: t.textPrimary, fontSize: 13 },
      extraCssText: "box-shadow: 0 4px 16px rgba(0,0,0,.08); border-radius: 8px;",
    },
  };
}

export function eixoValor(t: Tema, formatter: (v: number) => string = eixoBRL) {
  return {
    type: "value" as const,
    axisLabel: { color: t.muted, formatter, fontSize: 12 },
    splitLine: { lineStyle: { color: t.grid, width: 1, type: "solid" as const } },
    axisLine: { show: false },
    axisTick: { show: false },
  };
}

export function eixoCategoria(t: Tema, data: (string | number)[]) {
  return {
    type: "category" as const,
    data,
    axisLabel: { color: t.muted, fontSize: 12 },
    axisLine: { lineStyle: { color: t.axis } },
    axisTick: { show: false },
  };
}

/** Marcador de série para tooltips: traço curto na cor da série (não caixa). */
export function chave(cor: string): string {
  return `<span style="display:inline-block;width:12px;height:2px;background:${cor};vertical-align:middle;margin-right:6px;border-radius:1px"></span>`;
}

export function esc(s: string): string {
  return s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
