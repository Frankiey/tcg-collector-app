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
| `index.html` | 🚧 In progress | Copy of root index.html + TCGDex API layer |
| `styles.css` | ✅ Shared | Symlink or copy from root — no CSS changes expected |
| `sw.js` | 🚧 In progress | CACHE_NAME bumped to `pokemon-tcgdex-v1` |
| `pokemonData.js` | ⬜ Pending | Will be regenerated with new schema in Phase 4 |
