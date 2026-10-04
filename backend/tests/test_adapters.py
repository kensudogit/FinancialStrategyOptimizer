from app.services.adapters import describe_assets, to_stooq_symbol, to_yahoo_symbol


class TestAdapters:
    def test_describe_assets_has_four(self):
        ids = {item["id"] for item in describe_assets()}
        assert {"stockai", "fx", "heuristic", "backtest"} <= ids

    def test_symbol_maps(self):
        assert to_stooq_symbol("8035.T", "stock") == "8035.jp"
        assert to_yahoo_symbol("EURJPY", "fx") == "EURJPY=X"
