---
name: "Portal da Transparência - Empenho"
description: "Design system extracted from portaldatransparencia.gov.br/despesas/recursos-recebidos/empenho/ (light UI)."
colors:
  surface: "#FFFFFF"
  surface-dim: "#FAFAFA"
  surface-bright: "#F8F8F8"
  surface-container-lowest: "#FFFFFF"
  surface-container-low: "#FAFAFA"
  surface-container: "#F8F8F8"
  surface-container-high: "#F0F0F0"
  surface-container-highest: "#E8E8E8"
  on-surface: "#1a1a1a"
  on-surface-variant: "#333333"
  inverse-surface: "#1a1a1a"
  inverse-on-surface: "#FFFFFF"
  outline: "#333333"
  outline-variant: "#CCCCCC"
  surface-tint: "#1351B4"
  primary: "#1351B4"
  on-primary: "#FFFFFF"
  primary-container: "#E8F0FE"
  on-primary-container: "#0D47A1"
  inverse-primary: "#90CAF9"
  secondary: "#455A64"
  on-secondary: "#FFFFFF"
  secondary-container: "#ECEFF1"
  on-secondary-container: "#37474F"
  tertiary: "#071D41"
  on-tertiary: "#FFFFFF"
  tertiary-container: "#E3F2FD"
  on-tertiary-container: "#0D47A1"
  error: "#B00020"
  on-error: "#FFFFFF"
  error-container: "#FDECEA"
  on-error-container: "#B00020"
  primary-fixed: "#1351B4"
  primary-fixed-dim: "#0D47A1"
  on-primary-fixed: "#FFFFFF"
  on-primary-fixed-variant: "#E3F2FD"
  secondary-fixed: "#455A64"
  secondary-fixed-dim: "#37474F"
  on-secondary-fixed: "#FFFFFF"
  on-secondary-fixed-variant: "#ECEFF1"
  tertiary-fixed: "#071D41"
  tertiary-fixed-dim: "#0D47A1"
  on-tertiary-fixed: "#FFFFFF"
  on-tertiary-fixed-variant: "#E3F2FD"
  background: "#FFFFFF"
  on-background: "#1a1a1a"
  surface-variant: "#F8F8F8"
  border: "#333333"
  surface-muted: "#071D41"
typography:
  display-lg:
    fontFamily: "Rawline, Raleway, sans-serif"
    fontSize: 34.832px
    fontWeight: "600"
    lineHeight: 40.0568px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: "Rawline, Raleway, sans-serif"
    fontSize: 28px
    fontWeight: "500"
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: "Rawline, Raleway, sans-serif"
    fontSize: 24px
    fontWeight: "500"
    lineHeight: 32px
  body-lg:
    fontFamily: "Rawline, Raleway, sans-serif"
    fontSize: 18px
    fontWeight: "400"
    lineHeight: 26px
  body-md:
    fontFamily: "Rawline, Raleway, sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
  label-sm:
    fontFamily: "Rawline, Raleway, sans-serif"
    fontSize: 12px
    fontWeight: "600"
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 2px
  DEFAULT: 3px
  md: 4px
  lg: 6px
  xl: 12px
  full: 9999px
spacing:
  unit: 8px
  container-padding: 24px
  card-gap: 16px
  section-margin: 40px
  xs: 2.70312px
  sm: 3px
  md: 4px
  lg: 5px
  xl: 6px
  2xl: 8px
components:
  glass-card-standard:
    backgroundColor: "{colors.surface-container}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "{spacing.card-gap}"
  glass-card-elevated:
    backgroundColor: "{colors.surface-container-highest}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
    padding: "{spacing.card-gap}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.md}"
    padding: 8px 24px
  button-primary-hover:
    backgroundColor: "{colors.primary-fixed-dim}"
  button-secondary:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.primary}"
    borderColor: "{colors.primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.md}"
    padding: 8px 24px
  button-ghost:
    backgroundColor: transparent
    textColor: "{colors.primary}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.md}"
  input-field:
    backgroundColor: "{colors.surface-dim}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.border}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: 12px 16px
  input-field-focus:
    borderColor: "{colors.primary}"
    boxShadow: "0 0 0 2px rgba(19, 81, 180, 0.2)"
  weather-display-large:
    textColor: "{colors.on-surface}"
    typography: "{typography.display-lg}"
  metric-label:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.label-sm}"
  list-item-interactive:
    backgroundColor: transparent
    rounded: "{rounded.md}"
    padding: 12px
  list-item-interactive-hover:
    backgroundColor: "{colors.surface-container}"
  card-default:
    backgroundColor: "{colors.surface-dim}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
  nav-default:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.md}"
  badge-default:
    backgroundColor: "{colors.surface-muted}"
    textColor: "{colors.on-tertiary}"
    rounded: "{rounded.full}"
    padding: 4px 12px
---

## Brand & Style

This design system represents the visual identity of the Brazilian government's Portal da Transparência, focused on presenting budget commitment documents (Empenhos) with clarity, trust, and institutional authority.

The brand personality is **professional, accessible, and government-appropriate**: clean surfaces with clear hierarchy that allow citizens to easily navigate complex financial data. The UI maintains a light, airy aesthetic with blue accent colors that convey reliability and official authority.

The emotional response is intended to be trustworthy and informative—using structured layouts and consistent spacing to reduce cognitive load when processing detailed fiscal information.

## Colors

The color strategy prioritizes readability, accessibility, and professional government aesthetics.

- **Primary Canvas:** Clean white (#FFFFFF) as the main background for maximum legibility.
- **Surface Tones:** Subtle gray variations (#FAFAFA, #F8F8F8, #F0F0F0) for content separation and visual hierarchy.
- **Accent:** Official Blue (#1351B4) used for primary actions, links, and interactive elements—the standard color for Brazilian government digital services.
- **Text:** High-contrast blacks and dark grays (#1a1a1a, #333333) for optimal WCAG AA compliance.
- **Semantic Colors:** Error states use standard red (#B00020), with container variants for better visual feedback.

## Typography

The design system utilizes **Rawline/Raleway** as the official typeface, a government-standard font that balances institutional gravitas with modern digital accessibility.

- **Hierarchy:** Clear progression from display sizes for key figures to smaller labels for metadata and categories.
- **Legibility:** Body text at 16px with 24px line height ensures comfortable reading of dense financial information.
- **Treatment:** Bold weights (700) for labels and key data points; regular weights (400) for descriptive text.

## Layout & Spacing

The layout follows a structured, grid-based model appropriate for data-dense government interfaces.

- **Rhythm:** An 8px base grid governs all dimensions, with specific spacing tokens (xs: 2.7px through 2xl: 8px) for precise control.
- **Grouping:** Content organized in containers with consistent 24px padding and 16px gaps between cards.
- **Container Width:** Standard 1240px content width for optimal readability of tabular data.
- **Negative Space:** Moderate margins (24px) maintain breathing room without wasting valuable screen space.

## Elevation & Depth

Depth in this design system is achieved through subtle shadows and surface variations rather than dramatic glass effects.

- **The Surface Stack:**
  - **Level 1 (Base):** White background with subtle gray tones for content areas.
  - **Level 2 (Cards):** Light gray (#FAFAFA) backgrounds with subtle box shadows.
  - **Level 3 (Elevated):** White surfaces with more pronounced shadows for modals and overlays.
- **Shadow Pattern:** Primary shadow is "0px 6px 6px rgba(0, 0, 0, 0.16)" for card elevation.
- **Borders:** 1px solid borders (#333333) for clear separation of interactive elements like inputs.

## Shapes

The shape language is conservative and government-appropriate, prioritizing clarity over decorative elements.

- **Cards:** Use 6px (lg) for standard container elements.
- **Buttons:** Use 3px (DEFAULT) for primary actions—conservative but still visible.
- **Inputs:** Use 3px (md) for text fields to maintain professional appearance.
- **Badges/Pills:** Use full rounding (9999px) for tag-like elements like status indicators.

## Components

### Cards & Containers

Standard cards use the surface-dim color (#FAFAFA) for background with consistent rounded corners (4px). Elevated surfaces use slightly brighter backgrounds with maintained shadow hierarchy.

### Action Elements

Primary buttons use the official blue (#1351B4) with white text for maximum contrast and accessibility. Secondary buttons use outlined styles with transparent backgrounds to reduce visual weight while maintaining clear affordance.

### Inputs & Interaction

Text inputs use subtle gray backgrounds (#F8F8F8) with dark borders. Focus states introduce a blue ring (2px) to indicate active state clearly.

### Data Display

Key financial figures use display-lg typography for prominence. Supporting labels use label-sm with uppercase treatment for categorization.

## Do's and Don'ts

- Do keep new UI aligned with the extracted spacing and radius scales.
- Do reuse the accent color (#1351B4) for primary interaction emphasis.
- Do maintain the official government blue across all public-facing interfaces.
- Do verify hover, focus, and mobile states manually before treating this as final.
- Don't preserve every one-off exception from the source site.
- Don't introduce extra colors until you verify whether they belong to the core system.
- Don't use decorative elements that could distract from the financial data.
- Don't reduce contrast below WCAG AA standards for any text or interactive element.
