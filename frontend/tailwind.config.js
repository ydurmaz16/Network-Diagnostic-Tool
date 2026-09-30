/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#14213d",
        paper: "#eef2f5",
        line: "#d3dce6",
        accent: "#2f5bea",
        ok: "#12805c",
        warn: "#b7791f",
        bad: "#c0392b",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "Segoe UI", "Roboto", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
