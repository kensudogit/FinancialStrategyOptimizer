import type { Catalog, PipelineOut } from "@/lib/types";

export function catalog(overrides: Partial<Catalog> = {}): Catalog {
  return {
    assets: {
      stock: [{ symbol: "7203.T", name: "トヨタ自動車", source: "StockPricePredictionTool", sector: "自動車" }],
      fx: [{ symbol: "USDJPY", name: "ドル円", source: "fx", sector: "FX" }],
    },
    strategies: [
      { id: "sma_crossover", label: "SMAクロス", origin: "StockPricePredictionTool" },
      { id: "buy_hold", label: "バイ＆ホールド", origin: "baseline" },
    ],
    integrations: [
      { id: "backtest", name: "Backtest Engine", path: "local", available: true, role: "KPI" },
    ],
    ...overrides,
  };
}

export function pipelineOut(overrides: Partial<PipelineOut> = {}): PipelineOut {
  const kpi = {
    total_return: 0.1,
    buy_hold_return: 0.05,
    sharpe: 0.8,
    max_drawdown: -0.1,
    win_rate: 0.5,
    trades: 4,
    calmar: 1,
    profit_factor: 1.2,
    alpha_vs_buy_hold: 0.05,
    objective: 0.9,
  };
  return {
    symbol: "7203.T",
    asset_class: "stock",
    bars: 80,
    source: "sample:stockai-style",
    backtests: [
      {
        engine: "pandas",
        source: "sample:stockai-style",
        strategy: "sma_crossover",
        params: { fast: 10, slow: 30 },
        kpi,
        equity_curve: [
          { ts: "2024-01-01", equity: 1, buy_hold: 1, drawdown: 0 },
          { ts: "2024-01-02", equity: 1.02, buy_hold: 1.01, drawdown: 0 },
        ],
        radar: [{ axis: "Sharpe", value: 50 }],
        note: "候補",
      },
    ],
    optimizations: [
      { strategy: "sma_crossover", exhausted: false, note: "候補", best: { params: { fast: 10, slow: 30 } } },
    ],
    comparison: {
      symbol: "7203.T",
      ranking: [
        {
          strategy: "sma_crossover",
          params: { fast: 10, slow: 30 },
          kpi,
          radar: [{ axis: "Sharpe", value: 50 }],
          walk_forward: null,
          optimized: true,
          note: "候補",
        },
      ],
      radar_series: [{ name: "sma_crossover", values: [50, 40, 30, 20, 10, 5], axes: ["Sharpe", "リターン", "耐DD", "勝率", "堅牢性", "売買回数"] }],
    },
    report_markdown: "# レポート",
    report_html: "<p>レポート</p>",
    persisted_run_id: null,
    ...overrides,
  };
}
