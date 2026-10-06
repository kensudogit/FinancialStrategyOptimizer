# Financial Strategy Optimizer

> **FinTech / Quant Strategy Optimization Platform** — 株式・FX・バックテスト・ヒューリスティック探索を統合し、再現可能な戦略評価とパラメータ最適化を行うフルスタック基盤です。
>
> **Stack:** Python 3.12 · FastAPI · Next.js 15 · React 19 · TypeScript · PostgreSQL 16 · Docker · Railway

## Portfolio Overview

| Item | Description |
|---|---|
| **Problem** | 株式・FX・バックテスト・最適化が個別ツールに分散すると、KPI・探索条件・再現性が揃わず、戦略比較が難しい |
| **Solution** | データと戦略を共通パイプラインへ投入し、Backtest → KPI → Search → Optimization → Comparison → Report を一気通貫で実行 |
| **Architecture** | Next.js UI → FastAPI → Strategy / Backtest / Optimization Services → PostgreSQL → Report |
| **Differentiators** | 株式とFXの横断、共通KPI、複数戦略比較、seedによる再現性、「未証明の解を最適と呼ばない」探索設計 |
| **Role** | FinTechポートフォリオにおける **Quant Strategy Integration Layer** |

## Architecture

```text
Stock / FX Data
      │
      ▼
 Strategy Definitions
      │
      ▼
┌───────────────────────────────┐
│ FinancialStrategyOptimizer    │
│                               │
│ Backtest Engine               │
│ KPI / Risk Metrics            │
│ Parameter Search              │
│ Heuristic Optimization        │
│ Strategy Comparison           │
│ Report Generation             │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
   PostgreSQL       Next.js UI
                         │
                         ▼
              Radar / KPI / Report
```

## FinTech Portfolio Map

This repository is the integration and optimization layer of the broader FinTech/Quant portfolio.

| Repository | Primary role | Relationship |
|---|---|---|
| [Fintech](../Fintech) | Enterprise Financial AI | Valuation, lending, B2B matching, financial RAG and evidence-led decision support |
| [fx](../fx) | FX / Quant | FX market analysis, indicators, ML, risk management and backtesting |
| [StockPricePpredictionTool-](../StockPricePpredictionTool-) | Equity AI Agent | Equity analysis, prediction, walk-forward evidence, risk gates and trading workflow |
| [heuristic-optimizer](../heuristic-optimizer) | Optimization Engine | Reproducible heuristic search and constrained solution exploration |
| **FinancialStrategyOptimizer** | **Quant Strategy Integration** | Unifies backtesting, KPI, parameter search, optimization, comparison and reporting |

## Engineering Differentiators

- **Common evaluation pipeline** — strategies are compared through the same backtest and KPI model instead of unrelated tool-specific metrics.
- **Reproducible optimization** — stochastic exploration uses explicit seeds and bounded search conditions.
- **Evidence-aware terminology** — an unproven candidate is not presented as a mathematically proven optimum.
- **Cross-asset design** — equity and FX strategy inputs can be evaluated through the same integration layer.
- **Separation of concerns** — optimization and backtesting live in backend services rather than API route handlers.
- **Operational portability** — Docker/Railway deployment plus PostgreSQL-optional local execution.
- **Test visibility** — backend/frontend test results can be inspected from the application UI.

## Optimization Pipeline

```text
Market Data
   ↓
Strategy + Parameter Space
   ↓
Backtest
   ↓
KPI / Risk Evaluation
   ↓
Parameter Search / Heuristic Search
   ↓
Candidate Strategies
   ↓
Comparison + Radar Visualization
   ↓
HTML Report
```

## 技術構成

Python 3.12 + FastAPI、Next.js 15 / React 19 / TypeScript、PostgreSQL 16。
探索・バックテスト本体は `backend/app/services/` に閉じ、ルートには埋めません。

## 起動（Docker）

8000/3000 と 8010/3010 は既存システム用です。既定は API **8020**、画面 **3020**、Postgres **5434**。

```bat
cd /d C:\devlop\FinancialStrategyOptimize
start.cmd
```

PowerShell なら `.\start.ps1` です（`COMPOSE_BAKE=false`）。

- アプリ: http://localhost:3020
- API: http://localhost:8020/docs

停止は `docker compose down` です。

## Railway

リポジトリ直下は backend と frontend が並んでいるため、Railpack は言語を判定できません。
ルートの `railway.toml` と `Dockerfile` で、API と画面を1サービスにまとめています。

1. GitHub リポジトリから Deploy する
2. ビルダは Dockerfile（`railway.toml` で指定済み）
3. 公開 URL が画面。API は同じオリジンの `/api`
4. Postgres を付ける場合は `DATABASE_URL` をサービスに接続する。無くても探索は動く
5. `/tests` はイメージビルド時に pytest と Vitest を走らせ、結果を焼き込む。本番に npm / Vitest は載せない

## 起動（ローカル）

```powershell
cd C:\devlop\FinancialStrategyOptimize\backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL="sqlite+pysqlite:///./fso.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8020
```

Postgres なしでも API は動きます（結果の永続化だけスキップします）。

```powershell
cd C:\devlop\FinancialStrategyOptimize\frontend
npm install
$env:API_INTERNAL_URL="http://localhost:8020"
npm run dev -- --port 3020
```

## API

- `GET /health` / `GET /catalog` / `GET /sample`
- `GET /tests/summary` / `GET /tests/report` / `POST /tests/run` — pytest / Vitest 結果
- `POST /backtest` — 単一戦略
- `POST /optimize` — パラメータ探索。格子を走査し切ったときだけ「探索空間内の最良」
- `POST /compare` — 複数戦略 + レーダー
- `POST /pipeline` — 一気通貫
- `POST /report` — HTML レポート

## テスト

```powershell
cd C:\devlop\FinancialStrategyOptimizer\backend
.\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm test
```

画面の「テスト結果」（http://localhost:3020/tests）から全テスト実行とケース一覧を確認できます。

## 制約

- 証明していない解を最適と呼ばない
- サンプル OHLCV は決定的な疑似系列。実データは既存 StockAI / fx から差し替える
- 乱数を使う探索は `seed` で再現する