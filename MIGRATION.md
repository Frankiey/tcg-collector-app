# API Migration Plan

> Status: **Planning** | Last updated: 2026-03-12

## Overview

The Pokemon TCG Collector App currently relies on the [Pokemon TCG API](https://pokemontcg.io/) (v2) for card data. This document tracks the migration to a new API.

## Current API: Pokemon TCG API v2

- **Base URL**: `https://api.pokemontcg.io/v2`
- **Auth**: API key via `X-Api-Key` header
- **Rate limits**: 1,000 req/day (free tier), 30,000/day (paid)
- **Docs**: https://docs.pokemontcg.io/

### Endpoints Used

| Endpoint | Usage |
|----------|-------|
| `GET /cards?q=name:{pokemon}` | Fetch cards by Pokemon name |
| `GET /cards/{id}` | Fetch single card detail |

### Response Shape (current)

```json
{
  "data": [
    {
      "id": "base1-4",
      "name": "Charizard",
      "supertype": "Pokémon",
      "subtypes": ["Stage 2"],
      "hp": "120",
      "types": ["Fire"],
      "set": { "id": "base1", "name": "Base", "series": "Base" },
      "number": "4",
      "rarity": "Rare Holo",
      "images": {
        "small": "https://images.pokemontcg.io/base1/4.png",
        "large": "https://images.pokemontcg.io/base1/4_hires.png"
      },
      "tcgplayer": {
        "url": "https://...",
        "prices": { "holofoil": { "market": 350.00 } }
      },
      "cardmarket": {
        "url": "https://...",
        "prices": { "averageSellPrice": 280.00 }
      }
    }
  ],
  "page": 1,
  "pageSize": 250,
  "count": 42,
  "totalCount": 42
}
```

---

## Migration Phases

### Phase 1: Abstraction Layer ⬜
> Isolate all API calls behind a clean interface so the new API can be swapped in

- [ ] Extract API calls into a dedicated `ApiService` object in `index.html`
- [ ] Define a `mapCardResponse(rawCard)` function that normalizes API responses
- [ ] Create an internal card schema that both old and new APIs map to
- [ ] Ensure all components read from the internal schema, not raw API fields
- [ ] Write defensive field access (optional chaining) for price/image fields

### Phase 2: New API Integration ⬜
> Implement the new API client alongside the old one

- [ ] Document new API's base URL, auth, rate limits, and response format
- [ ] Implement `ApiService.fetchCardsNew()` using new API
- [ ] Write `mapCardResponseNew(rawCard)` for the new API's response shape
- [ ] Add a `CONFIG.useNewApi` feature flag to toggle between APIs
- [ ] Test both API paths side by side

### Phase 3: Data Migration ⬜
> Handle cached data and offline fallback data

- [ ] Write IndexedDB migration logic for cached cards with new schema
- [ ] Update `concat_pokemon_data.py` to output the new card shape
- [ ] Regenerate `pokemonData.js` with new format
- [ ] Update Python scrapers if the data source changes
- [ ] Handle mixed old/new format data in IndexedDB gracefully

### Phase 4: Cutover & Cleanup ⬜
> Switch fully to the new API and remove old code

- [ ] Set `CONFIG.useNewApi = true` as default
- [ ] Remove old API client code and mapping functions
- [ ] Bump `CACHE_NAME` in `sw.js` to invalidate old caches
- [ ] Clear old IndexedDB cached data on version upgrade
- [ ] Update all documentation (ARCHITECTURE.md, CLAUDE.md, skills)
- [ ] Test offline fallback chain end-to-end
- [ ] Remove feature flag

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| New API has different rate limits | Medium | High | Check limits early; implement request batching |
| Card IDs differ between APIs | High | High | Build ID mapping; migrate user data (favorites, notes) |
| Missing price data in new API | Medium | Medium | Keep Cardmarket scraping as supplement |
| IndexedDB cache has old-format data | Certain | Medium | Version check + migration in DBService.init() |
| Offline users have stale pokemonData.js | Low | Low | SW cache bump forces re-download |

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-12 | Created migration plan | Need structured approach for API swap |
| | | |

---

## Notes

- The current `CONFIG` object in `index.html` holds the API base URL and key
- All API-touching code is in the Vue app methods section of `index.html`
- The Python scraping pipeline is independent and can migrate separately
- User data (favorites, notes, collections) currently references card IDs — if IDs change, user data needs migration too
