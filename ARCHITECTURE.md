# Architecture

> Living document describing the system architecture of the Pokémon TCG Collector App.
> Update this when making structural changes.
>
> **Last updated:** 2026-03-16 — migrated from v2/ to root. TCGDex API is now live.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (PWA)                        │
│                                                             │
│  ┌────────────────┐   ┌────────────┐   ┌────────────────┐   │
│  │  index.html    │   │ styles.css │   │ Service Worker │   │
│  │  (templates +  │   │            │   │   (sw.js)      │   │
│  │   Vue mount)   │   └────────────┘   └───────┬────────┘   │
│  └───────┬────────┘                            │            │
│          │                                     │            │
│  ┌───────┴──────────────────────────────┐      │            │
│  │          JS Modules (js/)            │      │            │
│  │  app.js · config.js · api.js         │      │            │
│  │  db.js  · utils.js  · components.js  │      │            │
│  └───────┬──────────────────────────────┘      │            │
│          │                                     │            │
│  ┌───────┴─────────────────────────────────────┴─────────┐  │
│  │                  Storage Layer                        │  │
│  │  IndexedDB (primary) → localStorage (fallback)       │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │    TCGDex API (v2)      │
          │                         │
          │  GraphQL — card lists   │
          │  REST    — pricing      │
          │  CDN     — card images  │
          └─────────────────────────┘
```

## File Map

### Application Files

| File | Lines | Purpose |
|------|-------|---------|
| `index.html` | ~560 | HTML shell: Vue 3 templates + component `<template>` blocks |
| `styles.css` | ~1580 | All CSS: variables, glassmorphism, responsive, components |
| `sw.js` | ~64 | Service Worker: precaching, offline-first fetch strategy |
| `js/app.js` | ~615 | Vue 3 app entry point — state, methods, lifecycle |
| `js/config.js` | ~90 | Central CONFIG object — API URLs, defaults, mappings |
| `js/api.js` | ~190 | ApiService — TCGDex GraphQL + REST, `mapCard()` normalizer |
| `js/db.js` | ~340 | DBService — IndexedDB wrapper with retry + localStorage fallback |
| `js/utils.js` | ~190 | Utilities, LazyLoadService, NotificationService, OfflineService |
| `js/components.js` | ~235 | Vue 3 component definitions (Card, Modal, Notification, ImportDialog) |

### Data & Tooling

| File | Purpose |
|------|---------|
| `pokemonData.js` | Generated offline data blob (~122K lines) — used as fallback |
| `/data/*.json` | Per-Pokemon JSON files from scraper |
| `/images/` | Locally cached card images |

### Python Scripts

| Script | Purpose |
|--------|---------|
| `pokemon_scraper.py` | Scrape a single Pokemon's cards from Cardmarket |
| `batch_scraper.py` | Batch-run scraper for multiple Pokemon |
| `concat_pokemon_data.py` | Merge `/data/*.json` → `pokemonData.js` |
| `download_pokemon_images.py` | Download card images to `/images/` |
| `fix_missing_images.py` | Re-download failed/missing images |

### Documentation

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | This file — system design overview |
| `MIGRATION.md` | API migration plan and decision log |
| `WORKNOTES.md` | Session-by-session decision rationale |
| `SCRATCHPAD.md` | Raw analysis and API test results |
| `README.md` | Project overview and quick-start |

---

## Module Architecture

The app is split into ES modules loaded via `<script type="module">`:

```
index.html
  └─ js/app.js (entry point)
       ├─ js/config.js    — CONFIG object (API URLs, defaults, mappings)
       ├─ js/db.js         — DBService (IndexedDB + localStorage)
       ├─ js/api.js        — ApiService (TCGDex GraphQL + REST)
       ├─ js/utils.js      — utils, LazyLoadService, NotificationService, OfflineService
       └─ js/components.js — CardComponent, ModalComponent, NotificationComponent, ImportDialogComponent
```

Vue 3 is loaded via CDN as a global (`window.Vue`). All JS modules use native ES `import`/`export`.
Templates remain in `index.html` as `<template id="...">` blocks — components reference them by ID.

---

## Core Services

### ApiService (`js/api.js`)
Two-stage fetch strategy:
1. **Stage 1 — GraphQL** (on tab select): Fetches card list with HP, types, rarity, set info. No pricing.
2. **Stage 2 — REST** (on modal open): Lazy-loads pricing for individual cards.
- `mapCard()` normalizes TCGDex responses to internal card schema
- Set details (releaseDate) enriched via parallel REST calls
- TCG Pocket cards excluded by series ID

### DBService (`js/db.js`)
- IndexedDB wrapper with connection pooling and retry logic (3 attempts)
- Stores: `cards` (API cache, 24h TTL), `settings`, `userData`
- Automatic fallback to `localStorage` if IndexedDB unavailable
- Migration path: localStorage → IndexedDB on first load
- Export/import of full collection data as JSON

### LazyLoadService (`js/utils.js`)
- Uses `IntersectionObserver` for image lazy loading
- Cards load images only when scrolled into viewport
- Reduces initial bandwidth and improves perceived performance

### OfflineService (`js/utils.js`)
- Monitors `navigator.onLine` + `online`/`offline` events
- Toggles UI indicators when connectivity changes
- Toast notifications for online/offline transitions

### NotificationService (`js/utils.js`)
- Toast notification controller with configurable duration
- Supports info, success, error, warning types

### utils (`js/utils.js`)
- `debounce()` — 300ms search debounce
- `formatPrice()` — USD price formatting
- `getReleaseYear()` — extract year from release date
- `getPriceValue()` — TCGPlayer price extraction
- `getTypeIcon()` — Pokemon type → Font Awesome icon
- `downloadObjectAsJson()` — browser file download
- `getCardPrice()` — best available price for filtering
- `toPlainObject()` — Vue reactive → plain object for storage

---

## Vue App Architecture

### Component Structure
Templates live in `index.html`; component logic in `js/components.js`:

| Component | Template ID | Purpose |
|-----------|-------------|---------|
| `card-component` | `#card-template` | Card tile in the grid |
| `modal-component` | `#modal-template` | Card detail overlay with pricing |
| `notification-component` | `#notification-template` | Toast notifications |
| `import-dialog-component` | `#import-dialog-template` | JSON file import dialog |

### State Management
No Vuex/Pinia — state lives on the root Vue instance (`js/app.js`):

| State | Type | Persisted | Description |
|-------|------|-----------|-------------|
| `allCards` | `Array` | IndexedDB cache | Currently displayed card list |
| `boughtCards` | `Object` | IndexedDB | `{ cardId: boolean }` purchase tracking |
| `favoriteCards` | `Object` | IndexedDB | `{ cardId: cardObject }` favorited cards |
| `cardNotes` | `Object` | IndexedDB | `{ cardId: string }` user notes |
| `customCollections` | `Array` | IndexedDB | User-created collection objects |
| `collectionCards` | `Object` | IndexedDB | `{ collectionId: cardId[] }` |
| `customTabs` | `Array` | IndexedDB | User-added Pokemon name tabs |
| `currentView` | `String` | No | Active view (all/favorites/custom/add) |
| `currentCollection` | `String` | No | Active Pokemon tab |

### Views
1. **All Cards** — Browse by Pokemon species, with search, filters, and sort
2. **Favorites** — Starred cards across all collections
3. **Custom Collections** — User-curated groups (manual or auto-filtered)
4. **Add Pokemon** — Add new Pokemon species tabs

---

## Data Flow

### Card Loading (Stage 1)

```
User selects Pokemon tab
        │
        ▼
  ┌─────────────┐     ┌──────────────┐
  │ Check cache  │────▶│ Return cached │ (IndexedDB, <24h old)
  │ (IndexedDB)  │     │ results      │
  └──────┬───────┘     └──────────────┘
         │ cache miss / expired
         ▼
  ┌──────────────┐     ┌──────────────┐
  │ GraphQL POST │────▶│ mapCard() +  │
  │ to TCGDex    │     │ cache in IDB │
  └──────┬───────┘     └──────────────┘
         │ offline / error
         ▼
  ┌──────────────┐
  │ Serve stale  │
  │ cache (IDB)  │
  └──────────────┘
```

### Pricing (Stage 2)

```
User opens card modal
        │
        ▼
  ┌─────────────────┐
  │ pricing.loaded?  │──── yes ──▶ Show cached pricing
  └───────┬──────────┘
          │ no
          ▼
  ┌──────────────────┐
  │ REST GET /cards/  │
  │ {id} from TCGDex  │
  └───────┬──────────┘
          ▼
  ┌──────────────────┐
  │ Merge pricing    │
  │ into allCards[]  │
  └──────────────────┘
```

---

## API: TCGDex v2

| Property | Value |
|----------|-------|
| Base URL (REST) | `https://api.tcgdex.net/v2/en` |
| Base URL (GraphQL) | `https://api.tcgdex.net/v2/graphql` |
| Image CDN | `https://assets.tcgdex.net/en/{series}/{set}/{localId}/{quality}.webp` |
| Auth | **None** — fully open |
| Rate limit | Not publicly documented; handles 10M+ req/month |
| Pricing | Built-in Cardmarket + TCGPlayer (REST only) |

### GraphQL Query (Stage 1)
```graphql
{
  cards(
    filters: { name: "Charizard" }
    pagination: { page: 1, itemsPerPage: 250 }
  ) {
    id name image localId rarity hp types stage
    set { id name }
    variants { holo firstEdition }
  }
}
```

### Internal Card Schema
All components and templates read from this normalized shape:

```json
{
  "id": "base1-4",
  "name": "Charizard",
  "hp": "120",
  "types": ["Fire"],
  "rarity": "Rare Holo",
  "number": "4",
  "set": { "id": "base1", "name": "Base Set", "releaseDate": "1999-01-09" },
  "images": {
    "small": "https://assets.tcgdex.net/en/base/base1/4/low.webp",
    "large": "https://assets.tcgdex.net/en/base/base1/4/high.webp"
  },
  "variants": { "holo": true, "firstEdition": false },
  "pricing": { "loaded": false, "tcgplayer": null, "cardmarket": null }
}
```

---

## Offline Strategy

1. **Service Worker** (`sw.js`) precaches HTML, CSS, and all JS modules
2. **IndexedDB** caches API responses per collection with 24h TTL
3. **Stale cache** served when offline (no TTL check)
4. **OfflineService** detects connectivity and adjusts UI with toast notifications

---

## Storage Strategy

| Store | Key Path | Purpose |
|-------|----------|---------|
| `cards` | `id` | API response cache, indexed by `collection` and `lastUpdated` |
| `settings` | `key` | Cache metadata per collection (timestamp, count) |
| `userData` | `key` | All user data: bought, favorites, notes, tabs, collections |

Fallback chain: IndexedDB → localStorage (auto-migrated on first load)

---

## Known Technical Debt

- No automated tests — manual testing only
- CSS has some inline styles in HTML templates
- `pokemonData.js` is 122K lines (generated, not minified) — may be retired
- Python scrapers may be retired now that TCGDex has built-in Cardmarket pricing
- Custom collections view/edit not fully implemented (placeholder notifications)
