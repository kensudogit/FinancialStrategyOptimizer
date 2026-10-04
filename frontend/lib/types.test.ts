/**
 * @file types.test.ts
 * @description 共有型とフィクスチャの形。実 API には到達しない。
 */

import { describe, expect, it } from "vitest";
import * as fixtures from "@/test/fixtures";

describe("types fixtures", () => {
  it("catalog が株と FX を持つ", () => {
    const body = fixtures.catalog();
    expect(body.assets.stock[0].symbol).toBe("7203.T");
    expect(body.assets.fx[0].symbol).toBe("USDJPY");
    expect(body.strategies[0].id).toBe("sma_crossover");
  });

  it("pipelineOut が KPI とレーダーを持つ", () => {
    const body = fixtures.pipelineOut();
    expect(body.comparison.ranking[0].kpi.sharpe).toBeGreaterThan(0);
    expect(body.comparison.radar_series[0].axes).toHaveLength(6);
    expect(body.report_markdown).toContain("レポート");
  });
});
