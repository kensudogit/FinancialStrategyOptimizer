import path from "path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  esbuild: {
    jsx: "automatic",
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./test/setup.ts"],
    include: ["**/*.{test,spec}.{ts,tsx}"],
    exclude: ["node_modules", ".next"],
    reporters: ["default", "junit"],
    outputFile: { junit: "./public/test-results/frontend-junit.xml" },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname),
    },
  },
});
