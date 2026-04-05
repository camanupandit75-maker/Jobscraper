import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-ibm)", "IBM Plex Mono", "monospace"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
        display: ["var(--font-syne)", "Syne", "sans-serif"],
      },
      colors: {
        bg: "#0d0d14",
        surface: "#13131f",
        border: "#1e1e30",
        accent: "#e8c547",
        accent2: "#4fc3f7",
        muted: "#6b6b85",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.4s ease-out forwards",
      },
    },
  },
  plugins: [],
};

export default config;
