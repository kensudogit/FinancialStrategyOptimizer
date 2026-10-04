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
  const [maxTrials, setMaxTrials] = useState(16);
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
        fee_bps: feeBps,
        method: "grid",
        time_limit_ms: 8000,
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
      <div className="app-bar">
        <span className="app-bar-accent" />
        <div className="app-bar-text">
          <p className="app-eyebrow">FINANCIAL STRATEGY</p>
          <h1>Financial Strategy Optimizer</h1>
          <p className="lead">
            株価・FX と売買戦略を入力し、バックテストから KPI、パラメータ探索、複数戦略比較、レーダー、レポートまで一気通貫します。
            StockPricePredictionTool と fx は残したまま、この層で束ねます。
          </p>
        </div>
        <GuideButton />
      </div>

      <section>
        <h2>入力</h2>
        <div className="controls">
          <label>
            資産
            <select
              value={assetClass}
              onChange={(e) => setAssetClass(e.target.value as AssetClass)}
            >
              <option value="stock">株</option>
              <option value="fx">FX</option>
            </select>
          </label>
          <label>
            銘柄
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {symbols.map((item) => (
                <option key={item.symbol} value={item.symbol}>
                  {item.symbol} {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            seed
            <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value) || 1)} />
          </label>
          <label>
            試行数
            <input type="number" value={maxTrials} onChange={(e) => setMaxTrials(Number(e.target.value) || 8)} />
          </label>
          <label>
            手数料bps
            <input type="number" value={feeBps} onChange={(e) => setFeeBps(Number(e.target.value) || 0)} />
          </label>
        </div>
        <div className="strategy-list">
          {(catalog?.strategies ?? []).map((s) => (
            <label key={s.id} className="chip">
              <input type="checkbox" checked={strategies.includes(s.id)} onChange={() => toggle(s.id)} />
              {s.label}
              <span>{s.origin}</span>
            </label>
          ))}
        </div>
        <button type="button" className="primary" onClick={run} disabled={busy || strategies.length === 0}>
          {busy ? "実行中…" : "一気通貫"}
        </button>
        {error && <p className="error">{error}</p>}
      </section>

      {catalog && (
        <section>
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
        </section>
      )}

      {result && top && (
        <>
          <section>
            <h2>結果 — {result.symbol}</h2>
            <p className="note">
              {result.source} / {result.bars}本。先頭は目的関数順です。
              {top.optimized ? " パラメータ探索済み。" : ""} {top.note}
            </p>
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
            {topBacktest && <EquityChart points={topBacktest.equity_curve} />}
          </section>

          <section>
            <h2>複数戦略比較</h2>
            <div className="compare-wrap">
              <RadarChart series={result.comparison.radar_series} />
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
            </div>
          </section>

          <section>
            <h2>レポート</h2>
            <button type="button" onClick={downloadReport}>
              Markdown を保存
            </button>
            <pre className="report">{result.report_markdown}</pre>
          </section>
        </>
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
