/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080c14",
        surface: {
          DEFAULT: "#0f172a",
          secondary: "#141e33",
          hover: "#1a2744",
          border: "#1e293b",
        },
        navy: {
          950: "#040711",
          900: "#080c14",
          800: "#0f172a",
          700: "#1e293b",
          600: "#334155",
        },
        primary: {
          DEFAULT: "#38bdf8",
          hover: "#0284c7",
          foreground: "#080c14",
        },
        safe: {
          DEFAULT: "#10b981",
          light: "#d1fae5",
          dark: "#065f46",
          bg: "rgba(16, 185, 129, 0.1)",
        },
        warning: {
          DEFAULT: "#f59e0b",
          light: "#fef3c7",
          dark: "#78350f",
          bg: "rgba(245, 158, 11, 0.1)",
        },
        critical: {
          DEFAULT: "#ef4444",
          light: "#fee2e2",
          dark: "#7f1d1d",
          bg: "rgba(239, 68, 68, 0.1)",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "-apple-system", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        subtle: "0 1px 2px 0 rgba(0, 0, 0, 0.35)",
        card: "0 4px 6px -1px rgba(0, 0, 0, 0.25), 0 2px 4px -2px rgba(0, 0, 0, 0.25)",
      },
    },
  },
  plugins: [],
};

