/**
 * @file EquityChart.test.tsx
 * @description 資産曲線の表示。
 */

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { EquityChart } from "./EquityChart";

describe("EquityChart", () => {
  it("点が足りないと何も出さない", () => {
    const { container } = render(<EquityChart points={[{ ts: "a", equity: 1, buy_hold: 1 }]} />);
    expect(container.querySelector("svg")).toBeNull();
  });

  it("2点以上なら曲線を出す", () => {
    render(
      <EquityChart
        points={[
          { ts: "a", equity: 1, buy_hold: 1 },
          { ts: "b", equity: 1.1, buy_hold: 1.05 },
        ]}
      />,
    );
    expect(screen.getByRole("img", { name: "資産曲線" })).toBeTruthy();
  });
});
