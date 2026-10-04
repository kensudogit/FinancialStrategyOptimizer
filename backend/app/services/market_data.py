"""株・FX の OHLCV。実データはアダプタ経由。取れないときだけ決定的サンプル。"""

from __future__ import annotations

import hashlib
import os
import time
from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.services.adapters import fetch_stockai_bars, fetch_stooq_bars, fetch_yahoo_bars

CATALOG = {
    "stock": [
        {"symbol": "7203.T", "name": "トヨタ自動車", "source": "StockPricePredictionTool"},
        {"symbol": "6758.T", "name": "ソニーグループ", "source": "StockPricePredictionTool"},
        {"symbol": "9984.T", "name": "ソフトバンクグループ", "source": "StockPricePredictionTool"},
        {"symbol": "8306.T", "name": "三菱UFJフィナンシャル・グループ", "source": "StockPricePredictionTool"},
        {"symbol": "9432.T", "name": "日本電信電話", "source": "StockPricePredictionTool"},
    ],
    "fx": [
        {"symbol": "USDJPY", "name": "ドル円", "source": "fx"},
        {"symbol": "EURUSD", "name": "ユーロドル", "source": "fx"},
        {"symbol": "GBPUSD", "name": "ポンドドル", "source": "fx"},
    ],
}

_CACHE: dict[tuple[str, str, int], tuple[float, pd.DataFrame, str]] = {}
_CACHE_TTL_SEC = 15 * 60


def _use_live() -> bool:
    if os.getenv("FSO_FORCE_SAMPLE") == "1" or os.getenv("PYTEST_CURRENT_TEST"):
        return False
    return os.getenv("FSO_ALLOW_LIVE_DATA", "1") != "0"


def _stable_seed(symbol: str, seed: int) -> int:
    digest = hashlib.md5(symbol.encode("utf-8")).hexdigest()[:8]
    return (seed * 100_003 + int(digest, 16)) % (2**31 - 1)


def generate_ohlcv(symbol: str, asset_class: str, bars: int = 260, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(_stable_seed(symbol, seed))
    start_px = 1800.0 if asset_class == "stock" else (150.0 if symbol.endswith("JPY") else 1.08)
    mu = 0.00035 if asset_class == "stock" else 0.00008
    sigma = 0.013 if asset_class == "stock" else 0.0055
    rets = rng.normal(mu, sigma, bars)
    close = start_px * np.exp(np.cumsum(rets))
    noise = rng.normal(0, sigma * start_px * 0.15, bars)
    high = close + np.abs(noise) + rng.uniform(0.1, 1.2, bars)
    low = close - np.abs(noise) - rng.uniform(0.1, 1.2, bars)
    open_ = np.concatenate([[close[0]], close[:-1]])
    volume = rng.integers(80_000, 420_000, bars).astype(float)
    start = date.today() - timedelta(days=bars + 20)
    days: list[date] = []
    cursor = start
    while len(days) < bars:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor += timedelta(days=1)
    return pd.DataFrame(
        {
            "ts": [d.isoformat() for d in days],
            "open": open_.astype(float),
            "high": np.maximum(high, np.maximum(open_, close)).astype(float),
            "low": np.minimum(low, np.minimum(open_, close)).astype(float),
            "close": close.astype(float),
            "volume": volume,
        }
    )


def load_bars(symbol: str, asset_class: str, bars: int = 520, seed: int = 1) -> tuple[pd.DataFrame, str]:
    known = {item["symbol"] for item in CATALOG.get(asset_class, [])}
    if symbol not in known:
        raise ValueError(f"未知の銘柄です: {symbol} ({asset_class})")
    cache_key = (symbol, asset_class, bars)
    cached = _CACHE.get(cache_key)
    if cached and time.monotonic() - cached[0] < _CACHE_TTL_SEC:
        return cached[1].copy(), cached[2]
    df: pd.DataFrame | None = None
    source = ""
    if _use_live():
        if asset_class == "stock":
            df = fetch_stockai_bars(symbol, bars)
            if df is not None:
                source = "stockai-http"
        if df is None:
            df = fetch_yahoo_bars(symbol, asset_class, bars)
            if df is not None:
                source = f"yahoo:{symbol}"
        if df is None:
            df = fetch_stooq_bars(symbol, asset_class, bars)
            if df is not None:
                source = f"stooq:{symbol}"
    if df is None:
        df = generate_ohlcv(symbol, asset_class, bars=bars, seed=seed)
        source = "sample:stockai-style" if asset_class == "stock" else "sample:fx-style"
    if source.startswith(("stooq", "stockai", "yahoo")):
        _CACHE[cache_key] = (time.monotonic(), df.copy(), source)
    return df, source
