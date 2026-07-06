/** Design tokens from docs/UI_UX_DESIGN.md §2 — India-first, non-partisan palette. */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        indigo: { 700: "#2B3A67", 600: "#34478A" },
        teal: { 500: "#0E8F8F", 50: "#E6F4F4" },
        ink: { 900: "#1A1C21", 600: "#4A4E57", 400: "#8A8F99" },
        bl: {
          surface: "#FFFFFF",
          bg: "#F7F8FA",
          border: "#E5E7EB",
        },
        good: { 600: "#2E7D5B", 50: "#E8F3EE" },
        warn: { 600: "#B7791F", 50: "#FBF3E2" },
        review: { 600: "#B0413E", 50: "#F7E9E8" },
        redteam: { DEFAULT: "#A65A4E", 50: "#F6EAE7" },
        blueteam: { DEFAULT: "#3E6690", 50: "#E9EFF6" },
        council: { DEFAULT: "#6B4E9E", 50: "#EEE9F6" },
      },
      fontFamily: {
        sans: ["Mukta", "Hind", "Inter", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "apac-gradient": "linear-gradient(90deg, #FF7A2F 0%, #FF477E 100%)",
      },
      borderRadius: {
        card: "16px",
        btn: "12px",
      },
    },
  },
  plugins: [],
};
