"""戦略レジストリ。StockAI の SMA と fx の RSI/MACD 系を同じ信号インタフェースに揃える。"""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

SignalFn = Callable[[pd.Series, dict], pd.Series]


def _sma(close: pd.Series, window: int) -> pd.Series:
    return close.rolling(int(window)).mean()


def sma_crossover(close: pd.Series, params: dict) -> pd.Series:
    """StockPricePpredictionTool/backend/app/backtest/engine.py と同じクロス。"""
    fast = int(params.get("fast", 10))
    slow = int(params.get("slow", 30))
    f = _sma(close, fast)
    s = _sma(close, slow)
    sig = pd.Series(0, index=close.index, dtype=float)
    sig[f > s] = 1
    sig[f < s] = -1
    return sig.fillna(0)


def rsi_series(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / (loss + 1e-12)
    return 100 - (100 / (1 + rs))


def rsi_mean_reversion(close: pd.Series, params: dict) -> pd.Series:
    """fx の RSI 逆張りに相当。売られすぎで買い、買われすぎでフラット。"""
    period = int(params.get("period", 14))
    low = float(params.get("oversold", 30))
    high = float(params.get("overbought", 70))
    rsi = rsi_series(close, period)
    sig = pd.Series(0.0, index=close.index)
    sig[rsi < low] = 1
    sig[rsi > high] = -1
    return sig.fillna(0)


def macd_cross(close: pd.Series, params: dict) -> pd.Series:
    """fx Backtrader RSI/MACD 系の MACD クロス。"""
    fast = int(params.get("fast", 12))
    slow = int(params.get("slow", 26))
    signal = int(params.get("signal", 9))
    ema_f = close.ewm(span=fast, adjust=False).mean()
    ema_s = close.ewm(span=slow, adjust=False).mean()
    line = ema_f - ema_s
    sig_line = line.ewm(span=signal, adjust=False).mean()
    out = pd.Series(0.0, index=close.index)
    out[line > sig_line] = 1
    out[line < sig_line] = -1
    return out.fillna(0)


def donchian_breakout(close: pd.Series, params: dict) -> pd.Series:
    lookback = int(params.get("lookback", 20))
    hh = close.rolling(lookback).max()
    ll = close.rolling(lookback).min()
    sig = pd.Series(0.0, index=close.index)
    sig[close >= hh] = 1
    sig[close <= ll] = -1
    return sig.fillna(0)


def buy_hold(close: pd.Series, params: dict) -> pd.Series:
    return pd.Series(1.0, index=close.index)


STRATEGIES: dict[str, dict] = {
    "sma_crossover": {
        "label": "SMAクロス",
        "origin": "StockPricePredictionTool",
        "fn": sma_crossover,
        "defaults": {"fast": 10, "slow": 30},
        "space": {"fast": [5, 8, 10, 15, 20], "slow": [20, 30, 40, 60]},
    },
    "rsi_mean_reversion": {
        "label": "RSI逆張り",
        "origin": "fx",
        "fn": rsi_mean_reversion,
        "defaults": {"period": 14, "oversold": 30, "overbought": 70},
        "space": {"period": [7, 14, 21], "oversold": [25, 30, 35], "overbought": [65, 70, 75]},
    },
    "macd_cross": {
        "label": "MACDクロス",
        "origin": "fx",
        "fn": macd_cross,
        "defaults": {"fast": 12, "slow": 26, "signal": 9},
        "space": {"fast": [8, 12, 16], "slow": [20, 26, 32], "signal": [7, 9, 12]},
    },
    "donchian_breakout": {
        "label": "ドンチャン・ブレイク",
        "origin": "Backtest Engine",
        "fn": donchian_breakout,
        "defaults": {"lookback": 20},
        "space": {"lookback": [10, 15, 20, 30, 40]},
    },
    "buy_hold": {
        "label": "バイ＆ホールド",
        "origin": "baseline",
        "fn": buy_hold,
        "defaults": {},
        "space": {},
    },
}


def catalog() -> list[dict]:
    return [
        {"id": key, "label": spec["label"], "origin": spec["origin"], "defaults": spec["defaults"]}
        for key, spec in STRATEGIES.items()
    ]


def signal_for(name: str, close: pd.Series, params: dict | None = None) -> pd.Series:
    if name not in STRATEGIES:
        raise ValueError(f"未知の戦略です: {name}")
    spec = STRATEGIES[name]
    merged = {**spec["defaults"], **(params or {})}
    return spec["fn"](close, merged)
