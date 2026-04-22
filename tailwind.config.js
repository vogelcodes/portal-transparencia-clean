/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/templates/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        // Surface colors
        surface: "var(--color-surface)",
        "surface-dim": "var(--color-surface-dim)",
        "surface-bright": "var(--color-surface-bright)",
        "surface-container-lowest": "var(--color-surface-container-lowest)",
        "surface-container-low": "var(--color-surface-container-low)",
        "surface-container": "var(--color-surface-container)",
        "surface-container-high": "var(--color-surface-container-high)",
        "surface-container-highest": "var(--color-surface-container-highest)",

        // On Surface colors
        "on-surface": "var(--color-on-surface)",
        "on-surface-variant": "var(--color-on-surface-variant)",
        "inverse-surface": "var(--color-inverse-surface)",
        "inverse-on-surface": "var(--color-inverse-on-surface)",

        // Outline colors
        outline: "var(--color-outline)",
        "outline-variant": "var(--color-outline-variant)",
        "surface-tint": "var(--color-surface-tint)",

        // Primary colors
        primary: "var(--color-primary)",
        "on-primary": "var(--color-on-primary)",
        "primary-container": "var(--color-primary-container)",
        "on-primary-container": "var(--color-on-primary-container)",
        "inverse-primary": "var(--color-inverse-primary)",

        // Secondary colors
        secondary: "var(--color-secondary)",
        "on-secondary": "var(--color-on-secondary)",
        "secondary-container": "var(--color-secondary-container)",
        "on-secondary-container": "var(--color-on-secondary-container)",

        // Tertiary colors
        tertiary: "var(--color-tertiary)",
        "on-tertiary": "var(--color-on-tertiary)",
        "tertiary-container": "var(--color-tertiary-container)",
        "on-tertiary-container": "var(--color-on-tertiary-container)",

        // Error colors
        error: "var(--color-error)",
        "on-error": "var(--color-on-error)",
        "error-container": "var(--color-error-container)",
        "on-error-container": "var(--color-on-error-container)",

        // Semantic colors
        background: "var(--color-background)",
        border: "var(--color-border)",
        "surface-muted": "var(--color-surface-muted)",
      },
      fontFamily: {
        anthropic: ["Anthropic", "sans-serif"],
        rawline: ["Anthropic", "Rawline", "Raleway", "Segoe UI", "sans-serif"],
        sans: ["Anthropic", "Rawline", "Raleway", "Segoe UI", "sans-serif"],
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
        full: "9999px",
      },
      boxShadow: {
        card: "0 6px 6px rgba(0, 0, 0, 0.16)",
        elevated: "0 8px 16px rgba(0, 0, 0, 0.2)",
        glass: "0 8px 32px 0 rgba(0, 0, 0, 0.1)",
      },
      spacing: {
        unit: "8px",
        container: "24px",
        card: "16px",
        section: "40px",
      },
    },
  },
  plugins: [],
};
