from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any


def render_report(symbol: str, asset_class: str, source: str, comparison: dict[str, Any], optimizations: list[dict[str, Any]]) -> tuple[str, str]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows = comparison["ranking"]
    lines = [
        f"# 金融戦略レポート — {symbol} ({asset_class})",
        "",
        f"作成: {now}",
        f"データ源: {source}",
        "",
        "## 順位",
        "",
        "| 順位 | 戦略 | 目的関数 | Sharpe | リターン | 最大DD | 勝率 | 売買 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for i, row in enumerate(rows, start=1):
        k = row["kpi"]
        lines.append(
            f"| {i} | {row['strategy']} | {k['objective']:.3f} | {k['sharpe']:.2f} | "
            f"{k['total_return']*100:.1f}% | {k['max_drawdown']*100:.1f}% | {k['win_rate']*100:.1f}% | {int(k['trades'])} |"
        )
    lines += ["", "## 探索メモ", ""]
    for opt in optimizations:
        mark = "格子内の最良" if opt.get("exhausted") else "未証明の候補"
        lines.append(f"- {opt['strategy']}: {mark} / {opt['note']}")
    lines += [
        "",
        "## 注意",
        "",
        "- 証明していない解を最適とは呼びません。",
        "- データ源が sample: で始まるときは決定的な疑似系列です。yahoo / stooq / stockai-http のときだけ市場系列です。",
        "- StockPricePredictionTool と fx の既存エンジンは捨てていません。本パッケージは統合層です。",
        "",
    ]
    markdown = "\n".join(lines)
    table = "".join(
        "<tr>"
        f"<td>{i}</td><td>{escape(row['strategy'])}</td>"
        f"<td>{row['kpi']['objective']:.3f}</td>"
        f"<td>{row['kpi']['sharpe']:.2f}</td>"
        f"<td>{row['kpi']['total_return']*100:.1f}%</td>"
        "</tr>"
        for i, row in enumerate(rows, start=1)
    )
    html = (
        f"<html><head><meta charset='utf-8'><title>戦略レポート {escape(symbol)}</title></head>"
        f"<body><h1>{escape(symbol)} 戦略レポート</h1><p>{escape(now)} / {escape(source)}</p>"
        f"<table border='1' cellpadding='6'><thead><tr><th>#</th><th>戦略</th><th>目的関数</th>"
        f"<th>Sharpe</th><th>リターン</th></tr></thead><tbody>{table}</tbody></table>"
        f"<pre>{escape(markdown)}</pre></body></html>"
    )
    return markdown, html
