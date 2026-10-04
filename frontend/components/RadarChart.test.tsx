/**
 * @file RadarChart.test.tsx
 * @description レーダーの表示。
 */

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { RadarChart } from "./RadarChart";

describe("RadarChart", () => {
  it("系列が空なら何も出さない", () => {
    const { container } = render(<RadarChart series={[]} />);
    expect(container.querySelector("svg")).toBeNull();
  });

  it("系列があればレーダーを出す", () => {
    render(
      <RadarChart
        series={[
          {
            name: "sma",
            values: [50, 40, 30, 20, 10, 5],
            axes: ["Sharpe", "リターン", "耐DD", "勝率", "堅牢性", "売買回数"],
          },
        ]}
      />,
    );
    expect(screen.getByRole("img", { name: "戦略レーダー" })).toBeTruthy();
  });
});
