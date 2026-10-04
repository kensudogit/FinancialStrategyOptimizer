import type { ReactNode } from "react";
import "./globals.css";

export const metadata = {
  title: "Financial Strategy Optimizer",
  description: "株・FX戦略のバックテストから最適化・比較・レポートまで",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
