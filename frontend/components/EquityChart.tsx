"use client";

export function EquityChart({
  points,
}: {
  points: { ts: string; equity: number; buy_hold: number }[];
}) {
  if (points.length < 2) return null;
  const w = 520;
  const h = 180;
  const pad = 28;
  const ys = points.flatMap((p) => [p.equity, p.buy_hold]);
  const min = Math.min(...ys);
  const max = Math.max(...ys);
  const x = (i: number) => pad + (i / (points.length - 1)) * (w - pad * 2);
  const y = (v: number) => h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2);
  const line = (key: "equity" | "buy_hold") => points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(p[key])}`).join(" ");

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="equity" role="img" aria-label="資産曲線">
      <path d={line("buy_hold")} fill="none" stroke="#b2bec3" strokeWidth="1.6" />
      <path d={line("equity")} fill="none" stroke="#6c5ce7" strokeWidth="2" />
      <text x={pad} y={16} fontSize="11" fill="#6c5ce7">
        戦略
      </text>
      <text x={70} y={16} fontSize="11" fill="#636e72">
        バイ＆ホールド
      </text>
    </svg>
  );
}
