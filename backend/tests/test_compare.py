from app.services.compare import compare_strategies
from app.services.market_data import generate_ohlcv
from app.services.optimizer import search_params


class TestCompare:
    def test_ranking_sorted_by_objective(self):
        df = generate_ohlcv("7203.T", "stock", bars=120, seed=1)
        out = compare_strategies(
            df,
            ["sma_crossover", "buy_hold"],
            optimize=False,
            include_walk_forward=False,
        )
        objs = [row["kpi"]["objective"] for row in out["ranking"]]
        assert objs == sorted(objs, reverse=True)

    def test_reuses_precomputed_search(self):
        df = generate_ohlcv("7203.T", "stock", bars=120, seed=1)
        opt = search_params(df, "buy_hold", method="grid", max_trials=4, time_limit_ms=1000)
        out = compare_strategies(
            df,
            ["buy_hold"],
            optimize=True,
            include_walk_forward=False,
            precomputed={"buy_hold": opt},
        )
        assert out["ranking"][0]["params"] == opt["best"]["params"]
        assert out["ranking"][0]["optimized"] is True
