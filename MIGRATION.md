# API Migration Plan — pokemontcg.io → TCGDex

> Status: **Complete** | Last updated: 2026-03-16
> See `WORKNOTES.md` for the decision log and `SCRATCHPAD.md` for working analysis.
>
> The v2 migration was promoted to root on 2026-03-16. The app now uses TCGDex as its
> sole API provider. The old pokemontcg.io integration and `v2/` folder have been removed.

---

## Overview

The Pokémon TCG Collector App has been migrated from [pokemontcg.io](https://pokemontcg.io/) (v2)
to [TCGDex](https://tcgdex.dev) — an open-source, no-auth alternative with built-in
Cardmarket + TCGPlayer pricing, richer card metadata, and no rate-limit concerns.

The migration was developed in a `v2/` folder for side-by-side comparison, then promoted
to root when ready.

---

## API Comparison

### Current: Pokemon TCG API v2

| Property | Value |
|----------|-------|
| Base URL | `https://api.pokemontcg.io/v2` |
| Auth | `X-Api-Key` header required |
| Rate limit | 1,000 req/day (free), 30,000 (paid) |
| Search | `GET /cards?q=name:{pokemon}` → full card objects |
| Single card | `GET /cards/{id}` |
| Pricing | TCGPlayer + Cardmarket (embedded in card response) |

### New: TCGDex API v2

| Property | Value |
|----------|-------|
| Base URL | `https://api.tcgdex.net/v2/en` |
| Auth | **None** — fully open |
| Rate limit | Not publicly documented; open-source |
| GraphQL | `POST https://api.tcgdex.net/v2/graphql` |
| Card list | `GET /cards?category=Pokemon&name={pokemon}` → **shallow** `[{id, localId, name, image}]` |
| Full card | `GET /cards/{id}` → full card with pricing |
| Pricing | `pricing.cardmarket` + `pricing.tcgplayer` (REST only, not in GraphQL) |
| Images | `https://assets.tcgdex.net/en/{series}/{setId}/{localId}` + `/high.webp` or `/low.webp` |

**Critical: TCGDex REST list returns shallow data only.** Getting full card data (HP, types, rarity,
variants, pricing) requires either GraphQL (no pricing) or individual `GET /cards/{id}` calls.

---

## Field Mapping

### Card Object

| Field in app | pokemontcg.io | TCGDex REST (`/cards/{id}`) |
|---|---|---|
| Card ID | `id` ("base1-4") | `id` ("base1-4") ✅ same |
| Name | `name` | `name` ✅ same |
| HP | `hp` (string "120") | `hp` (number 120) — `String()` to normalize |
| Types | `types[]` (["Fire"]) | `types[]` ✅ same |
| Set name | `set.name` | `set.name` ✅ same |
| Set ID | `set.id` | `set.id` ✅ same |
| Card number | `number` ("4") | `localId` ("4") — rename |
| Rarity | `rarity` ("Rare Holo") | `rarity` ("Rare Holo") ✅ same values |
| Category | `supertype` ("Pokémon") | `category` ("Pokemon") — minor rename |
| Stage/subtype | `subtypes[]` (["Stage 2"]) | `stage` ("Stage2") — array → string |
| Image small | `images.small` | `image + '/low.webp'` |
| Image large | `images.large` | `image + '/high.webp'` |
| Release year | `set.releaseDate` | **Not in card object** — must fetch set separately or drop |
| TCGPlayer price | `tcgplayer.prices.{type}.market` | `pricing.tcgplayer.{type}.marketPrice` (REST only) |
| TCGPlayer URL | `tcgplayer.url` | Not provided — construct from product ID |
| CM avg price | `cardmarket.prices.averageSellPrice` | `pricing.cardmarket.avg` (REST only) |
| CM trend price | `cardmarket.prices.trendPrice` | `pricing.cardmarket.trend` (REST only) |
| CM URL | `cardmarket.url` | Not provided — construct from `pricing.cardmarket.idProduct` |
| Foil variant | (in rarity name) | `variants.holo` boolean |
| 1st Edition | (in rarity name) | `variants.firstEdition` boolean |

### Response Wrapper

| | pokemontcg.io | TCGDex |
|---|---|---|
| List endpoint wrapper | `{ data: [...], page, pageSize, count }` | Flat `[...]` array |
| List item richness | Full card objects | Shallow `{id, localId, name, image}` only |
| Full card richness | Full with pricing | Full with pricing (REST `/cards/{id}`) |

---

## Fetch Strategy (Chosen Approach)

**Problem:** TCGDex list endpoints return shallow objects; pricing only exists on individual card REST calls.

**Chosen strategy: Two-stage GraphQL + lazy REST**

```
Stage 1 (on tab select):
  GraphQL → get all cards for a Pokemon
  Returns: id, name, image, localId, rarity, hp, types, stage, set{id,name}, variants{holo,firstEdition}
  → enough to render the card grid
  → cache in IndexedDB (no pricing yet)

Stage 2 (on modal open):
  REST GET /cards/{id}
  Returns: full card including pricing.cardmarket + pricing.tcgplayer
  → merge pricing into cached card
  → update IndexedDB entry
```

**GraphQL query used (Stage 1):**
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

**Rationale:** Avoids N+1 upfront requests (no burst of 50+ calls). Pricing is only needed
when a user opens a card detail modal, so lazy-loading it is acceptable UX.

---

## Internal Card Schema (v2 normalized shape)

Both APIs map to this internal shape so templates and utils only read from this:

```json
{
  "id": "base1-4",
  "name": "Charizard",
  "hp": "120",
  "types": ["Fire"],
  "rarity": "Rare Holo",
  "category": "Pokemon",
  "stage": "Stage2",
  "localId": "4",
  "number": "4",
  "set": {
    "id": "base1",
    "name": "Base Set",
    "releaseDate": null
  },
  "images": {
    "small": "https://assets.tcgdex.net/en/base/base1/4/low.webp",
    "large": "https://assets.tcgdex.net/en/base/base1/4/high.webp"
  },
  "variants": {
    "holo": true,
    "firstEdition": false
  },
  "pricing": {
    "loaded": false,
    "tcgplayer": null,
    "cardmarket": null
  }
}
```

> `images.small` / `images.large` kept intentionally — templates use these paths and will need
> zero template changes. The mapper constructs them from the TCGDex `image` base URL.
> `number` aliased from `localId` for same reason.

---

## Migration Phases

### Phase 0: Setup & Folder Structure ✅
> Create isolated v2/ workspace; no changes to production index.html

- [x] Create `v2/` folder with skeleton files
- [x] Copy `index.html` → `v2/index.html` as starting point
- [x] Copy `styles.css` → `v2/styles.css`
- [x] Copy `sw.js` → `v2/sw.js` (bump CACHE_NAME)
- [x] Create `v2/README.md` explaining this is the TCGDex migration branch

### Phase 1: Abstraction Layer ✅
> Isolate all API-touching code behind ApiService + mapCard()

- [x] Extract `CONFIG.API_BASE_URL` to point to TCGDex
- [x] Add `CONFIG.TCGDEX_GRAPHQL_URL` and `CONFIG.TCGDEX_REST_URL`
- [x] Create `mapCard(rawCard)` function that normalizes TCGDex response → internal schema
- [x] Rewrite `ApiService.fetchCards()` to use GraphQL
- [x] Add `ApiService.fetchCardDetail(id)` for lazy pricing load (REST)
- [x] Ensure all templates read `card.images.small`, `card.number` (aliased) — no template changes needed

### Phase 2: Template Audit ✅
> Verify templates work with mapped data; fix any field mismatches

- [x] Audit `card.images.small` usage → mapper produces this
- [x] Audit `card.number` usage → `localId` alias is set
- [x] Audit pricing paths → `card.pricing?.tcgplayer` / `card.pricing?.cardmarket`
- [x] Audit `utils.getCardPrice()` → works with new price paths
- [x] Audit `utils.getPriceValue()` → works with new price paths
- [x] Audit foil filter → uses both `card.rarity` and `card.variants.holo`
- [x] Audit `set.releaseDate` → enriched via separate set REST calls

### Phase 3: Lazy Pricing + UX ✅
> Implement Stage 2 pricing fetch on modal open

- [x] On `openModal(card)`: if `!card.pricing?.loaded`, call `ApiService.fetchCardDetail(card.id)`
- [x] Merge pricing into card and re-render modal reactively
- [x] Show loading state in modal price section while fetching
- [x] Handle errors gracefully (show "Price unavailable")

### Phase 4: Python Scraper Update ⬜ (deferred)
> Update/retire Python pipeline; regenerate pokemonData.js

- [ ] Evaluate: TCGDex has Cardmarket pricing — can we retire `pokemon_scraper.py`?
- [ ] Update `concat_pokemon_data.py` to output new internal schema format
- [ ] Regenerate `pokemonData.js` with new shape
- [ ] Verify offline fallback works with new data shape

### Phase 5: IndexedDB Migration ✅
> Handle schema change for cached card data

- [x] Bump `CONFIG.DB_VERSION` to v2
- [x] Add migration in `DBService.init()` `onupgradeneeded`: clear old `cards` store
- [x] Bump `CACHE_NAME` in `sw.js` to `pokemon-tcgdex-v4`

### Phase 6: QA & Cutover ✅
> Compare v2 vs v1 side-by-side; promote when ready

- [x] Test v2 at `localhost:8000/v2/`
- [x] Verify all existing user data (favorites, notes, bought) still loads
- [x] Verify price display in modals
- [x] Promote v2 to root (2026-03-16)
- [x] Update `ARCHITECTURE.md` to reflect new architecture
- [x] Remove old `index.html`, `index2.html`, v2 folder
- [x] Update all documentation (CLAUDE.md, copilot-instructions.md, README.md)

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GraphQL pricing not available | **Confirmed** | Medium | Use lazy REST fetch on modal open |
| Card IDs differ between APIs | **Low** (same format!) | High | Verified: `base1-4` works in both — user data safe |
| Missing cards in TCGDex | Low-Medium | Medium | Fallback to pokemonData.js; monitor |
| `set.releaseDate` not in card | **Confirmed** | Low | Drop year filter OR separate set fetch |
| TCGDex image CDN reliability | Unknown | Medium | Cache images via SW; lazy-load fallback |
| Cardmarket URL construction | **Confirmed** | Low | Build from `idProduct`: `https://www.cardmarket.com/en/Pokemon/Products/Singles?idProduct={id}` |
| N+1 pricing requests on modal | Accepted | Low | Lazy-load; each user typically opens a few cards |
| IndexedDB old-format data | Certain | Medium | DB version bump + store clear in onupgradeneeded |
| SW stale cache serves old index.html | Certain | Medium | Bump CACHE_NAME in sw.js |

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-12 | Created migration plan | Need structured approach for API swap |
| 2026-03-12 | Target API: TCGDex | Open-source, no auth, built-in CM+TCGPlayer pricing, same card ID format |
| 2026-03-12 | Fetch strategy: GraphQL list + lazy REST pricing | Avoids N+1 burst; pricing only needed on modal open |
| 2026-03-12 | Keep `images.small`/`images.large` in internal schema | Avoids template changes; mapper constructs from TCGDex base URL |
| 2026-03-12 | Keep `card.number` as alias of `localId` | Same reason — zero template breakage |
| 2026-03-12 | User data (favorites, notes, bought) needs NO migration | Card IDs (`base1-4`) are identical between APIs |
| 2026-03-12 | New version in `v2/` folder | GitOps constraint — main branch = live; compare side-by-side |
| 2026-03-12 | Python scraper evaluation deferred | TCGDex has CM pricing built-in; scraper may be retirable in Phase 4 |
| 2026-03-16 | Promoted v2 to root | v2 validated, all phases complete except scraper evaluation |
| 2026-03-16 | Modular JS architecture kept | Cleaner than single-file; ES modules work without build step |
| 2026-03-16 | Removed old `index.html`, `index2.html`, `v2/` folder | No longer needed; v2 is now the production version |
| 2026-03-16 | SW cache bumped to `pokemon-tcgdex-v4` | Force re-cache after root migration |

---

## Notes

### Image URL Construction (TCGDex)
```js
// TCGDex image field: "https://assets.tcgdex.net/en/base/base1/4"
// (no extension — append quality suffix)
const imageSmall = card.image + '/low.webp';
const imageLarge = card.image + '/high.webp';
// Some cards have no image field → fallback to placeholder
```

### Cardmarket URL Construction (TCGDex)
```js
// TCGDex provides idProduct in pricing.cardmarket.idProduct
const cmUrl = `https://www.cardmarket.com/en/Pokemon/Products/Singles?idProduct=${card.pricing.cardmarket.idProduct}`;
```

### TCGPlayer URL (TCGDex)
```js
// TCGDex does NOT provide a TCGPlayer URL
// Use the product ID to construct if needed:
const tcgUrl = `https://www.tcgplayer.com/product/${card.pricing.tcgplayer.holofoil?.productId}`;
```

### Foil Filter Update
The current filter `card.rarity.toLowerCase().includes("holo")` still works because
TCGDex uses "Rare Holo" as a rarity value. However, in v2 we can also use the
more reliable `card.variants.holo === true` check.
