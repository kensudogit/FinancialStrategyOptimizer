"use client";

import { useCallback, useEffect, useState } from "react";

type Case = {
  class: string;
  name: string;
  time: number;
  status: string;
  message?: string;
};

type SideSummary = {
  suite?: string;
  exit_code?: number;
  total?: number;
  passed?: number;
  failed?: number;
  skipped?: number;
  suites?: { name: string; cases: Case[] }[];
  message?: string;
};

type Summary = {
  status?: string;
  message?: string;
  generated_at?: string;
  backend?: SideSummary;
  frontend?: SideSummary;
  totals?: { total: number; passed: number; failed: number; skipped: number; ok: boolean };
};

function parseJunitXml(xml: string): SideSummary {
  const doc = new DOMParser().parseFromString(xml, "text/xml");
  const suitesEl = Array.from(doc.getElementsByTagName("testsuite"));
  const suites: { name: string; cases: Case[] }[] = [];
  let total = 0;
  let failed = 0;
  let skipped = 0;
  for (const ts of suitesEl) {
    total += Number(ts.getAttribute("tests") || 0);
    failed += Number(ts.getAttribute("failures") || 0) + Number(ts.getAttribute("errors") || 0);
    skipped += Number(ts.getAttribute("skipped") || 0);
    const cases: Case[] = [];
    for (const tc of Array.from(ts.getElementsByTagName("testcase"))) {
      let status = "passed";
      if (tc.getElementsByTagName("failure").length) status = "failed";
      else if (tc.getElementsByTagName("error").length) status = "error";
      else if (tc.getElementsByTagName("skipped").length) status = "skipped";
      cases.push({
        class: tc.getAttribute("classname") || "",
        name: tc.getAttribute("name") || "",
        time: Number(tc.getAttribute("time") || 0),
        status,
      });
    }
    suites.push({ name: ts.getAttribute("name") || "frontend", cases });
  }
  return {
    suite: "frontend",
    total,
    passed: Math.max(total - failed - skipped, 0),
    failed,
    skipped,
    suites,
    message: "ビルド時の Vitest JUnit です",
  };
}

function withTotals(summary: Summary): Summary {
  const backend = summary.backend ?? {};
  const frontend = summary.frontend ?? {};
  const total = (backend.total ?? 0) + (frontend.total ?? 0);
  const passed = (backend.passed ?? 0) + (frontend.passed ?? 0);
  const failed = (backend.failed ?? 0) + (frontend.failed ?? 0);
  const skipped = (backend.skipped ?? 0) + (frontend.skipped ?? 0);
  return {
    ...summary,
    totals: { total, passed, failed, skipped, ok: failed === 0 && total > 0 },
  };
}

export default function TestsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const res = await fetch("/api/tests/summary", { cache: "no-store" });
      const data = (await res.json()) as Summary;
      if (!(data.frontend?.total)) {
        const fx = await fetch("/test-results/frontend-junit.xml", { cache: "no-store" });
        if (fx.ok) {
          data.frontend = parseJunitXml(await fx.text());
        }
      }
      setSummary(data.totals ? data : withTotals(data));
    } catch (err) {
      setError(err instanceof Error ? err.message : "読込に失敗しました");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function runTests() {
    setBusy(true);
    setError("");
    try {
      const res = await fetch("/api/tests/run", { method: "POST" });
      const data = (await res.json()) as { summary?: Summary; detail?: string };
      if (!res.ok) {
        setError(typeof data.detail === "string" ? data.detail : "実行に失敗しました");
        return;
      }
      if (data.summary) {
        const next = data.summary;
        if (!(next.frontend?.total)) {
          const fx = await fetch("/test-results/frontend-junit.xml", { cache: "no-store" });
          if (fx.ok) {
            next.frontend = parseJunitXml(await fx.text());
            setSummary(withTotals(next));
            return;
          }
        }
        setSummary(next.totals ? next : withTotals(next));
      } else await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "実行に失敗しました");
    } finally {
      setBusy(false);
    }
  }

  const totals = summary?.totals;
  const rows: { side: string; c: Case }[] = [];
  for (const side of ["backend", "frontend"] as const) {
    for (const suite of summary?.[side]?.suites ?? []) {
      for (const c of suite.cases ?? []) {
        rows.push({ side, c });
      }
    }
  }

  return (
    <main>
      <header className="hero">
        <div>
          <p className="brand">FSO</p>
          <h1>テスト結果</h1>
          <p className="lead">Python (pytest) / TypeScript (Vitest) のクラスとケースを確認できます。</p>
        </div>
        <div className="status">
          <a className="pill" href="/">
            ← ダッシュボード
          </a>
          <a className="pill" href="/api/tests/report" target="_blank" rel="noreferrer">
            HTMLレポート
          </a>
        </div>
      </header>

      <section className="toolbar">
        <button type="button" className="ghost" disabled={busy} onClick={() => void load()}>
          再読込
        </button>
        <button type="button" className="primary" disabled={busy} onClick={() => void runTests()}>
          {busy ? "実行中…" : "全テスト実行"}
        </button>
      </section>
      {error && <p className="error">{error}</p>}
      {summary?.status === "missing" && <p className="note">{summary.message}</p>}

      {totals && (
        <section className="grid">
          <article className="panel panel-third">
            <h2>合計</h2>
            <ul className="integrations">
              <li>
                <strong>Overall</strong>
                <span className={totals.ok ? "status-pass" : "status-fail"}>{totals.ok ? "PASS" : "FAIL"}</span>
                <em>{summary?.generated_at}</em>
              </li>
              <li>
                <strong>passed / failed</strong>
                <span>
                  {totals.passed} / {totals.failed}
                </span>
                <em>total {totals.total}</em>
              </li>
            </ul>
          </article>
          <article className="panel panel-third">
            <h2>Backend (pytest)</h2>
            <p className="note">
              {summary?.backend?.passed ?? 0} passed / {summary?.backend?.failed ?? 0} failed
            </p>
            {summary?.backend?.message && <p className="note">{summary.backend.message}</p>}
          </article>
          <article className="panel panel-third">
            <h2>Frontend (Vitest)</h2>
            <p className="note">
              {summary?.frontend?.passed ?? 0} passed / {summary?.frontend?.failed ?? 0} failed
            </p>
            {summary?.frontend?.message && <p className="note">{summary.frontend.message}</p>}
          </article>
        </section>
      )}

      {rows.length > 0 && (
        <section className="panel">
          <h2>ケース</h2>
          <table>
            <thead>
              <tr>
                <th>側</th>
                <th>クラス</th>
                <th>ケース</th>
                <th>結果</th>
                <th>秒</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={`${row.side}-${row.c.class}-${row.c.name}`}>
                  <td>{row.side}</td>
                  <td>{row.c.class}</td>
                  <td>{row.c.name}</td>
                  <td className={row.c.status === "passed" ? "status-pass" : row.c.status === "failed" || row.c.status === "error" ? "status-fail" : ""}>
                    {row.c.status}
                  </td>
                  <td>{row.c.time.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}
