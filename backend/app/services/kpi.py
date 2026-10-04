from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def compute_kpi(strat_rets: pd.Series, buy_hold_rets: pd.Series, trades: int) -> dict[str, float]:
    equity = (1 + strat_rets).cumprod()
    buy_hold = (1 + buy_hold_rets).cumprod()
    drawdown = equity / equity.cummax() - 1
    total_return = float(equity.iloc[-1] - 1)
    bh_return = float(buy_hold.iloc[-1] - 1)
    vol = float(strat_rets.std())
    sharpe = float(strat_rets.mean() / (vol + 1e-12) * np.sqrt(252))
    max_dd = float(drawdown.min())
    active = strat_rets[strat_rets.abs() > 1e-12]
    win_rate = float((active > 0).mean()) if len(active) else 0.0
    gains = float(active[active > 0].sum()) if len(active) else 0.0
    losses = float(-active[active < 0].sum()) if len(active) else 0.0
    profit_factor = gains / (losses + 1e-12)
    calmar = total_return / (abs(max_dd) + 1e-12)
    objective = sharpe - 2.5 * abs(min(0.0, max_dd)) + 0.15 * total_return
    return {
        "total_return": total_return,
        "buy_hold_return": bh_return,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "win_rate": win_rate,
        "trades": float(trades),
        "calmar": float(calmar),
        "profit_factor": float(profit_factor),
        "alpha_vs_buy_hold": total_return - bh_return,
        "objective": float(objective),
    }


def clip01(value: float, lo: float, hi: float) -> float:
    if hi == lo:
        return 0.0
    return float(np.clip((value - lo) / (hi - lo), 0, 1) * 100)


def radar_from_kpi(kpi: dict[str, Any], robustness: float | None = None) -> list[dict[str, float | str]]:
    robust = 50.0 if robustness is None else clip01(robustness, 0.0, 1.0)
    return [
        {"axis": "Sharpe", "value": clip01(float(kpi["sharpe"]), -1.0, 2.5)},
        {"axis": "リターン", "value": clip01(float(kpi["total_return"]), -0.4, 0.8)},
        {"axis": "耐DD", "value": clip01(-float(kpi["max_drawdown"]), 0.0, 0.4)},
        {"axis": "勝率", "value": clip01(float(kpi["win_rate"]), 0.3, 0.7)},
        {"axis": "堅牢性", "value": robust},
        {"axis": "売買回数", "value": clip01(float(kpi["trades"]), 2, 40)},
    ]
