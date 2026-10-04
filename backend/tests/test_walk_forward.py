from app.services.market_data import generate_ohlcv
from app.services.walk_forward import run_walk_forward


class TestWalkForward:
    def test_too_short(self):
        df = generate_ohlcv("7203.T", "stock", bars=40, seed=1)
        out = run_walk_forward(df, "buy_hold", {}, fee_bps=5)
        assert out["status"] == "error"

    def test_success_has_label(self):
        df = generate_ohlcv("7203.T", "stock", bars=200, seed=1)
        out = run_walk_forward(df, "buy_hold", {}, fee_bps=5, train_bars=80, test_bars=30, step_bars=30)
        assert out["status"] == "success"
        assert "robustness_label" in out["summary"]
