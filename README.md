# Pokémon TCG Collector

A Vue 3 PWA for browsing, collecting, and tracking Pokémon Trading Card Game cards. Browse cards by Pokémon, track purchases, add favorites, take notes, and manage custom collections — all offline-capable.

## Quick Start

```bash
python3 -m http.server 8000
# Open http://localhost:8000
```

No build step, no npm, no bundler. Static files only.

## Tech Stack

- **Vue 3** via CDN (`unpkg.com/vue@3`) — no SFC, no build step
- **TCGDex API** — GraphQL for card lists, REST for pricing (lazy-loaded on modal open)
- **IndexedDB** for persistence, localStorage fallback
- **Service Worker** for offline-first PWA
- **ES Modules** — modular JS architecture (`js/*.js`)

## Project Structure

```
index.html          HTML shell with Vue templates (~560 lines)
styles.css          All CSS — variables, glassmorphism, responsive (~1580 lines)
sw.js               Service Worker — precaches all JS modules
js/
  app.js            Vue 3 app entry point — state, methods, lifecycle
  config.js         CONFIG object — API URLs, DB version, defaults
  api.js            ApiService — TCGDex GraphQL + REST
  db.js             DBService — IndexedDB wrapper with retry logic
  utils.js          Utilities, LazyLoad, Notification, Offline services
  components.js     Vue components (Card, Modal, Notification, ImportDialog)
pokemonData.js      Generated offline fallback data (~122K lines, never edit)
data/               JSON per Pokémon species (scraper output)
images/             Downloaded card images (local cache)
```

## Documentation

| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | System design, module map, data flow |
| `MIGRATION.md` | TCGDex migration plan + decision log |
| `WORKNOTES.md` | Session decision trail |
| `SCRATCHPAD.md` | Raw research notes |

## Data Generation (Python)

```bash
python3 pokemon_scraper.py          # Scrape Cardmarket for a Pokémon
python3 batch_scraper.py            # Batch scrape
python3 concat_pokemon_data.py      # Build pokemonData.js from data/*.json
python3 download_pokemon_images.py  # Download card images locally
```

Requires: `selenium`, `webdriver-manager`, `beautifulsoup4`, `requests`

## License

See [LICENSE](LICENSE).
