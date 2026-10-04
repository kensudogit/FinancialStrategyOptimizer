/**
 * @file api.test.ts
 * @description `api` のユニットテスト。実 HTTP には到達しない。
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";
import * as fixtures from "@/test/fixtures";

describe("api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("catalog は JSON を返す", async () => {
    const body = fixtures.catalog();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => body,
      }),
    );
    await expect(api.catalog()).resolves.toEqual(body);
  });

  it("失敗時は Error にする", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        text: async () => "boom",
      }),
    );
    await expect(api.catalog()).rejects.toThrow("boom");
  });

  it("sample と pipeline を呼ぶ", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => fixtures.pipelineOut(),
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(api.sample()).resolves.toMatchObject({ symbol: "7203.T" });
    await expect(api.pipeline({ symbol: "7203.T" })).resolves.toMatchObject({ symbol: "7203.T" });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
