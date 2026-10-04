from pydantic import ValidationError

from app.models import BacktestRequest, OptimizeRequest


class TestModels:
    def test_backtest_defaults(self):
        req = BacktestRequest()
        assert req.symbol == "7203.T"
        assert req.bars == 520

    def test_optimize_rejects_tiny_trials(self):
        try:
            OptimizeRequest(max_trials=1)
        except ValidationError:
            return
        raise AssertionError("should reject max_trials=1")
