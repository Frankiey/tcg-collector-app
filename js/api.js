/**
 * api.js — TCGDex API integration.
 *
 * Two-stage fetch strategy:
 *   Stage 1 (fetchCards):     GraphQL query — loads card list with HP, types, rarity, set info.
 *                              No pricing. Results cached in IndexedDB (24h TTL).
 *   Stage 2 (fetchCardDetail): Lazy REST GET /cards/{id} — loads pricing on modal open.
 *
 * mapCard() normalises a raw TCGDex GraphQL card into the internal card schema used
 * by all templates and components.
 */

import CONFIG from './config.js';
import DBService from './db.js';

/**
 * Normalise a raw TCGDex card response to the internal schema.
 * All templates reference these field names — do not rename without updating templates.
 *
 * @param {Object} raw — raw card from TCGDex GraphQL or REST response
 * @returns {Object} normalised card
 */
export function mapCard(raw) {
  return {
    id: raw.id,
    name: raw.name,
    hp: raw.hp != null ? String(raw.hp) : null,   // TCGDex returns number; normalise to string
    types: raw.types || [],
    rarity: raw.rarity || null,
    category: raw.category || 'Pokemon',
    stage: raw.stage || null,
    localId: raw.localId,
    number: raw.localId,                           // alias so templates work unchanged
    set: raw.set ? {
      id: raw.set.id,
      name: raw.set.name,
      releaseDate: null                            // enriched later by _enrichSetDetails()
    } : null,
    images: {
      small: raw.image ? raw.image + '/low.webp' : '',
      large: raw.image ? raw.image + '/high.webp' : ''
    },
    variants: raw.variants || { holo: false, firstEdition: false, reverse: false, promo: false },
    illustrator: raw.illustrator || null,
    description: raw.description || null,
    pricing: {
      loaded: false,
      tcgplayer: null,
      cardmarket: null
    }
  };
}

const ApiService = {
  // Session cache: setId → { releaseDate, serieId }
  _setCache: {},

  // Fetch and cache set details for a single set ID
  async _fetchSetDetails(setId) {
    if (this._setCache[setId] !== undefined) return;
    try {
      const res = await fetch(`${CONFIG.TCGDEX_REST_URL}/sets/${setId}`);
      if (!res.ok) { this._setCache[setId] = {}; return; }
      const data = await res.json();
      this._setCache[setId] = {
        releaseDate: data.releaseDate || null,
        serieId: data.serie?.id || null
      };
    } catch {
      this._setCache[setId] = {};
    }
  },

  // Fetch set details for all unique sets in a card list, then patch the cards in-place
  async _enrichSetDetails(cards) {
    const uniqueSetIds = [...new Set(cards.map(c => c.set?.id).filter(Boolean))];
    await Promise.all(uniqueSetIds.map(id => this._fetchSetDetails(id)));
    cards.forEach(card => {
      if (card.set?.id) {
        const info = this._setCache[card.set.id] || {};
        card.set.releaseDate = info.releaseDate || null;
        card.set.serieId = info.serieId || null;
      }
    });
  },

  // TCGDex search is case-sensitive — ensure first letter is uppercase
  _formatPokemonName(name) {
    if (!name) return name;
    return name.charAt(0).toUpperCase() + name.slice(1);
  },

  /**
   * Stage 1 — Load card list for a collection tab.
   * Returns cached data within 24h; fetches from GraphQL otherwise.
   *
   * @param {string} collectionId — Pokemon name (lowercase, used as cache key)
   * @param {Object} options
   * @param {boolean} options.forceRefresh — bypass cache
   * @returns {Promise<Object[]>} array of normalised cards
   */
  async fetchCards(collectionId, options = {}) {
    const { forceRefresh = false } = options;

    // Offline: serve from IndexedDB cache
    if (!navigator.onLine) {
      try {
        const cachedCards = await DBService.getCards(collectionId);
        if (cachedCards && cachedCards.length > 0) {
          return cachedCards;
        }
        throw new Error('No cached data available while offline');
      } catch (err) {
        throw new Error('Cannot fetch cards while offline: ' + err.message);
      }
    }

    // Cache hit (within TTL)
    if (!forceRefresh) {
      const metadata = await DBService.getCardMetadata(collectionId);
      if (metadata && Date.now() - metadata.timestamp < CONFIG.CACHE_EXPIRY) {
        const cachedCards = await DBService.getCards(collectionId);
        if (cachedCards && cachedCards.length > 0) {
          return cachedCards;
        }
      }
    }

    // GraphQL query — card list without pricing
    const pokemonName = this._formatPokemonName(collectionId);
    const gqlQuery = `{
      cards(
        filters: { name: "${pokemonName}" }
        pagination: { page: 1, itemsPerPage: 250 }
      ) {
        id name image localId rarity hp types stage
        set { id name }
        variants { holo firstEdition }
      }
    }`;

    try {
      const response = await fetch(CONFIG.TCGDEX_GRAPHQL_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: gqlQuery })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`GraphQL API responded with status ${response.status}: ${errorText}`);
      }

      const json = await response.json();

      if (json.errors && json.errors.length > 0) {
        throw new Error('GraphQL error: ' + json.errors[0].message);
      }

      const rawCards = json.data?.cards || [];

      // TCGDex name filter is a substring match — "Mew" also returns "Mewtwo".
      // Keep only cards whose name is an exact match or a variant with a space suffix
      // (e.g. "Mew ex", "Mew V", "Mew VMAX") to exclude partial-prefix false positives.
      const searchNameLower = pokemonName.toLowerCase();
      const exactCards = rawCards.filter(c => {
        const n = (c.name || '').toLowerCase();
        return n === searchNameLower || n.startsWith(searchNameLower + ' ');
      });

      const mappedCards = exactCards.map(mapCard);

      // Enrich with releaseDate + serieId in parallel
      await this._enrichSetDetails(mappedCards);

      // Exclude Pokémon TCG Pocket cards (serie id 'tcgp' covers all Pocket sets)
      const EXCLUDED_SERIES = new Set(['tcgp']);
      const physicalCards = mappedCards.filter(c => !EXCLUDED_SERIES.has(c.set?.serieId));

      // Cache (pricing added lazily later, not stored here)
      await DBService.saveCards(collectionId, physicalCards);

      return physicalCards;
    } catch (error) {
      console.error('API Error:', error);

      // Fallback to stale cache if available
      try {
        const cachedCards = await DBService.getCards(collectionId);
        if (cachedCards && cachedCards.length > 0) {
          return cachedCards;
        }
      } catch (cacheError) {
        console.error('Cache retrieval error:', cacheError);
      }

      throw new Error(`Failed to fetch cards: ${error.message}`);
    }
  },

  /**
   * Stage 2 — Lazy pricing fetch, triggered when a card modal opens.
   * Returns pricing, illustrator, and description for a single card.
   *
   * @param {string} cardId — e.g. "base1-4"
   * @returns {Promise<{ pricing: Object|null, illustrator: string|null, description: string|null }>}
   */
  async fetchCardDetail(cardId) {
    const response = await fetch(`${CONFIG.TCGDEX_REST_URL}/cards/${cardId}`);

    if (!response.ok) {
      throw new Error(`REST API responded with status ${response.status}`);
    }

    const card = await response.json();
    return {
      pricing: card.pricing || null,
      illustrator: card.illustrator || null,
      description: card.description || null
    };
  }
};

export default ApiService;
