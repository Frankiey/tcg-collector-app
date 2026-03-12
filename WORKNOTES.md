# Work Notes — TCGDex Migration

> Decision log and rationale trail. Every significant call gets recorded here.
> Raw analysis lives in SCRATCHPAD.md. Full plan in MIGRATION.md.

---

## Session 1 — 2026-03-12

### Context
User wants to migrate from `api.pokemontcg.io/v2` to TCGDex (`api.tcgdex.net/v2`).
GitOps constraint: main branch is live. New version goes in `v2/` folder for side-by-side compare.

---

### Decision 001 — Target API: TCGDex
**Date:** 2026-03-12

**Options considered:**
1. pokemontcg.io v2 (current) — keep as-is, no migration needed
2. TCGDex — open-source, no auth, built-in pricing
3. Scryfall-style custom backend — out of scope

**Decision:** TCGDex

**Rationale:**
- No API key required — eliminates auth complexity and key rotation risk
- Built-in live Cardmarket + TCGPlayer pricing — may let us retire Python scrapers
- Card IDs use the same `setId-localId` format (e.g., `base1-4`) as pokemontcg.io
  → user data (favorites, notes, bought) requires NO migration
- Open source database (github.com/tcgdex/cards-database)
- Handles 10M+ requests/month — production-grade reliability

**Trade-offs accepted:**
- Pricing only available via individual REST calls (not in list/GraphQL)
- `set.releaseDate` not embedded in card objects
- Image CDN is different (new URLs, WebP format)

---

### Decision 002 — Fetch Strategy: GraphQL list + lazy REST pricing
**Date:** 2026-03-12

**Problem:**
TCGDex has no single endpoint that returns full card lists with pricing.
- `GET /cards?category=Pokemon&name={x}` → shallow `{id, localId, name, image}` only
- `POST /graphql` → rich fields (HP, types, rarity, variants, set) but NO pricing
- `GET /cards/{id}` → full card with pricing, but requires one request per card

**Options considered:**
1. **REST list + Promise.all individual fetches** — Gets full data for all cards upfront.
   Risk: Charizard has ~50 cards → 51 requests on tab select. Could hit rate limits
   or be slow on mobile. Acceptable for small sets, problematic for large ones.

2. **GraphQL for list + lazy REST pricing on modal open** ✅ (chosen)
   Trade-off: pricing not shown on card grid (only in modal). Acceptable UX because
   the current app also only shows pricing in the detail modal.

3. **GraphQL only** — Drop pricing entirely. Not acceptable; pricing is a core feature.

4. **Hybrid: GraphQL + background batch-fetch pricing** — Over-engineered for now.

**Decision:** GraphQL for card list (all display fields), lazy REST fetch on modal open for pricing.

**Implementation note:**
- `ApiService.fetchCards()` → GraphQL POST
- `ApiService.fetchCardDetail(id)` → new method, `GET /cards/{id}`
- Modal `openModal(card)` → call `fetchCardDetail` if `!card.pricing?.loaded`
- Store pricing in IndexedDB after first fetch so repeat modal opens are instant

---

### Decision 003 — Internal Card Schema: preserve `images.small/large` and `number`
**Date:** 2026-03-12

**Problem:**
TCGDex uses `image` (single base URL, no extension) and `localId` instead of
`images.small/large` and `number`. Changing templates would touch 8+ locations
in index.html (risky, tedious, diff-noisy).

**Decision:** Map TCGDex fields to old-style internal schema.
- `images.small = raw.image + '/low.webp'`
- `images.large = raw.image + '/high.webp'`
- `number = raw.localId` (alias)
- `card.pricing.cardmarket.prices` mirrors old `card.cardmarket.prices` shape
- `card.pricing.tcgplayer.prices` mirrors old `card.tcgplayer.prices` shape

**Trade-off:** The mapper is a bit verbose. But templates need zero changes for
image/number fields. Only price access paths (`card.tcgplayer` → `card.pricing.tcgplayer`)
need to change, which is a small set of locations.

---

### Decision 004 — New version in `v2/` folder
**Date:** 2026-03-12

**Context:** User explicitly requested this for GitOps workflow.

**Structure:**
```
v2/
├── index.html    (the new app — modified copy of root index.html)
├── styles.css    (copy or symlink from root — CSS unchanged)
├── sw.js         (CACHE_NAME → 'pokemon-tcgdex-v1')
└── pokemonData.js (regenerated in Phase 4)
```

**Deployment path:** When v2 is ready, copy `v2/index.html` → root `index.html`
and merge other files. Or update the deployment pipeline to serve from `v2/`.

---

### Decision 005 — User data: NO migration needed
**Date:** 2026-03-12

**Verification:** Tested `GET https://api.tcgdex.net/v2/en/cards/base1-4` — returns `"id": "base1-4"`.
Same format as pokemontcg.io. All user data (favorites, notes, bought cards, custom collections)
is keyed by card ID → all data is portable without any migration logic.

**IndexedDB impact:** Only the `cards` store (API response cache) needs clearing.
The `userData` store is untouched. DBService version bump + `deleteObjectStore('cards')` +
`createObjectStore('cards')` in `onupgradeneeded` is sufficient.

---

### Decision 006 — Python scraper evaluation deferred
**Date:** 2026-03-12

**Context:** The Python scrapers (`pokemon_scraper.py`, `batch_scraper.py`) were built to
extract Cardmarket pricing because the old API lacked it. TCGDex has live CM pricing built-in.

**Decision:** Evaluate in Phase 4. If TCGDex CM pricing is sufficient, retire the scrapers.
Keep `concat_pokemon_data.py` (updated) for offline pokemonData.js generation.
Keep `download_pokemon_images.py` as-is (still useful for local image caching).

**Questions to answer in Phase 4:**
- Is TCGDex CM data as fresh as what the scraper produced?
- Does the scraper provide data for cards TCGDex doesn't cover?
- Is the offline pokemonData.js still needed once TCGDex works offline via SW?

---

### Decision 007 — `set.releaseDate`: defer to Phase 2 audit
**Date:** 2026-03-12

**Context:** TCGDex card objects don't include `set.releaseDate`. The current app uses it
for a "year" filter. Options: (a) drop year filter, (b) fetch set details separately,
(c) build a local set-year lookup table.

**Decision:** Defer. The year filter is non-critical. Phase 2 template audit will decide.
Lean toward option (c) — a small hardcoded lookup for the sets the user actually has
is simpler than N extra API calls.

---

## Open Questions (unanswered as of Session 1)

| # | Question | Status |
|---|----------|--------|
| Q1 | Is `?name=` search case-sensitive? | Open |
| Q2 | Max cards for popular Pokemon (Charizard, Pikachu)? Need pagination? | Open |
| Q3 | Does `GET /sets/{id}` return `releaseDate`? | Open |
| Q4 | TCGDex rarity taxonomy completeness — same values as pokemontcg.io? | Open |
| Q5 | Can we retire Python Cardmarket scraper entirely? | Deferred to Phase 4 |

---

## Next Steps (start of Session 2)

1. Check SCRATCHPAD.md "TODO for Next Session" section
2. Run quick API tests for Q1-Q4 above
3. Begin Phase 0: copy `index.html` to `v2/index.html`, copy `sw.js` to `v2/sw.js`
4. Begin Phase 1: implement `mapCard()`, `mapCardPricing()`, rewrite `ApiService.fetchCards()`
