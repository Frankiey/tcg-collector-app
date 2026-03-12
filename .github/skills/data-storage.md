---
description: "Use when working with IndexedDB, localStorage, data persistence, caching, or the storage fallback chain."
---

# Data & Storage Skill

You are working with the data persistence layer of the Pokemon TCG Collector App.

## Storage Architecture

```
IndexedDB (primary)
    ├── cards store        → API response cache (24h TTL)
    ├── settings store     → App configuration
    └── userData store     → Favorites, notes, collections, purchases
        │
        ▼ (fallback if IndexedDB unavailable)
localStorage
    ├── tcg_favorites      → JSON string
    ├── tcg_notes          → JSON string
    ├── tcg_collections    → JSON string
    └── tcg_bought         → JSON string
        │
        ▼ (offline fallback for card data)
pokemonData.js             → Static generated data blob
```

## DBService (in index.html)

The `DBService` object handles all storage:

- `init()` — Opens IndexedDB connection, sets up stores
- `getCards(query)` — Check cache, return if fresh (<24h)
- `setCards(query, data)` — Cache API response with timestamp
- `getUserData()` — Load favorites, notes, collections, purchases
- `saveUserData(key, value)` — Persist user data
- Connection pooling and retry logic for reliability

## Rules

- **Never skip the fallback chain** — Always support IndexedDB → localStorage → pokemonData.js
- **Cache TTL is 24 hours** — Don't change without updating the cache invalidation logic
- **Auto-migration** — On first load, localStorage data migrates to IndexedDB. Don't break this path.
- **Schema changes need migration** — If you change the IndexedDB store structure, write migration logic in `DBService.init()`
- **Keep pokemonData.js generated** — Never edit by hand. Use `concat_pokemon_data.py`.

## Data shapes

### User data (persisted)
```js
boughtCards: { "cardId": { date: "2024-01-15", price: 12.50 } }
favoriteCards: { "cardId": true }
cardNotes: { "cardId": "My notes about this card" }
customCollections: [{ id: "uuid", name: "Holos", description: "...", cards: ["cardId1", "cardId2"] }]
```

### Cached card data
```js
{
  query: "name:pikachu",
  timestamp: 1710000000000,
  data: [ /* array of card objects from API */ ]
}
```
