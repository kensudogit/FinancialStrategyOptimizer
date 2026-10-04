from fastapi.testclient import TestClient

from app.main import app


class TestApi:
    def setup_method(self):
        self.client = TestClient(app)

    def test_health(self):
        res = self.client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_catalog(self):
        res = self.client.get("/catalog")
        body = res.json()
        assert "7203.T" in {item["symbol"] for item in body["assets"]["stock"]}
        assert body["strategies"]

    def test_backtest_sample(self):
        res = self.client.post(
            "/backtest",
            json={"symbol": "7203.T", "asset_class": "stock", "strategy": "buy_hold", "bars": 80},
        )
        assert res.status_code == 200
        assert res.json()["engine"] == "pandas"

    def test_unknown_symbol_400(self):
        res = self.client.post(
            "/backtest",
            json={"symbol": "NOPE.T", "asset_class": "stock", "strategy": "buy_hold"},
        )
        assert res.status_code == 400

    def test_tests_summary_endpoint(self):
        res = self.client.get("/tests/summary")
        assert res.status_code == 200
        assert "status" in res.json() or "totals" in res.json()

    def test_tests_report_endpoint(self):
        res = self.client.get("/tests/report")
        assert res.status_code == 200
        assert "test" in res.text.lower() or "No test report" in res.text
