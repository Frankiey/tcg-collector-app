# Architecture

> Living document describing the system architecture of the Pokemon TCG Collector App.
> Update this when making structural changes.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Browser (PWA)                      │
│                                                         │
│  ┌──────────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │   Vue 3 App  │  │ styles   │  │  Service Worker   │  │
│  │ (index.html) │  │ (.css)   │  │     (sw.js)       │  │
│  └──────┬───────┘  └──────────┘  └────────┬──────────┘  │
│         │                                  │             │
│  ┌──────┴──────────────────────────────────┴──────────┐  │
│  │              Core Services Layer                   │  │
│  │  DBService · LazyLoad · Offline · Utils            │  │
│  └──────┬─────────────────────────────────────────────┘  │
│         │                                                │
│  ┌──────┴──────────────────────────────────────────────┐ │
│  │              Storage Layer                          │ │
│  │  IndexedDB (primary) → localStorage (fallback)     │ │
│  └─────────────────────────────────────────────────────┘ │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │    External APIs        │
        │                         │
        │  Pokemon TCG API        │
        │  (api.pokemontcg.io)    │
        │                         │
        │  Cardmarket.com         │
        │  (scraped via Python)   │
        └─────────────────────────┘
```

## File Map

| File | Lines | Purpose |
|------|-------|---------|
| `index.html` | ~2050 | Main app: Vue 3 SPA with all templates, components, and logic |
| `index2.html` | ~2100 | Experimental/dev version (feature branch equivalent) |
| `styles.css` | ~1570 | All CSS: variables, glassmorphism, responsive, components |
| `sw.js` | ~64 | Service Worker: precaching, offline-first fetch strategy |
| `pokemonData.js` | ~122K | Generated offline data blob (all Pokemon card data) |

### Python Tooling

| Script | Purpose |
|--------|---------|
| `pokemon_scraper.py` | Scrape a single Pokemon's cards from Cardmarket |
| `batch_scraper.py` | Batch-run scraper for multiple Pokemon |
| `concat_pokemon_data.py` | Merge `/data/*.json` → `pokemonData.js` |
| `download_pokemon_images.py` | Download card images to `/images/` |
| `fix_missing_images.py` | Re-download failed/missing images |

## Core Services

### DBService
- IndexedDB wrapper with connection pooling and retry logic
- Stores: `cards` (API cache, 24h TTL), `settings`, `userData`
- Automatic fallback to `localStorage` if IndexedDB unavailable
- Migration path: localStorage → IndexedDB on first load

### LazyLoadService
- Uses `IntersectionObserver` for image lazy loading
- Cards load images only when scrolled into viewport
- Reduces initial bandwidth and improves perceived performance

### OfflineService
- Monitors `navigator.onLine` + `online`/`offline` events
- Toggles UI indicators when connectivity changes
- Falls back to `pokemonData.js` when API is unreachable

### Utils
- `debounce()` — 300ms search debounce
- Price formatting (EUR/USD)
- Pokemon type → icon mapping
- JSON export/import for user data

## Vue App Architecture

### Component Structure
All components are defined inline in `index.html` using Vue 3's `template` option with template IDs:

- **card-component** (`#card-template`) — Individual card display
- **modal-component** (`#modal-template`) — Card detail overlay
- **App root** — All views, tabs, state management

### State Management
No Vuex/Pinia — state lives on the root Vue instance:

| State | Type | Persisted | Description |
|-------|------|-----------|-------------|
| `allCards` | `Array` | Cache | Currently displayed cards |
| `boughtCards` | `Object` | IndexedDB | Card ID → purchase data |
| `favoriteCards` | `Object` | IndexedDB | Card ID → boolean |
| `cardNotes` | `Object` | IndexedDB | Card ID → note text |
| `customCollections` | `Array` | IndexedDB | User-created collections |
| `currentView` | `String` | No | Active view tab |
| `currentCollection` | `String` | No | Active Pokemon/filter |

### Views
1. **All Cards** — Browse by Pokemon species, with filters and search
2. **Favorites** — Starred cards
3. **Custom Collections** — User-curated groups (manual or auto-filtered)
4. **Add Pokemon** — Add new Pokemon species tabs

## Data Flow

```
User selects Pokemon tab
        │
        ▼
  ┌─────────────┐     ┌──────────────┐
  │ Check cache  │────▶│ Return cached │ (if <24h old)
  │ (IndexedDB)  │     │ results      │
  └──────┬───────┘     └──────────────┘
         │ cache miss
         ▼
  ┌──────────────┐     ┌──────────────┐
  │ Fetch from   │────▶│ Cache result  │
  │ TCG API      │     │ in IndexedDB  │
  └──────┬───────┘     └──────────────┘
         │ offline/error
         ▼
  ┌──────────────┐
  │ Fall back to │
  │ pokemonData  │
  └──────────────┘
```

## API Dependencies

### Pokemon TCG API (current)
- **Base URL**: `https://api.pokemontcg.io/v2`
- **Auth**: API key in request header (`X-Api-Key`)
- **Rate limits**: 1000 req/day (free), 30K/day (paid)
- **Used endpoints**: `GET /cards?q=name:{pokemon}`
- **Response format**: JSON with `data[]` array of card objects

### Cardmarket (scraped)
- Web scraping via Selenium + BeautifulSoup
- Provides pricing data not available in TCG API
- Results stored as JSON in `/data/` directory

## Offline Strategy

1. **Service Worker** precaches core assets (HTML, CSS, JS)
2. **IndexedDB** caches API responses with 24h TTL
3. **pokemonData.js** serves as ultimate offline fallback
4. **OfflineService** detects connectivity and adjusts UI

## Known Technical Debt

- All app logic lives in a single `index.html` (~2050 lines)
- No build step, bundler, or module system
- `index2.html` duplicates most of `index.html` (no shared code)
- No automated tests
- CSS has some inline styles in HTML templates
- `pokemonData.js` is 122K lines (generated, not minified)

---

## Planned: API Migration

> **Status**: Planning phase
>
> The app is preparing for a major migration to a new API.
> See [MIGRATION.md](MIGRATION.md) for the migration plan and checklist.

Key areas affected by an API migration:
1. **API client layer** — URL, auth, request format
2. **Response mapping** — Card object shape, field names, image URLs
3. **IndexedDB schema** — Cached card structure may change
4. **pokemonData.js** — Regeneration with new data shape
5. **Python scrapers** — May need new selectors/endpoints
6. **Service Worker** — Cache versioning bump required
