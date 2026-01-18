# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pokemon TCG Collector App - A Vue 3 single-page web application for collecting and managing Pokemon Trading Card Game cards. Users can browse cards, track purchases, add favorites, take notes, and manage custom collections.

## Technology Stack

- **Frontend**: Vue 3 (via CDN), vanilla JavaScript, CSS3 with glassmorphism
- **Data**: Pokemon TCG API (api.pokemontcg.io/v2), IndexedDB for persistence, localStorage fallback
- **Offline**: Service Worker (sw.js) for PWA capabilities
- **Data Generation**: Python scripts for web scraping Cardmarket.com

## Development

**No build step required** - Static site runs directly in browser.

Open `index.html` in a browser. For local development, set `LOCAL_DEV = true` in index.html line 12.

### Python Scripts (Data Generation)

```bash
# Scrape Pokemon card data from Cardmarket
python3 pokemon_scraper.py

# Batch scrape multiple Pokemon
python3 batch_scraper.py

# Concatenate JSON files into pokemonData.js
python3 concat_pokemon_data.py

# Download card images locally
python3 download_pokemon_images.py
```

Python dependencies: selenium, webdriver-manager, beautifulsoup4, requests

## Architecture

### Key Files

- `index.html` - Main Vue 3 app (primary version)
- `index2.html` - Alternative/newer version
- `styles.css` - All styling with CSS variables
- `sw.js` - Service Worker for offline caching
- `pokemonData.js` - Generated file with all Pokemon card data (~3.5MB)

### Vue App Structure

The app uses a centralized `CONFIG` object for all settings (API endpoints, default Pokemon tabs, cache expiry).

**Core Services:**
- `DBService` - IndexedDB wrapper with connection pooling, retry logic, and localStorage fallback
- `LazyLoadService` - IntersectionObserver for image loading

**Data State:**
- `allCards[]` - Currently displayed cards
- `boughtCards{}` - Purchase tracking by card ID
- `favoriteCards{}` - Favorited cards
- `cardNotes{}` - User notes per card
- `customCollections[]` - User-created collections

### Storage

- **IndexedDB**: Stores `cards` (cached API results), `settings`, `userData`
- **localStorage**: Fallback with auto-migration to IndexedDB
- **Cache**: 24-hour expiry for API results

### Data Flow

1. App loads CONFIG and connects to IndexedDB
2. User data (favorites, notes, collections) loaded from storage
3. Pokemon tab selection triggers API query to Pokemon TCG API
4. Results cached in IndexedDB; falls back to pokemonData.js offline

## Code Patterns

- Configuration-driven via centralized CONFIG object
- Vue 3 with template IDs for component templates
- Debounced search (300ms) for performance
- Graceful degradation: IndexedDB → localStorage fallback
