"""単一エンジンのバックテスト。StockAI の pandas 実装を KPI スキーマに拡張する。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.kpi import compute_kpi, radar_from_kpi
from app.services.strategies import STRATEGIES, signal_for


def run_backtest(
    df: pd.DataFrame,
    strategy: str,
    params: dict | None = None,
    fee_bps: float = 5.0,
    source: str = "local",
) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        raise ValueError(f"未知の戦略です: {strategy}")
    close = df["close"].astype(float)
    merged = {**STRATEGIES[strategy]["defaults"], **(params or {})}
    signal = signal_for(strategy, close, merged)
    position = signal.shift(1).fillna(0)
    rets = close.pct_change().fillna(0)
    turnover = position.diff().abs().fillna(0)
    strat_rets = position * rets - turnover * (fee_bps / 10000.0)
    trades = int(turnover.sum() / 2)
    kpi = compute_kpi(strat_rets, rets, trades)
    equity = (1 + strat_rets).cumprod()
    buy_hold = (1 + rets).cumprod()
    drawdown = equity / equity.cummax() - 1
    step = max(1, len(equity) // 80)
    curve = []
    for i in range(0, len(equity), step):
        ts = str(df.iloc[i]["ts"]) if "ts" in df.columns else str(i)
        curve.append(
            {
                "ts": ts,
                "equity": float(equity.iloc[i]),
                "buy_hold": float(buy_hold.iloc[i]),
                "drawdown": float(drawdown.iloc[i]),
            }
        )
    return {
        "engine": "pandas",
        "source": source,
        "strategy": strategy,
        "params": merged,
        "kpi": kpi,
        "equity_curve": curve,
        "radar": radar_from_kpi(kpi),
        "note": f"{STRATEGIES[strategy]['origin']} 由来の戦略を統合エンジンで評価",
        "_returns": strat_rets,
    }


def public_backtest(result: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in result.items() if not k.startswith("_")}
