import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    // jsdom for renderLatex (needs document, getComputedStyle, etc. via katex)
    environment: "jsdom",
    include: ["src/**/__tests__/**/*.test.{ts,tsx}"],
    css: false,
  },
});
