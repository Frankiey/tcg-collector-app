---
description: "Use when working on the API client layer, response mapping, or anything related to the API migration. Reads MIGRATION.md for current migration status."
---

# API Migration Skill

You are helping with a major API migration for the Pokemon TCG Collector App.

## Before making any changes

1. Read `MIGRATION.md` to understand the current migration status and plan
2. Read `ARCHITECTURE.md` to understand how the API layer fits into the app
3. Identify which phase of the migration applies to the requested change

## Key principles

- **Never break the offline fallback chain**: IndexedDB → localStorage → pokemonData.js
- **Keep API calls behind the CONFIG interface** so they can be swapped cleanly
- **Separate response mapping from rendering** — map API responses to an internal card shape
- **Preserve backward compatibility** with cached IndexedDB data during transition
- **Bump the Service Worker cache version** (`CACHE_NAME` in `sw.js`) after any change to cached assets

## Where API code lives

All API calls are in `index.html` within the Vue app's methods:
- Card fetching: search for `fetch(` calls using the `CONFIG` base URL
- Response mapping: look for where API response `data[]` is transformed
- Caching: `DBService` stores/retrieves cached results in IndexedDB

## Internal card shape (current)

The current API (api.pokemontcg.io/v2) returns cards with this structure. When migrating, map the new API's response to match this shape to minimize UI changes:

```js
{
  id: "base1-4",
  name: "Charizard",
  supertype: "Pokémon",
  subtypes: ["Stage 2"],
  hp: "120",
  types: ["Fire"],
  set: { name: "Base", series: "Base" },
  number: "4",
  rarity: "Rare Holo",
  images: { small: "https://...", large: "https://..." },
  tcgplayer: { prices: { holofoil: { market: 350.00 } } },
  cardmarket: { prices: { averageSellPrice: 280.00 } }
}
```

## Migration checklist pattern

When completing a migration task:
1. Implement the change
2. Update `MIGRATION.md` to reflect progress
3. Update `ARCHITECTURE.md` if the system structure changed
4. Note any backward-compatibility concerns
