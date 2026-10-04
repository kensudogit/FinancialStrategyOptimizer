"""既存パッケージへの薄い接続。本体は捨てず、ここから参照する。"""

from __future__ import annotations

import os
from pathlib import Path

STOCK_ROOT = Path(os.getenv("STOCKAI_ROOT", r"C:\devlop\StockPricePpredictionTool"))
FX_ROOT = Path(os.getenv("FX_ROOT", r"C:\devlop\fx"))
HEURISTIC_ROOT = Path(os.getenv("HEURISTIC_ROOT", r"C:\devlop\heuristic-optimizer"))

STOCKAI_URL = os.getenv("STOCKAI_URL", "").rstrip("/")
FX_URL = os.getenv("FX_URL", "").rstrip("/")


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
