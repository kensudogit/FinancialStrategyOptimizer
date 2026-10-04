"""ローカル / CI から pytest と Vitest をまとめて走らせる。"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.test_runner import run_all  # noqa: E402

if __name__ == "__main__":
    summary = run_all()
    totals = summary.get("totals") or {}
    print(json_text := __import__("json").dumps(totals, ensure_ascii=False))
    raise SystemExit(0 if totals.get("ok") else 1)
