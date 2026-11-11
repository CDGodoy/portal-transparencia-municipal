// Paleta validada (dataviz: CVD/normal-vision/contraste) — valores vêm do CSS para que
// o modo escuro troque tudo num lugar só.

export interface Tema {
  surface: string;
  textPrimary: string;
  textSecondary: string;
  muted: string;
  grid: string;
  axis: string;
  series: string[];
  neutro: string;
  status: { good: string; warning: string; serious: string; critical: string };
}

function v(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function lerTema(): Tema {
  return {
    surface: v("--surface-1"),
    textPrimary: v("--text-primary"),
    textSecondary: v("--text-secondary"),
    muted: v("--text-muted"),
    grid: v("--gridline"),
    axis: v("--baseline"),
    series: [1, 2, 3, 4, 5, 6, 7, 8].map((i) => v(`--series-${i}`)),
    neutro: v("--neutral-mark"),
    status: {
      good: v("--status-good"),
      warning: v("--status-warning"),
      serious: v("--status-serious"),
      critical: v("--status-critical"),
    },
  };
}
