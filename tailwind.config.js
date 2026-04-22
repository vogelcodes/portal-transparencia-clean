/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/templates/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        surface: "#FFFFFF",
        "surface-dim": "#FAFAFA",
        "surface-bright": "#F8F8F8",
        "surface-container-lowest": "#FFFFFF",
        "surface-container-low": "#FAFAFA",
        "surface-container": "#F8F8F8",
        "surface-container-high": "#F0F0F0",
        "surface-container-highest": "#E8E8E8",
        "on-surface": "#1a1a1a",
        "on-surface-variant": "#333333",
        primary: "#1351B4",
        "on-primary": "#FFFFFF",
        "primary-container": "#E8F0FE",
        "on-primary-container": "#0D47A1",
        secondary: "#455A64",
        "on-secondary": "#FFFFFF",
        "secondary-container": "#ECEFF1",
        "on-secondary-container": "#37474F",
        tertiary: "#071D41",
        "on-tertiary": "#FFFFFF",
        error: "#B00020",
        "on-error": "#FFFFFF",
        "error-container": "#FDECEA",
        "on-error-container": "#B00020",
        background: "#FFFFFF",
        "on-background": "#1a1a1a",
      },
      fontFamily: {
        rawline: ["Rawline", "Raleway", "sans-serif"],
      },
      fontSize: {
        "display-lg": [
          "34.832px",
          {
            lineHeight: "40.0568px",
            letterSpacing: "-0.02em",
            fontWeight: "600",
          },
        ],
        "headline-lg": [
          "28px",
          { lineHeight: "36px", letterSpacing: "-0.01em", fontWeight: "500" },
        ],
        "headline-md": ["24px", { lineHeight: "32px", fontWeight: "500" }],
        "body-lg": ["18px", { lineHeight: "26px", fontWeight: "400" }],
        "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "label-sm": [
          "12px",
          { lineHeight: "16px", letterSpacing: "0.05em", fontWeight: "600" },
        ],
      },
      borderRadius: {
        sm: "2px",
        DEFAULT: "3px",
        md: "4px",
        lg: "6px",
        xl: "12px",
      },
      boxShadow: {
        card: "0 6px 6px rgba(0, 0, 0, 0.16)",
        elevated: "0 8px 16px rgba(0, 0, 0, 0.2)",
      },
    },
  },
  plugins: [],
};
