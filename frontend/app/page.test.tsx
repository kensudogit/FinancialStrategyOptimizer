/**
 * @file page.test.tsx
 * @description トップ画面。実 API には到達しない。
 *
 * 検証範囲:
 * - カタログ表示
 * - 一気通貫後の KPI
 */

import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import Page from "./page";
import * as api from "@/lib/api";
import * as fixtures from "@/test/fixtures";

function mockApis() {
  vi.spyOn(api.api, "catalog").mockResolvedValue(fixtures.catalog());
  vi.spyOn(api.api, "pipeline").mockResolvedValue(fixtures.pipelineOut());
}

async function waitReady() {
  await waitFor(() => expect(screen.getByRole("heading", { name: /一つの画面で/ })).toBeTruthy());
}

describe("Page", () => {
  it("カタログ後に一気通貫できる", async () => {
    mockApis();
    render(<Page />);
    await waitReady();
    await waitFor(() => expect(screen.getByText("SMAクロス")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "一気通貫" }));
    await waitFor(() => expect(screen.getByText(/7203\.T/)).toBeTruthy());
    expect(api.api.pipeline).toHaveBeenCalled();
  });

  it("API 失敗なら down と出す", async () => {
    vi.spyOn(api.api, "catalog").mockRejectedValue(new Error("down"));
    render(<Page />);
    await waitFor(() => expect(screen.getByText("APIに接続できません")).toBeTruthy());
    expect(document.querySelector(".dotBad")).toBeTruthy();
  });
});
