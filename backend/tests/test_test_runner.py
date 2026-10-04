from pathlib import Path

from app.services.test_runner import _parse_junit, load_summary


class TestTestRunner:
    def test_load_summary_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.test_runner.RESULTS_DIR", tmp_path)
        out = load_summary()
        assert out["status"] == "missing"

    def test_parse_junit(self, tmp_path):
        xml = tmp_path / "x.xml"
        xml.write_text(
            """<?xml version="1.0"?>
<testsuite name="backend" tests="2" failures="1" errors="0" skipped="0">
  <testcase classname="tests.test_kpi.TestKpi" name="test_clip01_bounds" time="0.01"/>
  <testcase classname="tests.test_kpi.TestKpi" name="test_fail" time="0.02">
    <failure message="boom"/>
  </testcase>
</testsuite>
""",
            encoding="utf-8",
        )
        out = _parse_junit(xml, "backend")
        assert out["total"] == 2
        assert out["failed"] == 1
        assert out["passed"] == 1
        assert out["suites"][0]["cases"][0]["class"] == "tests.test_kpi.TestKpi"
