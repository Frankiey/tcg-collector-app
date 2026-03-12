---
description: "Use when working with Python scraping scripts, data generation pipeline, or the pokemonData.js generation process."
---

# Data Pipeline Skill

You are working with the Python data generation pipeline.

## Pipeline overview

```
Cardmarket.com
    │ (Selenium + BeautifulSoup)
    ▼
pokemon_scraper.py        → Scrapes one Pokemon's cards
batch_scraper.py          → Runs scraper for multiple Pokemon
    │
    ▼
/data/{pokemon}.json      → Raw scraped data per species
    │
    ▼
concat_pokemon_data.py    → Merges all JSON → pokemonData.js
    │
    ▼
pokemonData.js            → Browser-ready data blob (122K lines)

download_pokemon_images.py → Downloads card images to /images/
fix_missing_images.py      → Re-downloads failed images
```

## Running the pipeline

```bash
# Scrape a single Pokemon
python3 pokemon_scraper.py

# Batch scrape
python3 batch_scraper.py

# Regenerate the JS data file
python3 concat_pokemon_data.py

# Download images
python3 download_pokemon_images.py
```

## Rules

- **Never edit pokemonData.js by hand** — Always regenerate via `concat_pokemon_data.py`
- **Python style**: PEP 8, 4-space indents
- **Dependencies**: `selenium`, `webdriver-manager`, `beautifulsoup4`, `requests`
- **Scraping is fragile** — Cardmarket's HTML structure can change. If scraping breaks, check selectors first.
- **Logs go to `/logs/`** — Check there for scraping errors
- **Images go to `/images/{pokemon}/`** — One subdirectory per species

## When the API migration happens

The scraping pipeline may need updates:
- New data source may replace or supplement Cardmarket scraping
- `concat_pokemon_data.py` output shape may need to match new API card format
- Image URLs/paths may change
