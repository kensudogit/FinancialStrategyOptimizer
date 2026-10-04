---
name: financial-strategy-optimizer
description: >
  株価・FX と売買戦略を入力し、バックテスト → KPI → パラメータ探索 → 最適化 →
  複数戦略比較 → レーダーチャート → レポートまで一気通貫する
  FinancialStrategyOptimizer を Python 3.12 + FastAPI + Next.js/React/TypeScript
  + PostgreSQL で実装するときに必ず使う。
  「戦略最適化」「一気通貫バックテスト」「複数戦略比較」「レーダーチャート」
  「ウォークフォワード」「需要ではなく売買戦略の探索」
  「C:\devlop\FinancialStrategyOptimizer」の改修が出たら参照する。
  着信コンタクトセンター、汎用会計、実ブローカー発注、工場レイアウト単体には使わない。
---

# Financial Strategy Optimizer

`C:\devlop\FinancialStrategyOptimizer` の実装規約。コードを書く・直す・解説する前に読む。

既存資産は捨てない。

```
StockPricePredictionTool ─┐
                          ├→ FinancialStrategyOptimizer
fx ───────────────────────┤
                          │
Heuristic Optimizer ──────┤
                          │
Backtest Engine ──────────┘
```

## 先に決まっていること

1. **証明していない解を「最適」と呼ばない。** 格子を走査し切ったときだけ「探索空間内の最良」。打ち切りは候補。
2. **探索・バックテストは `backend/app/services/` に閉じる。** FastAPI ルートへ埋め込まない。
3. **ヒューリスティックは `seed` で再現する。** `max_trials` と `time_limit_ms` で打ち切る。
4. **StockAI と fx を置き換えない。** アダプタとローカル実装で束ねる。株は SMA/KPI、FX は RSI/MACD と IS/OOS。
5. **UI を変えたら http://localhost:3020 で操作確認する。** コミットと push は頼まれたときだけ。

## スタックと起動

- Backend: Python 3.12 / FastAPI / pandas / Pydantic / SQLAlchemy
- Frontend: Next.js 15 / React 19 / TypeScript（ECharts は使わず SVG）
- DB: PostgreSQL 16（ホスト **5434**）。無いときは永続化だけスキップ
- ローカル: API **8020**、画面 **3020**（8000/3000 と 8010/3010 は空けておく）
- 本番: ルート `Dockerfile` + `railway.toml`。Railpack 単体では判定できない

```bat
cd /d C:\devlop\FinancialStrategyOptimizer
start.cmd
```

PowerShell は `.\start.ps1`（`COMPOSE_BAKE=false`）。

- UI: http://localhost:3020
- API: http://localhost:8020/docs

## 実行手順

1. 依頼をリポジトリの `docs/作業内容.md` の行に対応付ける。
2. 入力を決める。`asset_class`（stock/fx）、`symbol`、戦略 ID、`fee_bps`、`seed`。
3. 市場データは `services/market_data.py`。未知銘柄は 400。実データ差し替えはアダプタ経由。
4. 戦略は `services/strategies.py` のレジストリに足す。信号は `close` と `params` だけ。
5. 評価は `services/backtest.py` → `services/kpi.py`。KPI スキーマを戦略ごとに変えない。
6. 探索は `services/optimizer.py`。grid / random / sa。`exhausted` と `note` を偽らない。
7. 堅牢性は `services/walk_forward.py`（fx と同じ IS/OOS）。
8. 比較とレーダーは `services/compare.py`。軸は Sharpe / リターン / 耐DD / 勝率 / 堅牢性 / 売買回数。
9. レポートは `services/report.py`。一気通貫は `POST /pipeline`。
10. pytest（`backend/tests/`）を通す。UI 変更は 3020 で「一気通貫」まで確認する。

## サービスと API

| モジュール | 役割 |
|---|---|
| `adapters.py` | StockAI / fx / heuristic のパス検出。本体は捨てない |
| `market_data.py` | 決定的サンプル OHLCV。seed で再現 |
| `strategies.py` | sma_crossover, rsi_mean_reversion, macd_cross, donchian_breakout, buy_hold |
| `backtest.py` | pandas 単一エンジン |
| `optimizer.py` | パラメータ探索 |
| `compare.py` / `pipeline.py` / `report.py` | 比較・一気通貫・Markdown/HTML |

- `GET /health` `/catalog` `/sample` `/tests/summary` `/tests/report`
- `POST /backtest` `/optimize` `/compare` `/pipeline` `/report` `/tests/run`

## 実装原則

- 目的関数は `kpi["objective"]`（Sharpe − DD ペナルティ + リターン）。ルートで再計算しない。
- TypeScript は `frontend/lib/types.ts` と API を揃える。`any` を増やさない。
- 画面の「利用手順」と README / 本 Skill の起動・ポート・最適の言い方を一致させる。
- サンプル系列を実市場確定値と書かない。

## 完了条件

- `backend` で pytest が通る
- Docker なら 3020 から `/api/pipeline` が呼べる
- 未証明の解を最適と呼んでいない
- README だけで第三者が起動できる（ローカルは 8020/3020、Railway はルート Dockerfile）
