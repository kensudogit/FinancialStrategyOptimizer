/**
 * @file tests/page.test.tsx
 * @description テスト結果画面。実バックエンドには到達しない。
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import TestsPage from "./page";

function jsonResponse(body: unknown, ok = true, status = 200) {
  return Promise.resolve({
    ok,
    status,
    text: async () => (typeof body === "string" ? body : JSON.stringify(body)),
  });
}

function mockApis() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation((url: string) => {
      if (String(url).includes("/tests/summary")) {
        return jsonResponse({
          status: "ok",
          generated_at: "2026-10-04T00:00:00Z",
          backend: { passed: 2, failed: 0, suites: [] },
          frontend: { passed: 1, failed: 0, suites: [] },
          totals: { total: 3, passed: 3, failed: 0, skipped: 0, ok: true },
        });
      }
      return jsonResponse("", false, 404);
    }),
  );
}

async function waitReady() {
  await waitFor(() => expect(screen.getByRole("heading", { name: "テスト結果" })).toBeTruthy());
}

describe("TestsPage", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("summary を表示する", async () => {
    mockApis();
    render(<TestsPage />);
    await waitReady();
    await waitFor(() => expect(screen.getByText("PASS")).toBeTruthy());
  });

  it("API 未起動なら接続案内を出す", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => "Internal Server Error",
      }),
    );
    render(<TestsPage />);
    await waitFor(() =>
      expect(screen.getByText(/API（8020）に接続できません/)).toBeTruthy(),
    );
  });
});
