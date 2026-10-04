from app.services.backtest import public_backtest, run_backtest
from app.services.market_data import generate_ohlcv


class TestBacktest:
    def test_sma_backtest_has_kpi(self):
        df = generate_ohlcv("7203.T", "stock", bars=180, seed=1)
        out = run_backtest(df, "sma_crossover", {"fast": 8, "slow": 21}, fee_bps=5)
        assert out["engine"] == "pandas"
        assert "sharpe" in out["kpi"]
        assert len(out["equity_curve"]) > 3
        assert out["kpi"]["trades"] >= 0

    def test_public_strips_private(self):
        df = generate_ohlcv("7203.T", "stock", bars=80, seed=1)
        raw = run_backtest(df, "buy_hold", {}, fee_bps=5)
        pub = public_backtest(raw)
        assert "_returns" not in pub

    def test_unknown_strategy(self):
        df = generate_ohlcv("USDJPY", "fx", bars=120, seed=2)
        try:
            run_backtest(df, "unknown", {})
        except ValueError as exc:
            assert "未知" in str(exc)
        else:
            raise AssertionError("should fail")
