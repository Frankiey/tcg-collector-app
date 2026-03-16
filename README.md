<div align="center">

<img src="https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png" width="80" alt="Pokéball" />

# Pokémon TCG Collector

**Browse, track, and manage your entire Pokémon Trading Card Game collection — right in the browser.**

[![PWA Ready](https://img.shields.io/badge/PWA-ready-5A0FC8?logo=pwa&logoColor=white)](https://web.dev/progressive-web-apps/)
[![Vue 3](https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![TCGDex API](https://img.shields.io/badge/TCGDex-API-EF5350?logo=pokemon&logoColor=white)](https://tcgdex.dev/)
[![No Build Step](https://img.shields.io/badge/no%20build%20step-★-FFD700)](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
[![Offline First](https://img.shields.io/badge/offline-first-2196F3?logo=serviceworker&logoColor=white)](https://developers.google.com/web/fundamentals/instant-and-offline/offline-cookbook)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## What is this?

A **zero-dependency, offline-capable** web app for Pokémon TCG collectors. It pulls live card data from the [TCGDex API](https://tcgdex.dev/), lets you browse every card of any Pokémon, and gives you personal tools to track your collection — all stored locally in your browser with no account needed.

### Who is it for?

| If you... | This app lets you... |
|-----------|---------------------|
| Collect physical Pokémon cards | Track what you own and what you've bought |
| Hunt specific cards | Browse all prints of any Pokémon with rarity, HP, and set info |
| Watch card prices | See live Cardmarket & TCGPlayer market prices per card |
| Organize your collection | Build custom collections and groups |
| Prefer offline-first tools | Works fully without internet after first load |

---

## Features

- **Browse by Pokémon** — Tab-based navigation: pick any Pokémon, instantly see every card ever printed for it across all sets
- **Live pricing** — Cardmarket and TCGPlayer prices loaded on demand when you open a card
- **Track purchases** — Mark individual cards as bought; filter your view to owned/unowned
- **Favorites** — Star cards and access them in a dedicated view
- **Notes** — Add personal notes to any card (condition, price paid, wishlist info)
- **Custom collections** — Create and name your own groups of cards
- **Search & filter** — Full text search with filters for rarity, type, set, price range, and more
- **Import / Export** — Back up and restore your full collection as JSON
- **PWA** — Install to your home screen; works offline after the first visit
- **Glassmorphism UI** — Sleek, modern design with smooth animations

---

## Screenshots

> _Drop your screenshots here!_
>
> Tip: run the app, take a few captures of the card grid, a modal, and the favorites view, then add them here as:
> ```md
> ![Card Grid](docs/screenshots/grid.png)
> ```

---

## Quick Start

No npm. No build step. No config. Just Python (or any static file server):

```bash
git clone https://github.com/your-username/tcg-collector-app.git
cd tcg-collector-app
python3 -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000) — that's it.

> **Tip:** The app works in any modern browser. For the full PWA/offline experience, use Chrome or Edge and hit "Install" in the address bar.

---

## How It Works

The app is a **Vue 3 SPA** with no bundler — all modules are native ES modules loaded directly in the browser. State lives on the root Vue instance, persisted in IndexedDB.

```
Browser
  └─ index.html  (templates + Vue mount)
       └─ js/app.js  (entry — state, lifecycle, methods)
            ├─ js/config.js      — central CONFIG (API URLs, defaults)
            ├─ js/api.js         — TCGDex GraphQL + REST, card normalizer
            ├─ js/db.js          — IndexedDB wrapper (retry + localStorage fallback)
            ├─ js/utils.js       — LazyLoad, Notifications, Offline detection
            └─ js/components.js  — Card, Modal, Notification, ImportDialog
```

### Data Flow

**Loading cards (two-stage fetch):**

1. You select a Pokémon tab → GraphQL query fetches the full card list (name, HP, types, rarity, set, image)
2. Results are cached in IndexedDB for 24 hours — subsequent visits are instant
3. You open a card → a lazy REST call fetches pricing for that specific card only

**Offline:**

The Service Worker precaches all HTML, CSS, and JS modules. When you're offline, IndexedDB serves stale card data and your personal collection data is always available locally.

**Storage hierarchy:**

```
IndexedDB (primary)
  └─ localStorage (automatic fallback for older browsers)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | [Vue 3](https://vuejs.org/) via CDN (no SFC, no build) |
| API | [TCGDex v2](https://tcgdex.dev/) — GraphQL for lists, REST for pricing |
| Storage | IndexedDB (primary) + localStorage (fallback) |
| Offline | Service Worker — cache-first strategy |
| Fonts & Icons | Google Fonts (Poppins) + Font Awesome 6 |
| Styling | CSS3 with custom properties, glassmorphism |

**Why no build step?** The app is intentionally dependency-free. No webpack, no Vite, no node_modules. This makes it trivially deployable to any static host (GitHub Pages, Netlify, Cloudflare Pages) and easy to contribute to without toolchain setup.

---

## Project Structure

```
tcg-collector-app/
├── index.html          # HTML shell + all Vue component templates
├── styles.css          # All CSS — variables, glassmorphism, responsive
├── sw.js               # Service Worker — precache + offline-first fetch
│
├── js/
│   ├── app.js          # Vue 3 app — state, computed, methods, lifecycle
│   ├── config.js       # Central CONFIG object (API URLs, DB version, defaults)
│   ├── api.js          # ApiService — TCGDex GraphQL + REST + card normalizer
│   ├── db.js           # DBService — IndexedDB with retry + localStorage fallback
│   ├── utils.js        # Utilities: LazyLoad, Notifications, Offline detection
│   └── components.js   # Vue components: Card, Modal, Notification, ImportDialog
│
```

---

## Deployment

Since it's a static site, deployment is a one-liner with any host:

**GitHub Pages:**
```bash
# Push to main → Pages serves it automatically (if configured)
git push origin main
```

**Netlify / Cloudflare Pages:** Connect the repo, set the publish directory to `/` (root), no build command needed.

**Self-hosted:**
```bash
python3 -m http.server 8000
# or: npx serve .
# or: caddy file-server
```

---

## Documentation

| File | What's in it |
|------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, module map, full data flow diagrams |
| [MIGRATION.md](MIGRATION.md) | TCGDex API migration decision log |
| [CLAUDE.md](CLAUDE.md) | AI agent instructions (rules, conventions, do/don't) |

---

## Contributing

Pull requests welcome. A few things to know before diving in:

- **No build step** — keep it that way. No bundlers, no package managers.
- **ES modules only** — all JS goes in `js/*.js` files with `import`/`export`.
- **Bump `CACHE_NAME`** in `sw.js` after changing any cached asset.
- Read [ARCHITECTURE.md](ARCHITECTURE.md) before making structural changes.

---

## License

[MIT](LICENSE) — do what you want, just don't remove the license notice.

---

<div align="center">

Built with Vue 3 · Powered by [TCGDex](https://tcgdex.dev/) · No Pokémon were harmed in the making of this app

</div>
