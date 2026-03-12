---
description: "General-purpose prompt for feature development. Use when adding new features, fixing bugs, or making improvements to the app."
applyTo: "**/*.{html,css,js}"
---

# Pokemon TCG Collector — Development Instructions

## Project constraints (always apply)

- No build step, no npm, no bundlers — static files only
- Vue 3 via CDN (`<script>` tags, no SFC, no `.vue` files)
- All app logic in `index.html`, all styles in `styles.css`
- Offline-first: Service Worker + IndexedDB + pokemonData.js fallback

## Before editing

1. Read `ARCHITECTURE.md` for system design context
2. If touching API code, read `MIGRATION.md` for migration status
3. Check the `CONFIG` object in `index.html` for current configuration

## After editing

1. If you changed the system structure → update `ARCHITECTURE.md`
2. If you changed cached assets → bump `CACHE_NAME` in `sw.js`
3. If you changed the API layer → update `MIGRATION.md`
4. Test with `python3 -m http.server 8000`
