import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-family)", "var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      colors: {
        // Joel's semantic tokens — driven by per-theme CSS overlays in
        // app/styles/themes/*. Used by all new components ported from Joel.
        text: "var(--text)",
        background: "var(--background)",
        surface: "var(--surface)",
        primary: "var(--primary)",
        secondary: "var(--secondary)",
        accent: "var(--accent)",
        border: "var(--border)",
        muted: "var(--muted)",
        success: "var(--success)",
        warning: "var(--warning)",
        error: "var(--error)",
        // Legacy ink/brand scales — preserved for backward compat with
        // already-shipped components. New work should use the semantic tokens above.
        ink: {
          50: "#f7f8f9",
          100: "#ecedf0",
          200: "#d6d8de",
          300: "#abafba",
          400: "#7a8090",
          500: "#52596b",
          600: "#3a414f",
          700: "#262b38",
          800: "#161a23",
          900: "#0a0c14",
        },
        brand: {
          50: "#eef2ff",
          100: "#dee5ff",
          500: "#4759f5",
          600: "#3845d8",
          700: "#2c35a8",
        },
      },
      backgroundImage: {
        "hero-grad":
          "radial-gradient(1200px circle at 30% 0%, rgba(71,89,245,0.08), transparent 50%)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
