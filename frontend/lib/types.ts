export type AssetClass = "stock" | "fx";

export interface Kpi {
  total_return: number;
  buy_hold_return: number;
  sharpe: number;
  max_drawdown: number;
  win_rate: number;
  trades: number;
  calmar: number;
  profit_factor: number;
  alpha_vs_buy_hold: number;
  objective: number;
}

export interface RadarAxis {
  axis: string;
  value: number;
}

export interface BacktestOut {
  engine: string;
  source: string;
  strategy: string;
  params: Record<string, number | string>;
  kpi: Kpi;
  equity_curve: { ts: string; equity: number; buy_hold: number; drawdown: number }[];
  radar: RadarAxis[];
  note: string;
}

export interface StrategyCompare {
  strategy: string;
  params: Record<string, number | string>;
  kpi: Kpi;
  radar: RadarAxis[];
  walk_forward: { status: string; summary?: { robustness_label: string; robustness: number } } | null;
  optimized: boolean;
  note: string;
}

export interface PipelineOut {
  symbol: string;
  asset_class: AssetClass;
  bars: number;
  source: string;
  backtests: BacktestOut[];
  optimizations: { strategy: string; exhausted: boolean; note: string; best: { params: Record<string, number | string> } }[];
  comparison: {
    symbol: string;
    ranking: StrategyCompare[];
    radar_series: { name: string; values: number[]; axes: string[] }[];
  };
  report_markdown: string;
  report_html: string;
  persisted_run_id: number | null;
}

export interface Catalog {
  assets: Record<AssetClass, { symbol: string; name: string; source: string; sector?: string }[]>;
  strategies: { id: string; label: string; origin: string }[];
  integrations: { id: string; name: string; path: string; available: boolean; role: string }[];
}
