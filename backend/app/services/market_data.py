"""株・FX の OHLCV。実データはアダプタ経由。取れないときだけ決定的サンプル。"""

from __future__ import annotations

import hashlib
import os
import time
from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.services.adapters import fetch_stockai_bars, fetch_stooq_bars, fetch_yahoo_bars

def _stock(symbol: str, name: str, sector: str) -> dict[str, str]:
    return {"symbol": symbol, "name": name, "sector": sector, "source": "StockPricePredictionTool"}


def _fx(symbol: str, name: str) -> dict[str, str]:
    return {"symbol": symbol, "name": name, "sector": "FX", "source": "fx"}


CATALOG = {
    "stock": [
        _stock("7203.T", "トヨタ自動車", "自動車"),
        _stock("7267.T", "ホンダ", "自動車"),
        _stock("7201.T", "日産自動車", "自動車"),
        _stock("6902.T", "デンソー", "自動車部品"),
        _stock("5108.T", "ブリヂストン", "ゴム"),
        _stock("6758.T", "ソニーグループ", "電機"),
        _stock("6501.T", "日立製作所", "電機"),
        _stock("6701.T", "日本電気", "電機"),
        _stock("6702.T", "富士通", "電機"),
        _stock("6594.T", "ニデック", "電機"),
        _stock("6861.T", "キーエンス", "電機"),
        _stock("6954.T", "ファナック", "機械"),
        _stock("6273.T", "SMC", "機械"),
        _stock("6367.T", "ダイキン工業", "機械"),
        _stock("7011.T", "三菱重工業", "機械"),
        _stock("8035.T", "東京エレクトロン", "半導体"),
        _stock("6857.T", "アドバンテスト", "半導体"),
        _stock("4063.T", "信越化学工業", "化学"),
        _stock("4452.T", "花王", "化学"),
        _stock("4901.T", "富士フイルムホールディングス", "化学"),
        _stock("4502.T", "武田薬品工業", "医薬品"),
        _stock("4519.T", "中外製薬", "医薬品"),
        _stock("4568.T", "第一三共", "医薬品"),
        _stock("4543.T", "テルモ", "精密"),
        _stock("7751.T", "キヤノン", "精密"),
        _stock("6098.T", "リクルートホールディングス", "サービス"),
        _stock("4661.T", "オリエンタルランド", "サービス"),
        _stock("9983.T", "ファーストリテイリング", "小売"),
        _stock("3382.T", "セブン&アイ・ホールディングス", "小売"),
        _stock("8267.T", "イオン", "小売"),
        _stock("2802.T", "味の素", "食品"),
        _stock("2914.T", "日本たばこ産業", "食品"),
        _stock("7974.T", "任天堂", "ゲーム"),
        _stock("3659.T", "ネクソン", "ゲーム"),
        _stock("9984.T", "ソフトバンクグループ", "通信"),
        _stock("9432.T", "日本電信電話", "通信"),
        _stock("9433.T", "KDDI", "通信"),
        _stock("9434.T", "ソフトバンク", "通信"),
        _stock("8058.T", "三菱商事", "商社"),
        _stock("8001.T", "伊藤忠商事", "商社"),
        _stock("8031.T", "三井物産", "商社"),
        _stock("8306.T", "三菱UFJフィナンシャル・グループ", "銀行"),
        _stock("8316.T", "三井住友フィナンシャルグループ", "銀行"),
        _stock("8411.T", "みずほフィナンシャルグループ", "銀行"),
        _stock("8604.T", "野村ホールディングス", "証券"),
        _stock("8766.T", "東京海上ホールディングス", "保険"),
        _stock("8697.T", "日本取引所グループ", "金融"),
        _stock("1321.T", "NEXT FUNDS 日経225連動型上場投信", "ETF"),
    ],
    "fx": [
        _fx("USDJPY", "ドル円"),
        _fx("EURJPY", "ユーロ円"),
        _fx("GBPJPY", "ポンド円"),
        _fx("AUDJPY", "豪ドル円"),
        _fx("NZDJPY", "キウイ円"),
        _fx("CADJPY", "カナダドル円"),
        _fx("CHFJPY", "スイスフラン円"),
        _fx("EURUSD", "ユーロドル"),
        _fx("GBPUSD", "ポンドドル"),
        _fx("AUDUSD", "豪ドル米ドル"),
        _fx("USDCHF", "ドルスイス"),
        _fx("USDCAD", "ドルカナダ"),
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
