# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pokémon TCG Collector App — A Vue 3 PWA for browsing, collecting, and tracking Pokémon TCG cards. Users can browse cards by Pokémon, track purchases, add favorites, take notes, and manage custom collections.

**Status**: TCGDex migration complete. See `MIGRATION.md` for the decision log.

## Technology Stack

- **Frontend**: Vue 3 (via CDN, no build step), ES modules, CSS3 with glassmorphism
- **API**: TCGDex (`api.tcgdex.net/v2`) — GraphQL for card lists, REST for pricing
- **Storage**: IndexedDB (primary), localStorage (fallback)
- **Offline**: Service Worker (`sw.js`) for PWA caching
- **Docs**: `ARCHITECTURE.md` (system design), `MIGRATION.md` (migration decisions)

## Development

**No build step required** — Static site with ES modules.

```bash
python3 -m http.server 8000
# Visit http://localhost:8000
```

## Architecture

See `ARCHITECTURE.md` for the full system architecture, data flow diagrams, and module dependency tree.

### Key Files

| File | Purpose |
|------|---------|
| `index.html` | HTML shell with Vue templates (~560 lines) |
| `styles.css` | All CSS — variables, glassmorphism, responsive (~1580 lines) |
| `sw.js` | Service Worker — precaches all JS modules |
| `js/app.js` | Vue 3 app entry — state, computed, methods, lifecycle (~615 lines) |
| `js/config.js` | CONFIG object — API URLs, DB version, defaults (~90 lines) |
| `js/api.js` | ApiService — TCGDex GraphQL + REST (~190 lines) |
| `js/db.js` | DBService — IndexedDB with retry logic (~340 lines) |
| `js/utils.js` | Utilities, LazyLoad, Notification, Offline services (~190 lines) |
| `js/components.js` | Vue components — Card, Modal, Notification, ImportDialog (~235 lines) |

### Module Dependencies

```
app.js
├── config.js      (CONFIG)
├── api.js          (ApiService) ← uses CONFIG
├── db.js           (DBService) ← uses CONFIG
├── utils.js        (utils, LazyLoadService, NotificationService, OfflineService)
└── components.js   (Card, Modal, Notification, ImportDialog)
```

### Data Flow

1. `app.js` imports all modules, creates Vue 3 app
2. On mount: DBService opens IndexedDB, loads user data (favorites, notes, collections)
3. Tab select → `ApiService.fetchCards()` fires GraphQL query to TCGDex
4. Results mapped via `mapCard()` to internal schema, cached in IndexedDB (24h TTL)
5. Modal open → `ApiService.fetchCardDetail(id)` fires REST call for pricing (lazy)
6. Offline: stale IndexedDB cache served if present, error shown otherwise

### Vue App State

| State | Type | Persisted | Description |
|-------|------|-----------|-------------|
| `allCards` | Array | Cache | Currently displayed cards |
| `boughtCards` | Object | IndexedDB | Purchase tracking by card ID |
| `favoriteCards` | Object | IndexedDB | Favorited cards |
| `cardNotes` | Object | IndexedDB | User notes per card |
| `customCollections` | Array | IndexedDB | User-created collections |

## Code Patterns & Conventions

- **No build step** — Static files via CDN, ES modules with `<script type="module">`
- **Modular architecture** — Logic split across `js/*.js` modules (not single-file)
- **Configuration-driven** — Centralized `CONFIG` object in `js/config.js`
- **Template IDs** — Vue components use `template: '#card-template'` registration
- **Two-stage fetch** — GraphQL for lists, lazy REST for pricing on modal open
- **Debounced inputs** — Search uses 300ms debounce
- **Graceful degradation** — IndexedDB → localStorage fallback chain
- **CSS variables** — All theming via `:root` custom properties in `styles.css`
- **`v-once`** — Used on static content to reduce Vue reactivity overhead

## Rules for AI Agents

### DO
- Read `ARCHITECTURE.md` before making structural changes
- Read `MIGRATION.md` before touching API-related code
- Preserve the offline-first architecture (SW + IndexedDB cache)
- Keep the no-build-step constraint — no bundlers, no npm, no node_modules
- Use Vue 3 CDN patterns (no SFC, no `.vue` files)
- Use ES module `import`/`export` in `js/*.js` files
- Test changes with `python3 -m http.server 8000`
- Update `ARCHITECTURE.md` when you change the system structure
- Bump `CACHE_NAME` version in `sw.js` after changing cached assets
- Update the SW precache list when adding new JS modules

### DON'T
- Don't introduce a build step or package manager without explicit approval
- Don't merge JS modules back into `index.html` — keep modular structure
- Don't remove the localStorage fallback — some users may have old browsers
- Don't change the IndexedDB schema without a migration plan
- Don't add API calls outside `js/api.js` — keep API layer centralized
