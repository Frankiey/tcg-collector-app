# v2 — TCGDex Migration

> This folder is the active development workspace for the API migration from
> [pokemontcg.io](https://pokemontcg.io) to [TCGDex](https://tcgdex.dev).
>
> The root `index.html` is the live production version and remains untouched.
> Work here; compare side-by-side; promote when ready.

## Running v2

```bash
# From project root
python3 -m http.server 8000
# Visit http://localhost:8000/v2/
```

## What's Different Here

| Area | Change |
|------|--------|
| API | TCGDex (no auth, open source) |
| Fetch strategy | GraphQL for card list + lazy REST for pricing |
| Image URLs | `assets.tcgdex.net` CDN + `/low.webp` / `/high.webp` |
| Pricing | Built-in Cardmarket + TCGPlayer (no Python scraper needed) |
| Card IDs | **Same** — user data (favorites, notes, bought) is portable |
| IndexedDB | DB version bumped; cards store cleared on upgrade |
| SW cache | `pokemon-tcgdex-v1` (new name to force re-cache) |

## Migration Status

See [`../MIGRATION.md`](../MIGRATION.md) for the full plan, field mapping, and phase checklist.

## File Map

| File | Status | Notes |
|------|--------|-------|
| `index.html` | ✅ Done | Thin HTML + Vue templates only (~556 lines) |
| `styles.css` | ✅ Done | Copied from root — self-contained |
| `sw.js` | ✅ Done | CACHE_NAME bumped to `pokemon-tcgdex-v2`, precaches JS modules |
| `js/config.js` | ✅ Done | Central CONFIG object (API URLs, defaults, mappings) |
| `js/db.js` | ✅ Done | DBService — IndexedDB wrapper with retry + fallback |
| `js/api.js` | ✅ Done | ApiService — TCGDex GraphQL + REST, mapCard() |
| `js/utils.js` | ✅ Done | Utilities, LazyLoadService, NotificationService, OfflineService |
| `js/components.js` | ✅ Done | Vue 3 component definitions (Card, Modal, Notification, ImportDialog) |
| `js/app.js` | ✅ Done | Vue 3 app entry point — state, methods, mount |
