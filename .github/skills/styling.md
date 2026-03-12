---
description: "Use when editing styles.css or any visual/UI-related changes. Provides CSS conventions, variable system, and responsive design patterns."
---

# Styling & UI Skill

You are editing the visual layer of the Pokemon TCG Collector App.

## CSS Architecture

All styles live in `styles.css` (~1570 lines), organized in sections:

1. **Theme Variables** — `:root` custom properties
2. **Global Styles** — Body, fonts, box-sizing
3. **Header Styles** — App header, branding
4. **Tabs Component** — Pokemon species tabs, view tabs
5. **Controls & Filters** — Search, sort, filter bar
6. **Cards & Collections** — Card grid, card details
7. **Modal Component** — Detail modal overlay
8. **Loading & State Indicators** — Spinners, offline badge
9. **Responsive Styles** — Media queries

## Rules

- **Use CSS variables** — Never hardcode colors. Use `var(--primary-color)` etc.
- **Follow section structure** — Add new styles to the appropriate section
- **Glassmorphism aesthetic** — `backdrop-filter: blur()`, semi-transparent backgrounds
- **Mobile-first** — Base styles for mobile, media queries for larger screens
- **BEM-ish naming** — `.card-component`, `.card-component__title`, `.card-component--bought`
- **No CSS-in-JS** — All styles in `styles.css`, minimize inline styles in HTML

## Key CSS variables

```css
--bg-gradient          /* Page background */
--card-bg              /* Card background */
--card-border          /* Card border */
--font-primary         /* Poppins font family */
--font-color           /* Text color */
--primary-color        /* Red accent (#ff5252) */
--secondary-color      /* Blue accent (#3a67cf) */
--success-color        /* Green (#2ecc71) */
--glassmorphism        /* Glass panel background */
--card-glow            /* Card hover glow effect */
```

## Responsive breakpoints

Follow existing media queries in the Responsive section at the bottom of `styles.css`.
