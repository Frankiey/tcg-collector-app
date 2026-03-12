# Scratchpad — TCGDex Migration

> My working analysis notes. Raw, updated as I go.
> For clean decisions see WORKNOTES.md. For the full plan see MIGRATION.md.

---

## TCGDex API — Live Test Results (2026-03-12)

### Endpoints that work

```
GET  https://api.tcgdex.net/v2/en/cards/{id}
     → Full card object with pricing ✅

GET  https://api.tcgdex.net/v2/en/cards?category=Pokemon&name={name}
     → Shallow array [{id, localId, name, image?}] ⚠️ no pricing

POST https://api.tcgdex.net/v2/graphql
     Body: { "query": "..." }
     → Rich card objects BUT no pricing field available ⚠️

GET  https://api.tcgdex.net/v2/en/sets
     → Array of sets [{id, name, logo, cardCount}] ✅
```

### Endpoints that DON'T work

```
GET  https://api.tcgdex.net/v2/en/pokemon/Charizard  → 404
GET  https://api.tcgdex.net/v2/en/cards?name=Charizard  → [] (case sensitive? just wrong param?)
GET  https://api.tcgdex.net/v2/en/cards?q=name:Charizard  → [] (pokemontcg.io syntax not supported)
```

**Working search format:** `?category=Pokemon&name=Charizard` (capital C)
→ Test if case-insensitive: need to verify. Current code uses `collectionId.toLowerCase()` so
  might need to capitalize first letter.

### Full card response (base1-4 Charizard)

```json
{
  "category": "Pokemon",
  "id": "base1-4",
  "illustrator": "Mitsuhiro Arita",
  "image": "https://assets.tcgdex.net/en/base/base1/4",
  "localId": "4",
  "name": "Charizard",
  "rarity": "Rare",
  "set": { "cardCount": {"official":102,"total":102}, "id":"base1", "logo":"...", "name":"Base Set" },
  "variants": {"firstEdition":true,"holo":true,"normal":false,"reverse":false,"wPromo":false},
  "variants_detailed": [...],
  "dexId": [6],
  "hp": 120,
  "types": ["Fire"],
  "evolveFrom": "Charmeleon",
  "stage": "Stage2",
  "abilities": [...],
  "attacks": [...],
  "weaknesses": [...],
  "resistances": [...],
  "retreat": 3,
  "legal": {"standard":false,"expanded":false},
  "updated": "2026-01-07T13:21:43+01:00",
  "pricing": {
    "cardmarket": {
      "updated": "2026-03-12T01:44:25.000Z",
      "unit": "EUR",
      "idProduct": 273699,
      "avg": 370.07,
      "low": 40,
      "trend": 415.87,
      "avg1": 1196.33,
      "avg7": 411.59,
      "avg30": 372.31
    },
    "tcgplayer": {
      "updated": "2026-03-11T20:05:23.000Z",
      "unit": "USD",
      "holofoil": {
        "productId": 42382,
        "lowPrice": 599.99,
        "midPrice": 800,
        "highPrice": 2000,
        "marketPrice": 492.82
      }
    }
  }
}
```

**Note:** `rarity` here is "Rare" not "Rare Holo" — but the GraphQL query returned "Rare Holo"
for other Charizard cards. Check if this is inconsistent in TCGDex data or set-specific.
The base1 set cards might have a different rarity taxonomy.

### GraphQL response (Charizard, 3 results)

```json
{
  "id": "pl4-1",
  "name": "Charizard",
  "image": "https://assets.tcgdex.net/en/pl/pl4/1",
  "localId": "1",
  "rarity": "Rare Holo",
  "hp": null,
  "types": ["Fire"],
  "stage": "Stage2",
  "set": { "id": "pl4", "name": "Arceus" },
  "variants": { "holo": true, "firstEdition": false }
}
```

**Note:** `hp` can be `null` in GraphQL responses (some older cards may lack it).
Handle defensively.

---

## Code Areas to Touch in v2/index.html

### CONFIG block (~line 509)
```js
// Change:
API_BASE_URL: 'https://api.pokemontcg.io/v2',
// To:
TCGDEX_REST_URL: 'https://api.tcgdex.net/v2/en',
TCGDEX_GQL_URL: 'https://api.tcgdex.net/v2/graphql',
```

### ApiService.fetchCards (~line 919)
- Replace `fetch(${CONFIG.API_BASE_URL}/cards?q=...)` with GraphQL POST
- Strip `{ data }` destructure — TCGDex list/GQL returns flat array
- Run through `mapCard()` on each result

### New: mapCard() function
```js
function mapCard(raw) {
  const imageBase = raw.image || '';
  return {
    id: raw.id,
    name: raw.name,
    hp: raw.hp != null ? String(raw.hp) : null,
    types: raw.types || [],
    rarity: raw.rarity || null,
    category: raw.category || 'Pokemon',
    stage: raw.stage || null,
    number: raw.localId || null,      // alias for templates
    localId: raw.localId || null,
    set: {
      id: raw.set?.id || null,
      name: raw.set?.name || null,
      releaseDate: raw.set?.releaseDate || null,
    },
    images: {
      small: imageBase ? imageBase + '/low.webp' : '',
      large: imageBase ? imageBase + '/high.webp' : '',
    },
    variants: raw.variants || null,
    pricing: {
      loaded: false,
      cardmarket: null,
      tcgplayer: null,
    },
  };
}
```

### New: mapCardPricing() function
```js
function mapCardPricing(restCard) {
  const cm = restCard.pricing?.cardmarket;
  const tcp = restCard.pricing?.tcgplayer;
  return {
    loaded: true,
    cardmarket: cm ? {
      prices: {
        averageSellPrice: cm.avg,
        trendPrice: cm.trend,
        avg7: cm.avg7,
        avg30: cm.avg30,
        low: cm.low,
      },
      url: cm.idProduct
        ? `https://www.cardmarket.com/en/Pokemon/Products/Singles?idProduct=${cm.idProduct}`
        : null,
    } : null,
    tcgplayer: tcp ? {
      prices: {
        // mirror old shape so utils.getCardPrice() / utils.getPriceValue() still work
        ...(tcp.holofoil ? {
          holofoil: {
            market: tcp.holofoil.marketPrice,
            mid: tcp.holofoil.midPrice,
            low: tcp.holofoil.lowPrice,
            high: tcp.holofoil.highPrice,
          }
        } : {}),
      },
      url: tcp.holofoil?.productId
        ? `https://www.tcgplayer.com/product/${tcp.holofoil.productId}`
        : null,
    } : null,
  };
}
```

> By mirroring old price shape inside `pricing.cardmarket.prices` and `pricing.tcgplayer.prices`,
> the existing `utils.getCardPrice()` and `utils.getPriceValue()` work with minimal changes.
> Only need to update the root path from `card.tcgplayer` → `card.pricing.tcgplayer` and
> `card.cardmarket` → `card.pricing.cardmarket`.

### utils.getCardPrice (~line 1037)
```js
// Change:
if (card.tcgplayer?.prices) { ... }
else if (card.cardmarket?.prices) { ... }
// To:
if (card.pricing?.tcgplayer?.prices) { ... }
else if (card.pricing?.cardmarket?.prices) { ... }
```

### Card template price blocks (~line 427, 442)
```html
<!-- Change v-if conditions: -->
v-if="card.tcgplayer?.prices"    →  v-if="card.pricing?.tcgplayer?.prices"
v-if="card.cardmarket?.prices"   →  v-if="card.pricing?.cardmarket?.prices"
<!-- And the price loop: -->
card.cardmarket.prices[key]      →  card.pricing.cardmarket.prices[key]
card.tcgplayer.url               →  card.pricing.tcgplayer.url
card.cardmarket.url              →  card.pricing.cardmarket.url
```

---

## Open Questions

1. **Is `?name=` search case-sensitive?**
   Tested: `?category=Pokemon&name=Charizard` works (capital C). Need to test lowercase.
   The current app stores tabs as lowercase (e.g., "charizard"). Need to capitalize first letter
   before querying, OR use GraphQL `filters:{name:"Charizard"}` (test if case-insensitive).

2. **Pagination: how many Charizard cards are there?**
   If > 250, pagination is needed. GraphQL supports `pagination:{page:1,itemsPerPage:250}`.
   Current app uses `pageSize=250` in pokemontcg.io. Should be fine.

3. **`set.releaseDate` is not in card objects**
   The year filter (`card.set.releaseDate.split("/")[0]`) will break.
   Options: (a) drop year filter, (b) fetch set details separately and cache them,
   (c) build a local set-year map. TCGDex has a `/sets/{id}` endpoint with `releaseDate`.

4. **`rarity` inconsistency: "Rare" vs "Rare Holo"**
   base1-4 Charizard REST returns `rarity: "Rare"` but the GraphQL returns "Rare Holo"
   for some cards. Is the REST result wrong, or is it a different variant?
   The `variants.holo: true` field is the reliable signal — use that for foil filter.

5. **Can we retire the Python Cardmarket scraper?**
   TCGDex includes live Cardmarket pricing. Check if the data quality / freshness is
   comparable to what the scraper was producing. If yes, retire `pokemon_scraper.py`
   and `batch_scraper.py`. Keep `concat_pokemon_data.py` (updated for new schema).

6. **GraphQL `hp: null` for some cards**
   Confirmed — handle with `raw.hp != null ? String(raw.hp) : null` in mapper.
   Template already has `v-if="card.hp"` guard — safe.

---

## Verified Facts

- ✅ Card IDs (`base1-4` format) are identical in both APIs — user data is safe
- ✅ `types[]` field is identical in both APIs
- ✅ `set.id` and `set.name` are identical
- ✅ `rarity` values overlap (both use "Rare Holo") but may not be 1:1 exhaustively
- ✅ TCGDex is completely free/no-auth
- ✅ TCGDex has live Cardmarket + TCGPlayer pricing in REST `/cards/{id}`
- ✅ GraphQL available and working (minus pricing)
- ⚠️ Pricing only in REST individual card endpoint, not GraphQL
- ⚠️ `set.releaseDate` NOT in card object (needs separate set fetch or drop)
- ⚠️ `image` field missing on some cards (older/promo cards in list endpoint)
- ⚠️ Search by name needs capitalization normalization

---

## TODO for Next Session

- [ ] Test case-sensitivity of `?name=` and GraphQL `filters:{name:}` with lowercase input
- [ ] Test pagination: how many results for popular Pokemon (Charizard, Pikachu)?
- [ ] Check `releaseDate` on a set object: `GET /v2/en/sets/base1`
- [ ] Start implementing `v2/index.html` — Phase 1 changes
- [ ] Decide on year filter approach (Option a/b/c above)
