# Copilot Instructions for Pokemon TCG Collector App

## Project Context

This is a **no-build-step** Vue 3 PWA. Everything runs from static files loaded via CDN. There is no npm, no bundler, no `.vue` files.

## Critical Constraints

1. **No build step** — Never introduce webpack, vite, rollup, or any bundler
2. **No package manager** — No npm, yarn, pnpm. Dependencies come from CDNs
3. **No ES modules** — The app uses `<script>` tags, not `import`/`export`
4. **Single-file app** — All Vue logic lives in `index.html` (~2050 lines)
5. **Offline-first** — Service Worker + IndexedDB + pokemonData.js fallback chain

## Code Style

- **JavaScript**: ES6+, no TypeScript, 2-space indent
- **CSS**: BEM-ish naming, CSS custom properties for theming, glassmorphism aesthetic
- **HTML**: Vue 3 template syntax with `v-once` on static content
- **Python**: PEP 8, 4-space indent, used only for data generation scripts

## When Making Changes

### Before editing
- Read `ARCHITECTURE.md` for system design context
- Read `MIGRATION.md` before touching any API-related code
- Understand the storage fallback chain: IndexedDB → localStorage → pokemonData.js

### When editing `index.html`
- Components use template IDs: `template: '#card-template'`
- State lives on root Vue instance (no Vuex/Pinia)
- Use `v-once` on elements that don't need reactivity
- Debounce search inputs (300ms)

### When editing `styles.css`
- Use existing CSS variables from `:root` — don't hardcode colors
- Follow the existing section structure (see Table of Contents comment at top)
- Mobile-first responsive design

### When editing `sw.js`
- Bump `CACHE_NAME` version when changing any cached asset
- Keep the precache list up to date

### When editing Python scripts
- These generate data files — never edit `pokemonData.js` by hand
- Pipeline: scrape → `/data/*.json` → `concat_pokemon_data.py` → `pokemonData.js`

## API Migration

A major API migration is planned. When working on API-related code:
- Isolate API calls behind the `CONFIG` object interface
- Keep response mapping separate from rendering logic
- Document assumptions about API response shapes in comments
- Consider backward compatibility with data cached in IndexedDB
- See `MIGRATION.md` for the full migration plan

## File Roles

| File | Edit? | Notes |
|------|-------|-------|
| `index.html` | Yes | Main app — be careful with the ~2050 line file |
| `index2.html` | Yes | Experimental — safe to break, not production |
| `styles.css` | Yes | All styles — follow CSS variable conventions |
| `sw.js` | Rarely | Bump cache version after asset changes |
| `pokemonData.js` | Never | Generated file — use `concat_pokemon_data.py` |
| `ARCHITECTURE.md` | Update | Keep in sync with structural changes |
| `MIGRATION.md` | Update | Track migration progress |

## Testing

No test framework — verify manually:
```bash
python3 -m http.server 8000
# Open http://localhost:8000/index.html
# Check: cards load, favorites persist, offline mode works
```
