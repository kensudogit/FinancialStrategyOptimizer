from __future__ import annotations

from typing import Any

from app.services.compare import compare_strategies
from app.services.market_data import load_bars
from app.services.optimizer import search_params
from app.services.report import render_report


def run_pipeline(
    *,
    asset_class: str,
    symbol: str,
    strategies: list[str],
    fee_bps: float = 5.0,
    bars: int = 520,
    seed: int = 1,
    method: str = "grid",
    max_trials: int = 48,
    time_limit_ms: int = 20000,
    include_walk_forward: bool = True,
    include_report: bool = True,
) -> dict[str, Any]:
    df, source = load_bars(symbol, asset_class, bars=bars, seed=seed)
    names = strategies or ["sma_crossover", "rsi_mean_reversion", "macd_cross"]
    optimizations = [
        search_params(
            df,
            name,
            method=method,
            max_trials=max_trials,
            time_limit_ms=time_limit_ms,
            seed=seed,
            fee_bps=fee_bps,
        )
        for name in names
    ]
    backtests = []
    for item in optimizations:
        item["best_backtest"]["source"] = source
        backtests.append(item["best_backtest"])
    comparison = compare_strategies(
        df,
        names,
        fee_bps=fee_bps,
        seed=seed,
        optimize=True,
        method=method,
        max_trials=max_trials,
        time_limit_ms=time_limit_ms,
        include_walk_forward=include_walk_forward,
        precomputed={item["strategy"]: item for item in optimizations},
    )
    comparison = {"symbol": symbol, "asset_class": asset_class, **comparison}
    markdown, html = ("", "")
    if include_report:
        markdown, html = render_report(symbol, asset_class, source, comparison, optimizations)
    return {
        "symbol": symbol,
        "asset_class": asset_class,
        "bars": len(df),
        "source": source,
        "backtests": backtests,
        "optimizations": [{k: v for k, v in item.items() if k != "best_backtest"} for item in optimizations],
        "comparison": comparison,
        "report_markdown": markdown,
        "report_html": html,
    }
