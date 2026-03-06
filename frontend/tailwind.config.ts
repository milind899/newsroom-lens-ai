import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0d0d0d",
          2: "#1a1a1a",
          3: "#2a2a2a",
          4: "#3a3a3a",
        },
        paper: {
          DEFAULT: "#f5f0e8",
          2: "#ede8de",
          3: "#e4dfd4",
        },
        rule: {
          DEFAULT: "#c8c0b0",
          dark: "#2e2e2e",
        },
        chalk: {
          DEFAULT: "#e8e2d8",
          muted: "#9a9490",
          faint: "#5a5450",
        },
        red: {
          ink: "#d4372c",
          dark: "#9b1c14",
          light: "#f87171",
        },
        amber: {
          ink: "#d4831c",
          light: "#fbbf24",
        },
        green: {
          ink: "#1e7c4a",
          light: "#4ade80",
        },
        blue: {
          ink: "#1a4fd4",
          light: "#60a5fa",
        },
        political: {
          left: "#3b82f6",
          center: "#8b5cf6",
          right: "#ef4444",
        },
      },
      fontFamily: {
        display: ["Syne", "sans-serif"],
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["DM Mono", "Consolas", "monospace"],
      },
      fontSize: {
        "2xs": ["10px", "1.4"],
      },
    },
  },
  plugins: [],
};
export default config;
