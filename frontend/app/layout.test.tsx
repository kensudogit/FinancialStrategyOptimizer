/**
 * @file layout.test.tsx
 * @description ルートレイアウト。実 API には到達しない。
 */

import { describe, expect, it } from "vitest";
import { metadata } from "./layout";

describe("RootLayout", () => {
  it("タイトルを公開する", () => {
    expect(metadata.title).toContain("Financial Strategy Optimizer");
  });
});
