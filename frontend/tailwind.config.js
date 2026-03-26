/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Inter"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
      colors: {
        navy: "#1B2A4A",
        accent: "#3B7DD8",
        "accent-light": "#EBF4FF",
        border: "#E2E8F0",
        muted: "#718096",
        success: "#38A169",
        warning: "#D69E2E",
        danger: "#E53E3E",
      },
      borderRadius: {
        card: "8px",
        btn: "6px",
        input: "4px",
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.08)",
        "card-hover": "0 4px 12px rgba(0,0,0,0.1)",
        btn: "0 1px 2px rgba(0,0,0,0.05)",
      },
    },
  },
  plugins: [],
};
