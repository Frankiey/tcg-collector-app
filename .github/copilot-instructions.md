# Copilot Instructions for Pokémon TCG Collector App

## Project Context

This is a **no-build-step** Vue 3 PWA with **modular ES modules**. Everything runs from static files loaded via CDN. There is no npm, no bundler, no `.vue` files. JavaScript is split across `js/*.js` modules using native `import`/`export`.

## Critical Constraints

1. **No build step** — Never introduce webpack, vite, rollup, or any bundler
2. **No package manager** — No npm, yarn, pnpm. Dependencies come from CDNs
3. **ES modules** — The app uses `<script type="module">` and `import`/`export` in `js/*.js`
4. **Modular architecture** — Logic split across `js/` modules, NOT a single-file app
5. **Offline-first** — Service Worker + IndexedDB + pokemonData.js fallback chain
6. **TCGDex API** — GraphQL for card lists, REST for pricing (lazy on modal open)

## Code Style

- **JavaScript**: ES6+, no TypeScript, 2-space indent, ES module imports
- **CSS**: BEM-ish naming, CSS custom properties for theming, glassmorphism aesthetic
- **HTML**: Vue 3 template syntax with `v-once` on static content
- **Python**: PEP 8, 4-space indent, used only for data generation scripts

## When Making Changes

### Before editing
- Read `ARCHITECTURE.md` for system design context and module dependency tree
- Read `MIGRATION.md` before touching any API-related code
- Understand the storage fallback chain: IndexedDB → localStorage → pokemonData.js

### When editing `index.html`
- This is the HTML shell (~560 lines) — templates and mount point only
- Components use template IDs: `template: '#card-template'`
- App logic lives in `js/app.js`, NOT in index.html
- State lives on root Vue instance (no Vuex/Pinia)

### When editing `js/*.js` modules
- `config.js` — Centralized CONFIG object, API URLs, DB version
- `api.js` — All API calls go here (TCGDex GraphQL + REST)
- `db.js` — IndexedDB wrapper, never access IndexedDB directly elsewhere
- `utils.js` — Shared utilities, LazyLoad, Notification, Offline services
- `components.js` — Vue component definitions
- `app.js` — Vue app entry point, state, methods, lifecycle

### When editing `styles.css`
- Use existing CSS variables from `:root` — don't hardcode colors
- Follow the existing section structure (see Table of Contents comment at top)
- Mobile-first responsive design

### When editing `sw.js`
- Bump `CACHE_NAME` version when changing any cached asset
- Keep the precache list up to date — it includes all `js/*.js` modules

### When editing Python scripts
- These generate data files — never edit `pokemonData.js` by hand
- Pipeline: scrape → `/data/*.json` → `concat_pokemon_data.py` → `pokemonData.js`

## File Roles

| File | Edit? | Notes |
|------|-------|-------|
| `index.html` | Yes | HTML shell and templates (~560 lines) |
| `js/app.js` | Yes | Vue app entry — state, methods, lifecycle |
| `js/config.js` | Yes | CONFIG object — API URLs, settings |
| `js/api.js` | Yes | ApiService — keep all API calls here |
| `js/db.js` | Yes | DBService — IndexedDB wrapper |
| `js/utils.js` | Yes | Utilities and services |
| `js/components.js` | Yes | Vue component definitions |
| `styles.css` | Yes | All styles — follow CSS variable conventions |
| `sw.js` | Rarely | Bump cache version after asset changes |
| `pokemonData.js` | Never | Generated file — use `concat_pokemon_data.py` |
| `ARCHITECTURE.md` | Update | Keep in sync with structural changes |
| `MIGRATION.md` | Update | Track migration decisions |

## Testing

No test framework — verify manually:
```bash
python3 -m http.server 8000
# Open http://localhost:8000
# Check: cards load, favorites persist, offline mode works
```
