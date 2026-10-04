"use client";

import { useCallback, useEffect, useRef, useState } from "react";

const STEPS = [
  {
    no: "01",
    title: "アプリを起動する",
    body: "リポジトリ直下で start.cmd または .\\start.ps1 を実行します。COMPOSE_BAKE=false 付きの docker compose です。画面は http://localhost:3020、API は http://localhost:8020/docs です。8000/3000 と 8010/3010 は既存システム用に空けています。",
  },
  {
    no: "02",
    title: "資産クラスと銘柄を選ぶ",
    body: "株は StockPricePredictionTool 側の銘柄（7203.T など）、FX は fx 側の通貨ペア（USDJPY など）です。既存パッケージは捨てず、この画面が統合入口になります。",
  },
  {
    no: "03",
    title: "戦略を複数選ぶ",
    body: "SMAクロスは StockAI、RSI/MACD は fx、ドンチャンは統合バックテストエンジンです。バイ＆ホールドは比較用の基準線です。",
  },
  {
    no: "04",
    title: "一気通貫を実行する",
    body: "「一気通貫」で バックテスト → KPI → パラメータ探索 → 最適化 → 複数戦略比較 → レーダー → レポート まで走ります。seed を固定すると再現できます。",
  },
  {
    no: "05",
    title: "数字の読み方",
    body: "格子を走査し切ったときだけ「探索空間内の最良」と書きます。打ち切りなら候補です。最適とは呼びません。ウォークフォワードの堅牢性は fx と同じ IS/OOS 評価です。",
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
            <p className="guide-card-eyebrow">株 / FX / バックテスト / 最適化</p>
            <h3>Financial Strategy Optimizer</h3>
            <p className="guide-card-text">
              StockPricePredictionTool と fx を残したまま、ヒューリスティック探索とバックテストエンジンを束ね、
              戦略比較とレポートまで一気通貫にします。
            </p>
          </section>
          {STEPS.map((step) => (
            <section className="guide-step" key={step.no}>
              <span className="guide-step-no">{step.no}</span>
              <div>
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </div>
            </section>
          ))}
          <p className="guide-footnote">
            詳細は README.md と docs/作業内容.md。探索ロジックは backend/app/services/ に閉じます。
          </p>
        </div>
      </div>
    </div>
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
