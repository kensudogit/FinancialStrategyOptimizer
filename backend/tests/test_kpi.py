import pandas as pd

from app.services.kpi import clip01, compute_kpi, radar_from_kpi


class TestKpi:
    def test_compute_kpi_keys(self):
        rets = pd.Series([0.01, -0.005, 0.002, 0.0])
        kpi = compute_kpi(rets, rets, trades=2)
        assert {"sharpe", "objective", "max_drawdown", "total_return"} <= set(kpi)

    def test_clip01_bounds(self):
        assert clip01(5, 0, 10) == 50
        assert clip01(0, 0, 0) == 0

    def test_radar_axes(self):
        kpi = compute_kpi(pd.Series([0.01, 0.01]), pd.Series([0.01, 0.0]), trades=4)
        axes = [item["axis"] for item in radar_from_kpi(kpi, robustness=0.8)]
        assert axes == ["Sharpe", "リターン", "耐DD", "勝率", "堅牢性", "売買回数"]
