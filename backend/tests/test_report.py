from app.services.report import render_report


class TestReport:
    def test_markdown_does_not_call_optimum(self):
        comparison = {
            "ranking": [
                {
                    "strategy": "sma_crossover",
                    "kpi": {
                        "objective": 1.0,
                        "sharpe": 0.5,
                        "total_return": 0.1,
                        "max_drawdown": -0.05,
                        "win_rate": 0.5,
                        "trades": 4,
                    },
                }
            ]
        }
        md, html = render_report(
            "7203.T",
            "stock",
            "sample:stockai-style",
            comparison,
            [{"strategy": "sma_crossover", "exhausted": False, "note": "候補"}],
        )
        assert "最適とは呼びません" in md
        assert "sample:" in md
        assert "7203.T" in html
