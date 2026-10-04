"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface Step {
  no: string;
  title: string;
  body: string;
  note?: string;
}

const TAGS = [
  "Python 3.12",
  "FastAPI",
  "Next.js 15",
  "React 19",
  "TypeScript",
  "PostgreSQL",
  "Docker",
  "Railway",
];

const BASIC_STEPS: Step[] = [
  {
    no: "01",
    title: "アプリを起動する",
    body: "リポジトリ直下で start.cmd（コマンドプロンプト）または .\\start.ps1（PowerShell）を実行します。中身は COMPOSE_BAKE=false 付きの docker compose up --build -d です。画面は http://localhost:3020、API は http://localhost:8020/docs、Postgres はホスト 5434 です。8000/3000 は StockAI、8010/3010 は heuristic-optimizer 用に空けてあります。",
    note: "Docker Desktop が起動していることを確認してください。停止は docker compose down です。画面からの API は /api 経由なので、ブラウザは 3020 だけ開けば動きます。コマンドプロンプトから .ps1 を直接叩いても動きません。Railway へ出すときはルートの railway.toml と Dockerfile を使います。Railpack 単体では backend / frontend を判定できません。",
  },
  {
    no: "02",
    title: "資産クラスと銘柄を選ぶ",
    body: "上段の「資産」で株または FX を選び、「銘柄」を切り替えます。株は StockPricePredictionTool 側の銘柄（7203.T トヨタ、6758.T ソニー、9984.T ソフトバンクグループ）、FX は fx 側の通貨ペア（USDJPY など）です。候補は起動時の GET /catalog から入ります。この画面が統合入口で、既存パッケージは捨てません。",
    note: "未知の銘柄を API に直接送ると 400 です。取れるときは Yahoo 日足、StockAI HTTP、Stooq の順で入れます。取れないときだけ決定的サンプルです。データ源が sample: で始まる行は実市場の確定値ではありません。",
  },
  {
    no: "03",
    title: "戦略を複数選ぶ",
    body: "チップのチェックで比較対象を選びます。既定は SMAクロス・RSI逆張り・MACDクロスです。SMAクロスは StockAI（fast/slow）、RSI逆張りと MACDクロスは fx、ドンチャン・ブレイクは統合バックテストエンジン、バイ＆ホールドは比較用の基準線です。少なくとも 1 つ必要です。",
    note: "信号は終値とパラメータだけです。戦略を足すときは backend/app/services/strategies.py のレジストリに追加します。KPI スキーマは戦略ごとに変えません。",
  },
  {
    no: "04",
    title: "seed・試行数・手数料を決める",
    body: "seed を固定すると同じ乱数系列で探索を再現できます。本数の既定は 520（約2年）。試行数はパラメータ探索の上限（既定 48）。手数料 bps は往復コストです（既定 5）。画面の一気通貫は method=grid、制限時間 20000ms、ウォークフォワードとレポート込みです。",
    note: "試行数か制限時間のどちらかに達すると打ち切ります。打ち切った解は候補です。格子を走査し切ったときだけ「探索空間内の最良」と書きます。最適とは呼びません。",
  },
  {
    no: "05",
    title: "一気通貫を実行する",
    body: "緑の「一気通貫」で POST /pipeline が走ります。バックテスト → KPI → パラメータ探索 → 複数戦略比較 → レーダー → レポートまで一気に進みます。実行中はボタンが「実行中…」になり、完了すると左に資産曲線、右にレーダー、下に KPI・比較表・Markdown が出ます。",
    note: "単体 API も使えます。POST /backtest は1戦略、/optimize は探索、/compare は比較、/report は HTML です。探索本体は backend/app/services/ に閉じ、FastAPI ルートには埋めません。",
  },
];

const ADVANCED_STEPS: Step[] = [
  {
    no: "06",
    title: "KPI と注記を読む",
    body: "先頭行は目的関数順です。Sharpe、リターン、最大ドローダウン、勝率、売買回数、堅牢性ラベルを出します。目的関数は Sharpe − DD ペナルティ + リターン（kpi.objective）です。画面上の緑の注記にデータ源・本数・探索済みかどうかが付きます。",
    note: "堅牢性は fx と同じウォークフォワード（IS/OOS）です。ラベルは walk_forward.summary.robustness_label です。打ち切り時の note は「時間または試行回数で打ち切った候補です。最適とは呼びません。」です。",
  },
  {
    no: "07",
    title: "チャートと比較表を見る",
    body: "左の資産曲線は選択戦略の資産（緑実線）とバイ＆ホールド（灰破線）です。右のレーダー軸は Sharpe / リターン / 耐DD / 勝率 / 堅牢性 / 売買回数です。下の表は戦略ごとの Sharpe・リターン・DD・勝率・目的関数です。",
    note: "チャートは ECharts ではなく SVG です。色は StockAI と同じ緑・黄・ミュート・赤です。レーダーの値は 0〜100 に正規化した比較用で、Sharpe そのものではありません。",
  },
  {
    no: "08",
    title: "レポートを保存する",
    body: "「Markdown を保存」で fso-<銘柄>.md をダウンロードできます。本文は画面のレポート欄と同じで、入力・KPI・探索の打ち切り有無・比較順位を含みます。",
    note: "Postgres があるときだけ strategy_runs に残します。DATABASE_URL が無い、または接続できないときは persisted_run_id は空で、探索自体は動きます。Railway で残すなら Postgres を付けて DATABASE_URL を接続します。",
  },
  {
    no: "09",
    title: "統合資産と差し替えを確認する",
    body: "画面下の一覧は StockPricePredictionTool、fx、Heuristic Optimizer、Backtest Engine です。「検出」はパスが見つかったとき、「パス未検出（ローカル実装で代替）」はアダプタがローカル実装に落ちたときです。役割の説明も同じ行に出ます。",
    note: "StockAI と fx は置き換えません。実 OHLCV や既存バックテストへ進めるときはアダプタ経由です。作業の対応表は docs/作業内容.md、起動と制約は README.md と skill/financial-strategy-optimizer/SKILL.md です。",
  },
];

const TIPS: { title: string; body: string }[] = [
  {
    title: "「探索空間内の最良」と「候補」を混同しない",
    body: "格子を走査し切ったとき（exhausted=true）だけ「探索空間内の最良」です。試行数や 20000ms で止まった結果は候補です。先頭の Sharpe が高くても最適とは呼びません。顧客説明でも同じ言い方にしてください。",
  },
  {
    title: "API に接続できない・ポートが埋まっている",
    body: "右上のピルが API down なら backend を確認します。3020 / 8020 / 5434 が他コンテナで埋まっているときは docker compose down してから start.cmd をやり直します。古い financialstrategyoptimize-* コンテナが残っていると同じポートを掴みます。",
  },
  {
    title: "cmd から起動できない・Railway が失敗する",
    body: "コマンドプロンプトは start.cmd、PowerShell は .\\start.ps1 です。Railway は Railpack ではなくルート Dockerfile（railway.toml）です。公開 URL が画面で、API は同じオリジンの /api です。Postgres が無くても探索は動きます。",
  },
  {
    title: "実行が長い・結果が毎回違う",
    body: "試行数を増やす、または戦略を増やすと制限時間まで待ちます。再現したいときは seed を固定します。サンプル系列は seed で決まる疑似 OHLCV なので、同じ入力なら同じ曲線になります。実データ差し替え後はソース側の系列に従います。",
  },
  {
    title: "これは需要探索でも発注でもない",
    body: "この画面は売買戦略のバックテストと比較です。GitHub 需要スコア、実ブローカー発注、工場レイアウト探索は別パッケージです。mode: paper / live: paper は紙上評価で、証券 API への発注はしません。",
  },
];

export function GuideModal({ onClose }: { onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const [atBottom, setAtBottom] = useState(false);
  const handleScroll = useCallback(() => {
    const el = bodyRef.current;
    if (!el) return;
    setAtBottom(el.scrollTop + el.clientHeight >= el.scrollHeight - 24);
  }, []);

  useEffect(() => {
    closeRef.current?.focus();
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  return (
    <div className="guide-overlay" onClick={onClose} role="presentation">
      <div className="guide-panel" role="dialog" aria-modal="true" aria-labelledby="guide-title" onClick={(e) => e.stopPropagation()}>
        <header className="guide-header">
          <span className="guide-bar" />
          <div className="guide-heading">
            <h2 id="guide-title">利用手順</h2>
            <p className="guide-eyebrow">FINANCIAL STRATEGY GUIDE</p>
          </div>
          <span className="guide-spacer" />
          {!atBottom && <span className="guide-scroll-hint">スクロールして確認</span>}
          <button ref={closeRef} type="button" className="guide-close" onClick={onClose} aria-label="閉じる">
            ×
          </button>
        </header>
        <div className="guide-body" ref={bodyRef} onScroll={handleScroll}>
          <section className="guide-card guide-card-hero">
            <p className="guide-card-eyebrow">株 / FX / バックテスト / 探索 / 比較</p>
            <h3>Financial Strategy Optimizer</h3>
            <p className="guide-card-text">
              StockPricePredictionTool と fx を残したまま、ヒューリスティック探索とバックテストエンジンを束ね、
              バックテスト → KPI → パラメータ探索 → 複数戦略比較 → レーダー → レポートまで一気通貫します。
              格子を走査し切ったときだけ「探索空間内の最良」と書きます。打ち切りは候補です。最適とは呼びません。
            </p>
            <div className="guide-tags">
              {TAGS.map((tag) => (
                <span key={tag} className="guide-tag">
                  {tag}
                </span>
              ))}
            </div>
          </section>

          <section className="guide-card guide-card-arch">
            <p className="guide-card-eyebrow">ARCHITECTURE</p>
            <h3>Next.js 画面 + FastAPI 探索エンジン</h3>
            <p className="guide-card-text">
              ローカルではブラウザは 3020 だけ見れば動きます。画面からの API はコンテナ内で /api が
              バックエンドへ中継します。Railway でも同じオリジンの /api です。探索とバックテストは
              backend/app/services/ に閉じます。
            </p>
            <ul className="guide-list">
              <li>Next.js — 銘柄・戦略・seed、一気通貫、資産曲線、レーダー、KPI、レポート保存</li>
              <li>FastAPI — /health /catalog /sample /backtest /optimize /compare /pipeline /report</li>
              <li>pandas 単一エンジン — KPI スキーマを戦略間で揃える。曲線は探索後パラメータ</li>
              <li>grid / random / sa — seed・試行数・制限時間。未証明を最適と呼ばない</li>
              <li>Yahoo / StockAI HTTP / Stooq — 取れた日足を使う。失敗時だけサンプル</li>
              <li>PostgreSQL 16 — ホスト 5434。無いときは永続化だけスキップ</li>
            </ul>
          </section>

          <p className="guide-section-label">BASIC WORKFLOW</p>
          {BASIC_STEPS.map((step) => (
            <StepCard key={step.no} step={step} />
          ))}

          <p className="guide-section-label">ADVANCED</p>
          {ADVANCED_STEPS.map((step) => (
            <StepCard key={step.no} step={step} />
          ))}

          <p className="guide-section-label">PRINCIPLES</p>
          <section className="guide-card guide-card-arch">
            <p className="guide-card-eyebrow">RULES</p>
            <h3>このパッケージが守っていること</h3>
            <ul className="guide-list">
              <li>証明していない解を「最適」と呼ばない</li>
              <li>探索・バックテストを FastAPI ルートへ埋め込まない</li>
              <li>乱数を使う探索は seed で再現する</li>
              <li>StockAI と fx を置き換えない。アダプタとローカル実装で束ねる</li>
              <li>サンプル系列を実市場の確定値と書かない</li>
              <li>目的関数は kpi.objective。ルートで再計算しない</li>
              <li>利用手順の起動・ポート・最適の言い方を README と Skill に揃える</li>
            </ul>
          </section>

          <p className="guide-section-label">TIPS</p>
          <section className="guide-card">
            <dl className="guide-faq">
              {TIPS.map((tip) => (
                <div key={tip.title}>
                  <dt>{tip.title}</dt>
                  <dd>{tip.body}</dd>
                </div>
              ))}
            </dl>
          </section>

          <p className="guide-footnote">
            詳細は README.md、docs/作業内容.md、CLAUDE.md、
            skill/financial-strategy-optimizer/SKILL.md です。探索ロジックは backend/app/services/ に閉じます。
          </p>
        </div>
      </div>
    </div>
  );
}

function StepCard({ step }: { step: Step }) {
  return (
    <section className="guide-step">
      <span className="guide-step-no" aria-hidden="true">
        {step.no}
      </span>
      <div className="guide-step-main">
        <h3>{step.title}</h3>
        <p>{step.body}</p>
        {step.note && <p className="guide-note">{step.note}</p>}
      </div>
    </section>
  );
}

export function GuideButton() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button type="button" className="pill" onClick={() => setOpen(true)}>
        利用手順
      </button>
      {open && <GuideModal onClose={() => setOpen(false)} />}
    </>
  );
}
