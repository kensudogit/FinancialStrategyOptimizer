"use client";

import type { RadarAxis } from "@/lib/types";

export function RadarChart({
  series,
}: {
  series: { name: string; values: number[]; axes: string[] }[] | { radar: RadarAxis[]; name: string }[];
}) {
  const first = series[0];
  if (!first) return null;
  const axes = "axes" in first ? first.axes : first.radar.map((a) => a.axis);
  const n = axes.length;
  const cx = 140;
  const cy = 140;
  const r = 92;
  const colors = ["#3dd68c", "#e8b84a", "#8aa396", "#e85d5d"];

  function point(index: number, value: number) {
    const angle = -Math.PI / 2 + (index * 2 * Math.PI) / n;
    const rad = (Math.max(0, Math.min(100, value)) / 100) * r;
    return [cx + rad * Math.cos(angle), cy + rad * Math.sin(angle)];
  }

  return (
    <svg viewBox="0 0 280 280" className="radar" role="img" aria-label="戦略レーダー">
      {[0.25, 0.5, 0.75, 1].map((scale) => (
        <polygon
          key={scale}
          fill="none"
          stroke="#2a3a32"
          points={axes
            .map((_, i) => point(i, scale * 100).join(","))
            .join(" ")}
        />
      ))}
      {axes.map((axis, i) => {
        const [x, y] = point(i, 100);
        const [lx, ly] = point(i, 118);
        return (
          <g key={axis}>
            <line x1={cx} y1={cy} x2={x} y2={y} stroke="#2a3a32" />
            <text x={lx} y={ly} textAnchor="middle" fontSize="10" fill="#8aa396">
              {axis}
            </text>
          </g>
        );
      })}
      {series.map((item, s) => {
        const values = "values" in item ? item.values : item.radar.map((a) => a.value);
        const pts = values.map((v, i) => point(i, v).join(",")).join(" ");
        return (
          <polygon key={item.name} points={pts} fill={colors[s % colors.length]} fillOpacity="0.18" stroke={colors[s % colors.length]} />
        );
      })}
    </svg>
  );
}
