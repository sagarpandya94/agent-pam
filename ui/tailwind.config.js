/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["'Space Mono'", "monospace"],
        body: ["'DM Sans'", "sans-serif"],
      },
      colors: {
        surface: "#0a0a0f",
        panel: "#12121a",
        border: "#1e1e2e",
        amber: {
          400: "#fbbf24",
          500: "#f59e0b",
        },
        emerald: { 400: "#34d399" },
        rose: { 400: "#fb7185" },
        sky: { 400: "#38bdf8" },
      },
    },
  },
  plugins: [],
}
