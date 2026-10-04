from app.services.market_data import generate_ohlcv
from app.services.optimizer import search_params


def test_grid_is_seed_stable():
    df = generate_ohlcv("7203.T", "stock", bars=200, seed=1)
    a = search_params(df, "sma_crossover", method="grid", max_trials=12, time_limit_ms=5000, seed=7)
    b = search_params(df, "sma_crossover", method="grid", max_trials=12, time_limit_ms=5000, seed=7)
    assert a["best"]["params"] == b["best"]["params"]
    assert a["trials"] == b["trials"]


def test_does_not_claim_optimum_when_truncated():
    df = generate_ohlcv("USDJPY", "fx", bars=180, seed=3)
    out = search_params(df, "rsi_mean_reversion", method="random", max_trials=4, time_limit_ms=200, seed=1)
    assert out["exhausted"] is False
    assert "候補" in out["note"]
    assert out["best"]["proven_best_in_space"] is False
