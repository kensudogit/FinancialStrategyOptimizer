# Financial Strategy Optimizer

株価・FX データと売買戦略を入力し、

**バックテスト → KPI → パラメータ探索 → 最適化 → 複数戦略比較 → レーダーチャート → レポート**

まで一気通貫する統合パッケージです。

既存資産は捨てません。

```
StockPricePredictionTool ─┐
                          ├→ FinancialStrategyOptimizer
fx ───────────────────────┤
                          │
Heuristic Optimizer ──────┤
                          │
Backtest Engine ──────────┘
```

| 既存 | このパッケージでの役割 |
|---|---|
| `C:\devlop\StockPricePpredictionTool` | 株 OHLCV、SMAクロス、Sharpe/DD KPI |
| `C:\devlop\fx` | FX OHLCV、RSI/MACD、ウォークフォワード堅牢性 |
| `C:\devlop\heuristic-optimizer` | seed・制限時間・複数提案・未証明を最適と呼ばない作法 |
| Backtest Engine | pandas 単一エンジンに KPI を揃える（`backend/app/services/backtest.py`） |

作業対応は [`docs/作業内容.md`](docs/作業内容.md) です。
エージェント規約は [`skill/financial-strategy-optimizer/SKILL.md`](skill/financial-strategy-optimizer/SKILL.md) です。

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
