"""pytest / vitest を実行し、WEB 用の summary.json を書く。探索ロジックは含めない。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent if (BACKEND_ROOT.parent / "frontend").is_dir() else BACKEND_ROOT
RESULTS_DIR = Path(os.getenv("FSO_TEST_RESULTS", str(BACKEND_ROOT / "test-results")))


def _summary_path() -> Path:
    return RESULTS_DIR / "summary.json"


def load_summary() -> dict[str, Any]:
    path = _summary_path()
    if not path.exists():
        return {
            "status": "missing",
            "message": "まだテスト結果がありません。「全テスト実行」を押してください。",
            "results_dir": str(RESULTS_DIR),
        }
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_junit(path: Path, suite_name: str) -> dict[str, Any]:
    if not path.exists():
        return {
            "suite": suite_name,
            "exit_code": 1,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "suites": [],
            "message": f"{path.name} がありません",
        }
    root = ET.parse(path).getroot()
    suites_el = root.findall("testsuite") if root.tag == "testsuites" else [root]
    total = failed = skipped = errors = 0
    suites: list[dict[str, Any]] = []
    for ts in suites_el:
        total += int(ts.attrib.get("tests", 0))
        failed += int(ts.attrib.get("failures", 0))
        errors += int(ts.attrib.get("errors", 0))
        skipped += int(ts.attrib.get("skipped", 0))
        cases = []
        for tc in ts.findall("testcase"):
            status = "passed"
            msg = ""
            if tc.find("failure") is not None:
                status = "failed"
                msg = (tc.find("failure").attrib.get("message") or "")[:500]
            elif tc.find("error") is not None:
                status = "error"
                msg = (tc.find("error").attrib.get("message") or "")[:500]
            elif tc.find("skipped") is not None:
                status = "skipped"
            cases.append(
                {
                    "class": tc.attrib.get("classname", ""),
                    "name": tc.attrib.get("name", ""),
                    "time": float(tc.attrib.get("time", 0) or 0),
                    "status": status,
                    "message": msg,
                }
            )
        suites.append({"name": ts.attrib.get("name", suite_name), "cases": cases})
    failed_all = failed + errors
    return {
        "suite": suite_name,
        "exit_code": 0 if failed_all == 0 else 1,
        "total": total,
        "passed": max(total - failed_all - skipped, 0),
        "failed": failed_all,
        "skipped": skipped,
        "suites": suites,
    }


def _empty(suite: str, message: str, exit_code: int = 0) -> dict[str, Any]:
    return {
        "suite": suite,
        "exit_code": exit_code,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "suites": [],
        "message": message,
    }


def _existing_junit(*candidates: Path | None) -> Path | None:
    for path in candidates:
        if path and path.exists() and path.is_file():
            return path
    return None


def _run_pytest() -> dict[str, Any]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    junit = RESULTS_DIR / "backend-junit.xml"
    tests_dir = BACKEND_ROOT / "tests"
    if not tests_dir.is_dir():
        baked = _existing_junit(junit)
        if baked:
            out = _parse_junit(baked, "backend")
            out["message"] = "ビルド時の pytest JUnit です"
            return out
        return _empty("backend", "backend/tests がイメージにありません")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_ROOT)
    env["FSO_FORCE_SAMPLE"] = "1"
    code = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", f"--junitxml={junit}", "-q"],
        cwd=str(BACKEND_ROOT),
        env=env,
        check=False,
    ).returncode
    out = _parse_junit(junit, "backend")
    out["exit_code"] = code
    out["html_report"] = None
    if out["total"] == 0 and code != 0:
        out["message"] = "pytest が JUnit を書けませんでした"
    return out


def _frontend_root() -> Path | None:
    env = os.getenv("FRONTEND_ROOT", "").strip()
    candidates = [
        Path(env) if env else None,
        REPO_ROOT / "frontend",
        BACKEND_ROOT.parent / "frontend",
    ]
    for path in candidates:
        if path and (path / "package.json").exists():
            return path
    return None


def _vitest_available(root: Path) -> bool:
    return (root / "node_modules" / "vitest").exists() or (root / "node_modules" / ".bin" / "vitest").exists()


def _run_vitest() -> dict[str, Any]:
    root = _frontend_root()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    junit = RESULTS_DIR / "frontend-junit.xml"
    ran = False
    code = 0
    if root is not None and shutil.which("npm") and _vitest_available(root):
        code = subprocess.run(
            [shutil.which("npm"), "test", "--", "--run", "--reporter=junit", f"--outputFile={junit}"],
            cwd=str(root),
            check=False,
        ).returncode
        ran = True
    baked = _existing_junit(
        junit,
        (root / "public" / "test-results" / "frontend-junit.xml") if root else None,
        (root / "test-results" / "frontend-junit.xml") if root else None,
        Path("/app/frontend/public/test-results/frontend-junit.xml"),
    )
    if baked is None:
        if root is None:
            return _empty("frontend", "frontend ディレクトリが見つかりません")
        if ran:
            return _empty("frontend", "Vitest JUnit が書けませんでした", exit_code=code)
        return _empty("frontend", "本番イメージに Vitest が無いため、ビルド時 JUnit を使います")
    out = _parse_junit(baked, "frontend")
    if ran:
        out["exit_code"] = code
    else:
        out["message"] = "ビルド時の Vitest JUnit です"
    return out


def run_all() -> dict[str, Any]:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    backend = _run_pytest()
    frontend = _run_vitest()
    total = int(backend.get("total", 0)) + int(frontend.get("total", 0))
    passed = int(backend.get("passed", 0)) + int(frontend.get("passed", 0))
    failed = int(backend.get("failed", 0)) + int(frontend.get("failed", 0))
    skipped = int(backend.get("skipped", 0)) + int(frontend.get("skipped", 0))
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "ok" if failed == 0 and total > 0 else ("failed" if failed else "missing"),
        "backend": backend,
        "frontend": frontend,
        "totals": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "ok": failed == 0 and total > 0,
        },
    }
    _summary_path().write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS_DIR / "index.html").write_text(_html(summary), encoding="utf-8")
    return summary


def _html(summary: dict[str, Any]) -> str:
    totals = summary.get("totals") or {}
    return (
        "<html><head><meta charset='utf-8'><title>FSO テスト結果</title></head>"
        f"<body><h1>FSO テスト結果</h1><p>{summary.get('generated_at')}</p>"
        f"<p>total={totals.get('total')} passed={totals.get('passed')} "
        f"failed={totals.get('failed')} ok={totals.get('ok')}</p>"
        f"<pre>{json.dumps(summary, ensure_ascii=False, indent=2)}</pre></body></html>"
    )
