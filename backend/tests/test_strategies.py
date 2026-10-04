from app.services.market_data import generate_ohlcv
from app.services.strategies import catalog, signal_for, sma_crossover


class TestStrategies:
    def test_catalog_has_five_ids(self):
        ids = {item["id"] for item in catalog()}
        assert ids == {
            "sma_crossover",
            "rsi_mean_reversion",
            "macd_cross",
            "donchian_breakout",
            "buy_hold",
        }

    def test_sma_signal_length_matches_close(self):
        close = generate_ohlcv("7203.T", "stock", bars=80, seed=1)["close"]
        sig = sma_crossover(close, {"fast": 5, "slow": 20})
        assert len(sig) == len(close)
        assert set(sig.unique()).issubset({-1.0, 0.0, 1.0})

    def test_buy_hold_is_always_long(self):
        close = generate_ohlcv("USDJPY", "fx", bars=60, seed=2)["close"]
        sig = signal_for("buy_hold", close, {})
        assert (sig == 1.0).all()

    def test_unknown_signal(self):
        close = generate_ohlcv("7203.T", "stock", bars=40, seed=1)["close"]
        try:
            signal_for("nope", close, {})
        except ValueError as exc:
            assert "未知" in str(exc)
        else:
            raise AssertionError("should fail")
