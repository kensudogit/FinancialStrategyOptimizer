from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.backtest import public_backtest, run_backtest
from app.services.kpi import radar_from_kpi
from app.services.optimizer import search_params
from app.services.walk_forward import run_walk_forward


def compare_strategies(
    df: pd.DataFrame,
    strategies: list[str],
    *,
    fee_bps: float = 5.0,
    seed: int = 1,
    optimize: bool = True,
    method: str = "grid",
    max_trials: int = 48,
    time_limit_ms: int = 20000,
    include_walk_forward: bool = True,
    precomputed: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    ranking = []
    series = []
    for name in strategies:
        reuse = (precomputed or {}).get(name)
        if reuse:
            bt = reuse["best_backtest"]
            params = reuse["best"]["params"]
            note = reuse["note"]
            optimized = True
        elif optimize:
            opt = search_params(
                df,
                name,
                method=method,
                max_trials=max_trials,
                time_limit_ms=time_limit_ms,
                seed=seed,
                fee_bps=fee_bps,
            )
            bt = opt["best_backtest"]
            params = opt["best"]["params"]
            note = opt["note"]
            optimized = True
        else:
            raw = run_backtest(df, name, None, fee_bps)
            bt = public_backtest(raw)
            params = bt["params"]
            note = bt["note"]
            optimized = False
        wf = run_walk_forward(df, name, params, fee_bps) if include_walk_forward else None
        robustness = None
        if wf and wf.get("status") == "success":
            robustness = wf["summary"]["robustness"]
        radar = radar_from_kpi(bt["kpi"], robustness)
        ranking.append(
            {
                "strategy": name,
                "params": params,
                "kpi": bt["kpi"],
                "radar": radar,
                "walk_forward": wf,
                "optimized": optimized,
                "note": note,
            }
        )
        series.append({"name": name, "values": [axis["value"] for axis in radar], "axes": [axis["axis"] for axis in radar]})

    ranking.sort(key=lambda x: x["kpi"]["objective"], reverse=True)
    return {"ranking": ranking, "radar_series": series}
