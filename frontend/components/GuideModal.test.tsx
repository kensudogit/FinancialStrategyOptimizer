/**
 * @file GuideModal.test.tsx
 * @description 利用手順ボタンとモーダル。
 */

import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { GuideButton } from "./GuideModal";

describe("GuideButton", () => {
  it("初期はモーダルを出さない", () => {
    render(<GuideButton />);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("利用手順でダイアログを開く", () => {
    render(<GuideButton />);
    fireEvent.click(screen.getByRole("button", { name: "利用手順" }));
    expect(screen.getByRole("dialog", { name: "利用手順" })).toBeTruthy();
    expect(screen.getByText("BASIC WORKFLOW")).toBeTruthy();
  });
});
