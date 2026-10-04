from app.services.pipeline import run_pipeline


def test_pipeline_stock_compare():
    out = run_pipeline(
        asset_class="stock",
        symbol="7203.T",
        strategies=["sma_crossover", "buy_hold"],
        max_trials=6,
        time_limit_ms=4000,
        include_walk_forward=False,
    )
    assert out["symbol"] == "7203.T"
    assert len(out["backtests"]) == 2
    assert len(out["comparison"]["ranking"]) == 2
    top = out["comparison"]["ranking"][0]
    chart = next(item for item in out["backtests"] if item["strategy"] == top["strategy"])
    assert chart["kpi"]["objective"] == top["kpi"]["objective"]
    assert chart["params"] == top["params"]
    assert "Sharpe" in out["report_markdown"] or "戦略" in out["report_markdown"]
