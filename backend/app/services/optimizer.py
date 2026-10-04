"""パラメータ探索。heuristic-optimizer と同じく seed・制限時間・未証明を最適と呼ばない。"""

from __future__ import annotations

import itertools
import time
from typing import Any

import numpy as np
import pandas as pd

from app.services.backtest import public_backtest, run_backtest
from app.services.strategies import STRATEGIES


def _param_grid(space: dict[str, list]) -> list[dict[str, Any]]:
    if not space:
        return [{}]
    keys = list(space)
    combos = []
    for values in itertools.product(*[space[k] for k in keys]):
        item = dict(zip(keys, values))
        if "fast" in item and "slow" in item and item["fast"] >= item["slow"]:
            continue
        if "oversold" in item and "overbought" in item and item["oversold"] >= item["overbought"]:
            continue
        combos.append(item)
    return combos or [{}]


def _neighbor(rng: np.random.Generator, base: dict[str, Any], space: dict[str, list]) -> dict[str, Any]:
    if not space:
        return dict(base)
    nxt = dict(base)
    key = rng.choice(list(space))
    nxt[key] = rng.choice(space[key])
    if "fast" in nxt and "slow" in nxt and nxt["fast"] >= nxt["slow"]:
        nxt["fast"], nxt["slow"] = min(space.get("fast", [5])), max(space.get("slow", [30]))
    return nxt


def search_params(
    df: pd.DataFrame,
    strategy: str,
    *,
    method: str = "grid",
    max_trials: int = 24,
    time_limit_ms: int = 8000,
    seed: int = 1,
    fee_bps: float = 5.0,
) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        raise ValueError(f"未知の戦略です: {strategy}")
    space = STRATEGIES[strategy]["space"]
    grid = _param_grid(space)
    rng = np.random.default_rng(seed)
    started = time.perf_counter()
    deadline = started + time_limit_ms / 1000.0
    evaluated: list[dict[str, Any]] = []
    seen: set[tuple] = set()

    def evaluate(params: dict[str, Any]) -> None:
        key = tuple(sorted(params.items()))
        if key in seen:
            return
        seen.add(key)
        result = run_backtest(df, strategy, params, fee_bps)
        evaluated.append({"params": result["params"], "kpi": result["kpi"], "result": result})

    if method == "grid":
        for params in grid:
            if time.perf_counter() > deadline or len(evaluated) >= max_trials:
                break
            evaluate(params)
        exhausted = len(evaluated) >= len(grid) and time.perf_counter() <= deadline
    else:
        if grid:
            evaluate(grid[0])
        current = evaluated[0]["params"] if evaluated else STRATEGIES[strategy]["defaults"]
        current_obj = evaluated[0]["kpi"]["objective"] if evaluated else -1e9
        temp = 1.0
        while len(evaluated) < max_trials and time.perf_counter() <= deadline:
            cand = _neighbor(rng, current, space) if method == "sa" else dict(zip(space, [rng.choice(space[k]) for k in space]))
            before = len(evaluated)
            evaluate(cand)
            if len(evaluated) == before:
                continue
            obj = evaluated[-1]["kpi"]["objective"]
            if method == "sa":
                accept = obj >= current_obj or rng.random() < np.exp((obj - current_obj) / max(temp, 1e-3))
                if accept:
                    current, current_obj = evaluated[-1]["params"], obj
                temp *= 0.92
        exhausted = False

    evaluated.sort(key=lambda x: x["kpi"]["objective"], reverse=True)
    if not evaluated:
        fallback = run_backtest(df, strategy, None, fee_bps)
        evaluated = [{"params": fallback["params"], "kpi": fallback["kpi"], "result": fallback}]
        exhausted = True

    proposals = []
    for item in evaluated[:3]:
        proposals.append(
            {
                "params": item["params"],
                "kpi": item["kpi"],
                "proven_best_in_space": bool(exhausted and item is evaluated[0]),
            }
        )
    best = proposals[0]
    note = (
        "格子を走査し切ったので、この探索空間では最良です。全市場の最適とは限りません。"
        if exhausted
        else "時間または試行回数で打ち切った候補です。最適とは呼びません。"
    )
    return {
        "strategy": strategy,
        "method": method,
        "trials": len(evaluated),
        "exhausted": exhausted,
        "best": best,
        "proposals": proposals,
        "note": note,
        "best_backtest": public_backtest(evaluated[0]["result"]),
    }
