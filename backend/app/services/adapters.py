"""既存パッケージへの薄い接続。本体は捨てず、ここから参照する。"""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

STOCK_ROOT = Path(os.getenv("STOCKAI_ROOT", r"C:\devlop\StockPricePpredictionTool"))
FX_ROOT = Path(os.getenv("FX_ROOT", r"C:\devlop\fx"))
HEURISTIC_ROOT = Path(os.getenv("HEURISTIC_ROOT", r"C:\devlop\heuristic-optimizer"))

STOCKAI_URL = os.getenv("STOCKAI_URL", "").rstrip("/")
FX_URL = os.getenv("FX_URL", "").rstrip("/")

STOOQ_FX = {"USDJPY": "usdjpy", "EURUSD": "eurusd", "GBPUSD": "gbpusd"}
YAHOO_FX = {"USDJPY": "USDJPY=X", "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X"}
YAHOO_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def to_stooq_symbol(ticker: str, asset_class: str) -> str | None:
    if asset_class == "fx":
        return STOOQ_FX.get(ticker)
    if ticker.endswith(".T"):
        return f"{ticker[:-2].lower()}.jp"
    if ticker.endswith(".JP"):
        return ticker.lower()
    return None


def parse_stooq_csv(text: str, bars: int) -> pd.DataFrame | None:
    raw = (text or "").strip()
    if not raw or raw.lower().startswith("<!doctype") or "No data" in raw:
        return None
    rows = list(csv.DictReader(io.StringIO(raw)))
    if not rows:
        return None
    records = []
    for row in rows[-bars:]:
        date_s = row.get("Date") or row.get("date")
        if not date_s:
            continue
        try:
            records.append(
                {
                    "ts": date_s,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row.get("Volume") or 0),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    if len(records) < 80:
        return None
    return pd.DataFrame(records)


def to_yahoo_symbol(ticker: str, asset_class: str) -> str:
    if asset_class == "fx":
        return YAHOO_FX.get(ticker, f"{ticker}=X")
    return ticker


def parse_yahoo_chart(payload: dict, bars: int) -> pd.DataFrame | None:
    result = (payload.get("chart") or {}).get("result") or []
    if not result:
        return None
    node = result[0]
    stamps = node.get("timestamp") or []
    quote = ((node.get("indicators") or {}).get("quote") or [{}])[0]
    opens = quote.get("open") or []
    highs = quote.get("high") or []
    lows = quote.get("low") or []
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    records = []
    for i, stamp in enumerate(stamps):
        try:
            close = closes[i]
            if close is None:
                continue
            records.append(
                {
                    "ts": datetime.fromtimestamp(int(stamp), tz=timezone.utc).date().isoformat(),
                    "open": float(opens[i] if opens[i] is not None else close),
                    "high": float(highs[i] if highs[i] is not None else close),
                    "low": float(lows[i] if lows[i] is not None else close),
                    "close": float(close),
                    "volume": float(volumes[i] or 0) if i < len(volumes) else 0.0,
                }
            )
        except (IndexError, TypeError, ValueError, OSError):
            continue
    if len(records) < 80:
        return None
    return pd.DataFrame(records[-bars:])


def fetch_yahoo_bars(symbol: str, asset_class: str, bars: int) -> pd.DataFrame | None:
    ticker = to_yahoo_symbol(symbol, asset_class)
    chart_range = "2y" if bars > 200 else "1y" if bars > 80 else "6mo"
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    try:
        with httpx.Client(timeout=12.0, follow_redirects=True) as client:
            resp = client.get(
                url,
                params={"interval": "1d", "range": chart_range},
                headers={"User-Agent": YAHOO_UA, "Accept": "application/json"},
            )
            resp.raise_for_status()
            return parse_yahoo_chart(resp.json(), bars)
    except (httpx.HTTPError, ValueError):
        return None


def fetch_stooq_bars(symbol: str, asset_class: str, bars: int) -> pd.DataFrame | None:
    code = to_stooq_symbol(symbol, asset_class)
    if not code:
        return None
    url = f"https://stooq.com/q/d/l/?s={code}&i=d"
    try:
        with httpx.Client(timeout=8.0, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "FSO/1.0"})
            resp.raise_for_status()
            return parse_stooq_csv(resp.text, bars)
    except httpx.HTTPError:
        return None


def fetch_stockai_bars(symbol: str, bars: int) -> pd.DataFrame | None:
    if not STOCKAI_URL:
        return None
    url = f"{STOCKAI_URL}/api/v1/market/{symbol}/bars"
    try:
        with httpx.Client(timeout=2.0, follow_redirects=True) as client:
            resp = client.get(url, params={"timeframe": "1d", "limit": bars})
            resp.raise_for_status()
            payload = resp.json()
    except (httpx.HTTPError, ValueError):
        return None
    if not isinstance(payload, list) or len(payload) < 80:
        return None
    records = []
    for row in payload[-bars:]:
        try:
            ts = row.get("ts") or row.get("date")
            records.append(
                {
                    "ts": str(ts)[:10],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume") or 0),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    if len(records) < 80:
        return None
    return pd.DataFrame(records)


def describe_assets() -> list[dict[str, str]]:
    return [
        {
            "id": "stockai",
            "name": "StockPricePredictionTool (StockAI)",
            "path": str(STOCK_ROOT),
            "available": (STOCK_ROOT / "backend" / "app" / "backtest" / "engine.py").exists(),
            "role": "株価 OHLCV・SMA/OLS バックテスト・Sharpe/DD KPI",
            "http": STOCKAI_URL or "http://localhost:8000/api/v1/backtest/run",
        },
        {
            "id": "fx",
            "name": "fx",
            "path": str(FX_ROOT),
            "available": (FX_ROOT / "backend" / "src" / "backtest" / "walk_forward.py").exists(),
            "role": "FX OHLCV・RSI/MACD・ウォークフォワード堅牢性",
            "http": FX_URL or "http://localhost:8000/api/pro/backtest/{symbol}",
        },
        {
            "id": "heuristic",
            "name": "Heuristic Optimizer",
            "path": str(HEURISTIC_ROOT),
            "available": (HEURISTIC_ROOT / "backend" / "app" / "services" / "optimizer.py").exists(),
            "role": "複数スタート・seed・制限時間・未証明を最適と呼ばない探索作法",
            "http": "",
        },
        {
            "id": "backtest",
            "name": "Backtest Engine (統合)",
            "path": "backend/app/services/backtest.py",
            "available": True,
            "role": "StockAI pandas エンジンと FX シグナル評価を単一の KPI スキーマに揃える",
            "http": "",
        },
    ]
