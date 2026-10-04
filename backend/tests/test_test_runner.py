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

    def test_vitest_uses_baked_junit_without_npm(self, tmp_path, monkeypatch):
        from app.services import test_runner as tr

        junit = tmp_path / "frontend-junit.xml"
        junit.write_text(
            """<?xml version="1.0"?>
<testsuite name="frontend" tests="1" failures="0" errors="0" skipped="0">
  <testcase classname="Page" name="test_ok" time="0.01"/>
</testsuite>
""",
            encoding="utf-8",
        )
        monkeypatch.setattr(tr, "RESULTS_DIR", tmp_path)
        monkeypatch.setattr(tr, "_frontend_root", lambda: None)
        monkeypatch.setattr(tr.shutil, "which", lambda _name: None)
        out = tr._run_vitest()
        assert out["passed"] == 1
        assert out["failed"] == 0
        assert "ビルド時" in (out.get("message") or "")
