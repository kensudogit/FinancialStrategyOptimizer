"""FastAPI 入口。探索・バックテスト本体は services に置く。"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from app.db import SessionLocal, StrategyRun, init_db
from app.models import (
    BacktestRequest,
    CompareRequest,
    OptimizeRequest,
    PipelineRequest,
)
from app.services.adapters import describe_assets
from app.services.backtest import public_backtest, run_backtest
from app.services.compare import compare_strategies
from app.services.market_data import CATALOG, load_bars
from app.services.optimizer import search_params
from app.services.pipeline import run_pipeline
from app.services.report import render_report
from app.services.strategies import catalog as strategy_catalog
from app.services.test_runner import RESULTS_DIR, load_summary, run_all

app = FastAPI(
    title="Financial Strategy Optimizer",
    version="1.0.0",
    description="株・FX戦略のバックテストから比較・レポートまでを統合する層。既存の StockAI / fx は捨てない。",
)

_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:3020").split(",")
    if origin.strip()
]
_allow_all = "*" in _origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _allow_all else _origins,
    allow_credentials=not _allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    try:
        init_db()
    except Exception:
        # 単体テストや Postgres 未起動でも API は動かす
        pass


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tests/summary")
def tests_summary() -> dict:
    return load_summary()


@app.get("/tests/report", response_class=HTMLResponse)
def tests_report() -> str:
    index = RESULTS_DIR / "index.html"
    if index.exists():
        return index.read_text(encoding="utf-8")
    return "<h1>No test report</h1><p>POST /tests/run を先に実行してください。</p>"


@app.get("/tests/files/{name}")
def tests_file(name: str):
    safe = Path(name).name
    path = RESULTS_DIR / safe
    if not path.exists() or not path.is_file():
        raise HTTPException(404, f"{safe} not found")
    return FileResponse(path)


@app.post("/tests/run")
def tests_run() -> dict:
    if os.getenv("ALLOW_TEST_RUN", "true").lower() in {"0", "false", "no"}:
        raise HTTPException(403, "Test runs disabled")
    return {"status": "completed", "summary": run_all()}


@app.get("/catalog")
def catalog() -> dict:
    return {
        "assets": CATALOG,
        "strategies": strategy_catalog(),
        "integrations": describe_assets(),
    }


@app.get("/sample")
def sample() -> dict:
    return {
        "asset_class": "stock",
        "symbol": "7203.T",
        "strategies": ["sma_crossover", "rsi_mean_reversion", "macd_cross"],
        "fee_bps": 5,
        "bars": 520,
        "seed": 1,
        "method": "grid",
        "max_trials": 48,
        "time_limit_ms": 20000,
    }


def _load(req: BacktestRequest):
    try:
        return load_bars(req.symbol, req.asset_class, bars=req.bars, seed=req.seed)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/backtest")
def backtest(req: BacktestRequest) -> dict:
    df, source = _load(req)
    try:
        return public_backtest(run_backtest(df, req.strategy, req.params, req.fee_bps, source))
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/optimize")
def optimize(req: OptimizeRequest) -> dict:
    df, _source = _load(req)
    try:
        result = search_params(
            df,
            req.strategy,
            method=req.method,
            max_trials=req.max_trials,
            time_limit_ms=req.time_limit_ms,
            seed=req.seed,
            fee_bps=req.fee_bps,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    result.pop("best_backtest", None)
    return result


@app.post("/compare")
def compare(req: CompareRequest) -> dict:
    df, _source = load_bars(req.symbol, req.asset_class, bars=req.bars, seed=req.seed)
    try:
        out = compare_strategies(
            df,
            req.strategies,
            fee_bps=req.fee_bps,
            seed=req.seed,
            optimize=req.optimize,
            method=req.method,
            max_trials=req.max_trials,
            time_limit_ms=req.time_limit_ms,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"symbol": req.symbol, "asset_class": req.asset_class, **out}


@app.post("/pipeline")
def pipeline(req: PipelineRequest) -> dict:
    try:
        result = run_pipeline(
            asset_class=req.asset_class,
            symbol=req.symbol,
            strategies=req.strategies,
            fee_bps=req.fee_bps,
            bars=req.bars,
            seed=req.seed,
            method=req.method,
            max_trials=req.max_trials,
            time_limit_ms=req.time_limit_ms,
            include_walk_forward=req.include_walk_forward,
            include_report=req.include_report,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if SessionLocal is not None:
        session = SessionLocal()
        try:
            row = StrategyRun(
                asset_class=req.asset_class,
                symbol=req.symbol,
                optimized=True,
                payload={"ranking": result["comparison"]["ranking"], "source": result["source"]},
                report_markdown=result["report_markdown"],
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            result["persisted_run_id"] = row.id
        except Exception:
            session.rollback()
        finally:
            session.close()
    return result


@app.post("/report", response_class=HTMLResponse)
def report(req: CompareRequest) -> str:
    df, source = load_bars(req.symbol, req.asset_class, bars=req.bars, seed=req.seed)
    comparison = compare_strategies(
        df,
        req.strategies,
        fee_bps=req.fee_bps,
        seed=req.seed,
        optimize=req.optimize,
        method=req.method,
        max_trials=req.max_trials,
        time_limit_ms=req.time_limit_ms,
    )
    _md, html = render_report(req.symbol, req.asset_class, source, comparison, [])
    return html
