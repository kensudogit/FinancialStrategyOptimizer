"use client";

import { useEffect, useMemo, useState } from "react";
import { EquityChart } from "@/components/EquityChart";
import { GuideButton } from "@/components/GuideModal";
import { RadarChart } from "@/components/RadarChart";
import { api } from "@/lib/api";
import type { AssetClass, Catalog, PipelineOut } from "@/lib/types";

const DEFAULT_STRATEGIES = ["sma_crossover", "rsi_mean_reversion", "macd_cross"];

export default function Page() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [assetClass, setAssetClass] = useState<AssetClass>("stock");
  const [symbol, setSymbol] = useState("7203.T");
  const [strategies, setStrategies] = useState<string[]>(DEFAULT_STRATEGIES);
  const [seed, setSeed] = useState(1);
  const [maxTrials, setMaxTrials] = useState(48);
  const [bars, setBars] = useState(520);
  const [feeBps, setFeeBps] = useState(5);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<PipelineOut | null>(null);

  useEffect(() => {
    api
      .catalog()
      .then(setCatalog)
      .catch(() => setError("APIに接続できません"));
  }, []);

  const symbols = catalog?.assets[assetClass] ?? [];

  useEffect(() => {
    if (symbols[0] && !symbols.some((s) => s.symbol === symbol)) {
      setSymbol(symbols[0].symbol);
    }
  }, [assetClass, symbol, symbols]);

  const top = result?.comparison.ranking[0];
  const topBacktest = useMemo(
    () => result?.backtests.find((b) => b.strategy === top?.strategy) ?? result?.backtests[0],
    [result, top],
  );

  async function run() {
    setBusy(true);
    setError("");
    try {
      const out = await api.pipeline({
        asset_class: assetClass,
        symbol,
        strategies,
        seed,
        max_trials: maxTrials,
        bars,
        fee_bps: feeBps,
        method: "grid",
        time_limit_ms: 20000,
        include_walk_forward: true,
        include_report: true,
      });
      setResult(out);
    } catch (err) {
      setError(err instanceof Error ? err.message : "実行に失敗しました");
    } finally {
      setBusy(false);
    }
  }

  function toggle(id: string) {
    setStrategies((cur) => (cur.includes(id) ? cur.filter((x) => x !== id) : [...cur, id]));
  }

  function downloadReport() {
    if (!result) return;
    const blob = new Blob([result.report_markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fso-${result.symbol}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main>
      <header className="hero">
        <div>
          <p className="brand">FSO</p>
          <h1>分析・予測・売買・バックテストを一つの画面で。</h1>
          <p className="lead">
            バックテスト / KPI / パラメータ探索 / 複数戦略比較 / レーダー / レポート
          </p>
        </div>
        <div className="status">
          <a className="pill" href="/tests">
            テスト結果
          </a>
          <GuideButton />
          <span className="pill">
            <span className={error && !catalog ? "dotBad" : "dotOk"} />
            API {catalog ? "ok" : error ? "down" : "…"}
          </span>
          <span className="pill">mode: paper</span>
          <span className="pill">live: paper</span>
        </div>
      </header>

      <section className="toolbar">
        <label className="field">
          資産
          <select
            value={assetClass}
            onChange={(e) => setAssetClass(e.target.value as AssetClass)}
          >
            <option value="stock">株</option>
            <option value="fx">FX</option>
          </select>
        </label>
        <label className="field">
          銘柄
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {symbols.map((item) => (
              <option key={item.symbol} value={item.symbol}>
                {item.symbol} {item.name ? `— ${item.name}` : ""}
                {item.sector ? `（${item.sector}）` : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          seed
          <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value) || 1)} />
        </label>
        <label className="field">
          本数
          <input type="number" value={bars} onChange={(e) => setBars(Number(e.target.value) || 80)} />
        </label>
        <label className="field">
          試行数
          <input type="number" value={maxTrials} onChange={(e) => setMaxTrials(Number(e.target.value) || 8)} />
        </label>
        <label className="field">
          手数料bps
          <input type="number" value={feeBps} onChange={(e) => setFeeBps(Number(e.target.value) || 0)} />
        </label>
        <button type="button" className="primary" onClick={run} disabled={busy || strategies.length === 0}>
          {busy ? "実行中…" : "一気通貫"}
        </button>
      </section>
      <div className="strategy-list">
        {(catalog?.strategies ?? []).map((s) => (
          <label key={s.id} className="chip">
            <input type="checkbox" checked={strategies.includes(s.id)} onChange={() => toggle(s.id)} />
            {s.label}
            <span>{s.origin}</span>
          </label>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      {result && top && (
        <p className="note">
          {result.symbol} / {result.source} / {result.bars}本。先頭は目的関数順です。
          {top.optimized ? " パラメータ探索済み。" : ""} {top.note}
        </p>
      )}

      <section className="chart-grid">
        <article className="panel panel-half">
          <h3>資産曲線 — 戦略 / バイ＆ホールド</h3>
          {topBacktest ? (
            <EquityChart points={topBacktest.equity_curve} />
          ) : (
            <p className="empty">「一気通貫」でバックテスト曲線を表示</p>
          )}
        </article>
        <article className="panel panel-half">
          <h3>レーダー — 複数戦略比較</h3>
          {result ? (
            <RadarChart series={result.comparison.radar_series} />
          ) : (
            <p className="empty">実行後に戦略レーダーを表示</p>
          )}
        </article>
      </section>

      {result && top && (
        <section className="grid">
          <article className="panel panel-wide">
            <h2>結果 — {result.symbol}</h2>
            <div className="kpi-grid">
              <Kpi label="Sharpe" value={top.kpi.sharpe.toFixed(2)} />
              <Kpi label="リターン" value={`${(top.kpi.total_return * 100).toFixed(1)}%`} />
              <Kpi label="最大DD" value={`${(top.kpi.max_drawdown * 100).toFixed(1)}%`} />
              <Kpi label="勝率" value={`${(top.kpi.win_rate * 100).toFixed(1)}%`} />
              <Kpi label="売買" value={String(top.kpi.trades)} />
              <Kpi
                label="堅牢性"
                value={top.walk_forward?.summary?.robustness_label ?? "—"}
              />
            </div>
          </article>
          <article className="panel panel-wide">
            <h2>複数戦略比較</h2>
            <table>
              <thead>
                <tr>
                  <th>戦略</th>
                  <th>Sharpe</th>
                  <th>リターン</th>
                  <th>DD</th>
                  <th>勝率</th>
                  <th>目的関数</th>
                </tr>
              </thead>
              <tbody>
                {result.comparison.ranking.map((row) => (
                  <tr key={row.strategy}>
                    <td>{row.strategy}</td>
                    <td>{row.kpi.sharpe.toFixed(2)}</td>
                    <td>{(row.kpi.total_return * 100).toFixed(1)}%</td>
                    <td>{(row.kpi.max_drawdown * 100).toFixed(1)}%</td>
                    <td>{(row.kpi.win_rate * 100).toFixed(1)}%</td>
                    <td>{row.kpi.objective.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </article>
          <article className="panel panel-wide">
            <h2>レポート</h2>
            <button type="button" className="ghost" onClick={downloadReport}>
              Markdown を保存
            </button>
            <pre className="report">{result.report_markdown}</pre>
          </article>
        </section>
      )}

      {catalog && (
        <section className="grid">
          <article className="panel panel-wide">
            <h2>統合している既存資産</h2>
            <ul className="integrations">
              {catalog.integrations.map((item) => (
                <li key={item.id}>
                  <strong>{item.name}</strong>
                  <span>{item.available ? "検出" : "パス未検出（ローカル実装で代替）"}</span>
                  <em>{item.role}</em>
                </li>
              ))}
            </ul>
          </article>
        </section>
      )}
    </main>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="kpi">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
