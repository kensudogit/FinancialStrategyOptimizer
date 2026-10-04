# Claude Code / Cursor エージェント向け手順

このリポジトリは、株・FX 戦略の統合探索パッケージです。既存の StockPricePredictionTool と fx は捨てません。

## 守ること

- 証明していない解を「最適」と呼ばない。格子を走査し切ったときだけ探索空間内の最良と書く
- バックテストと探索は `backend/app/services/` に閉じ、FastAPI ルートへ埋め込まない
- ヒューリスティックは `seed` で再現する
- コミットと push は利用者から頼まれたときだけ行う
- UI を変えたら http://localhost:3020 で操作確認する

## 既存資産

- 株エンジン: `C:\devlop\StockPricePpredictionTool\backend\app\backtest\engine.py`
- FX ウォークフォワード: `C:\devlop\fx\backend\src\backtest\walk_forward.py`
- 探索作法: `C:\devlop\heuristic-optimizer\backend\app\services\optimizer.py`

## 起動

`start.cmd` または `.\start.ps1`（`COMPOSE_BAKE=false`）。ポートは 8020 / 3020 / 5434。
Railway はルートの `Dockerfile`（`railway.toml`）。Railpack 単体では判定できない。
