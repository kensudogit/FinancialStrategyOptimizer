from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AssetClass = Literal["stock", "fx"]
SearchMethod = Literal["grid", "random", "sa"]


class BacktestRequest(BaseModel):
    asset_class: AssetClass = "stock"
    symbol: str = "7203.T"
    strategy: str = "sma_crossover"
    params: dict[str, Any] = Field(default_factory=dict)
    fee_bps: float = Field(5, ge=0, le=100)
    bars: int = Field(260, ge=80, le=2000)
    seed: int = 1


class OptimizeRequest(BacktestRequest):
    method: SearchMethod = "grid"
    max_trials: int = Field(24, ge=4, le=200)
    time_limit_ms: int = Field(8000, ge=500, le=120000)


class CompareRequest(BaseModel):
    asset_class: AssetClass = "stock"
    symbol: str = "7203.T"
    strategies: list[str] = Field(default_factory=lambda: ["sma_crossover", "rsi_mean_reversion", "macd_cross"])
    fee_bps: float = 5
    bars: int = 260
    seed: int = 1
    method: SearchMethod = "grid"
    max_trials: int = 16
    time_limit_ms: int = 8000
    optimize: bool = True


class PipelineRequest(CompareRequest):
    include_walk_forward: bool = True
    include_report: bool = True


class KpiOut(BaseModel):
    total_return: float
    buy_hold_return: float
    sharpe: float
    max_drawdown: float
    win_rate: float
    trades: int
    calmar: float
    profit_factor: float
    alpha_vs_buy_hold: float
    objective: float


class RadarAxisOut(BaseModel):
    axis: str
    value: float


class BacktestOut(BaseModel):
    engine: str
    source: str
    strategy: str
    params: dict[str, Any]
    kpi: KpiOut
    equity_curve: list[dict[str, Any]]
    radar: list[RadarAxisOut]
    note: str = ""


class CandidateOut(BaseModel):
    params: dict[str, Any]
    kpi: KpiOut
    proven_best_in_space: bool = False


class OptimizeOut(BaseModel):
    strategy: str
    method: str
    trials: int
    exhausted: bool
    best: CandidateOut
    proposals: list[CandidateOut]
    note: str


class StrategyCompareOut(BaseModel):
    strategy: str
    params: dict[str, Any]
    kpi: KpiOut
    radar: list[RadarAxisOut]
    walk_forward: dict[str, Any] | None = None
    optimized: bool = False
    note: str = ""


class CompareOut(BaseModel):
    symbol: str
    asset_class: str
    ranking: list[StrategyCompareOut]
    radar_series: list[dict[str, Any]]


class PipelineOut(BaseModel):
    symbol: str
    asset_class: str
    bars: int
    source: str
    backtests: list[BacktestOut]
    optimizations: list[OptimizeOut]
    comparison: CompareOut
    report_markdown: str
    report_html: str
    persisted_run_id: int | None = None
