"""fx/backend/src/backtest/walk_forward.py と同じ IS/OOS スライド。"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.services.backtest import run_backtest


def run_walk_forward(
    df: pd.DataFrame,
    strategy: str,
    params: dict | None = None,
    fee_bps: float = 5.0,
    train_bars: int | None = None,
    test_bars: int | None = None,
    step_bars: int | None = None,
) -> dict[str, Any]:
    n = len(df)
    if train_bars is None:
        train_bars = 120 if n >= 400 else 80
    if test_bars is None:
        test_bars = 40 if n >= 400 else 30
    if step_bars is None:
        step_bars = test_bars
    if n < train_bars + test_bars + 10:
        return {"status": "error", "message": "ウォークフォワードにはデータが足りません"}

    windows = []
    start = 0
    while start + train_bars + test_bars <= len(df):
        is_df = df.iloc[start : start + train_bars].reset_index(drop=True)
        oos_df = df.iloc[start + train_bars : start + train_bars + test_bars].reset_index(drop=True)
        is_bt = run_backtest(is_df, strategy, params, fee_bps)
        oos_bt = run_backtest(oos_df, strategy, params, fee_bps)
        windows.append(
            {
                "start": str(df.iloc[start]["ts"]) if "ts" in df.columns else start,
                "is_win_rate": is_bt["kpi"]["win_rate"],
                "oos_win_rate": oos_bt["kpi"]["win_rate"],
                "is_sharpe": is_bt["kpi"]["sharpe"],
                "oos_sharpe": oos_bt["kpi"]["sharpe"],
            }
        )
        start += step_bars

    if not windows:
        return {"status": "error", "message": "ウィンドウを生成できませんでした"}

    avg_is = sum(w["oos_win_rate"] * 0 + w["is_win_rate"] for w in windows) / len(windows)
    avg_oos = sum(w["oos_win_rate"] for w in windows) / len(windows)
    gap = abs(avg_is - avg_oos)
    if gap < 0.10 and avg_oos >= 0.45:
        grade, label = "good", "堅牢"
    elif gap < 0.20:
        grade, label = "moderate", "普通"
    else:
        grade, label = "weak", "過学習の疑い"
    robustness = max(0.0, 1.0 - gap / 0.30)
    return {
        "status": "success",
        "windows": windows,
        "summary": {
            "avg_in_sample_win_rate": avg_is,
            "avg_out_of_sample_win_rate": avg_oos,
            "is_oos_degradation": gap,
            "robustness": robustness,
            "robustness_grade": grade,
            "robustness_label": label,
        },
    }
