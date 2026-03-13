/**
 * config.js — Central configuration and constants.
 * All environment-specific values, API URLs, defaults, and mappings live here.
 * Import this module anywhere you need access to CONFIG.
 */

const CONFIG = {
  TCGDEX_GRAPHQL_URL: 'https://api.tcgdex.net/v2/graphql',
  TCGDEX_REST_URL: 'https://api.tcgdex.net/v2/en',
  CACHE_VERSION: 2,
  CACHE_EXPIRY: 24 * 60 * 60 * 1000, // 24 hours in ms
  DB_NAME: 'pokemon-collector',
  DB_VERSION: 2,
  LOCAL_STORAGE_KEYS: {
    BOUGHT: 'boughtCards',
    NOTES: 'cardNotes',
    FAVORITES: 'favoriteCards',
    CUSTOM_TABS: 'customPokemonTabs',
    CUSTOM_COLLECTIONS: 'customCollections',
    COLLECTION_CARDS: 'collectionCards',
    QUERY_TYPES: 'queryTypes'
  },
  DEFAULT_POKEMON: [
    'Charizard', 'Cubone', 'Psyduck', 'Pikachu', "Farfetch'd",
    'Golem', 'Gastly', 'Haunter', 'Gengar', 'Mew', 'Mewtwo',
    'Machop', 'Machoke', 'Machamp'
  ],
  PRICE_LABELS: {
    tcgplayer: {
      'low': 'Low',
      'mid': 'Mid',
      'high': 'High',
      'marketPrice': 'Market'
    },
    cardmarket: {
      'avg': 'Avg Sell',
      'low': 'Low',
      'trend': 'Trend',
      'avg30': '30d Avg'
    }
  },
  TYPE_ICONS: {
    fire: 'fire',
    water: 'tint',
    grass: 'leaf',
    electric: 'bolt',
    psychic: 'brain',
    fighting: 'fist-raised',
    darkness: 'moon',
    metal: 'cog',
    fairy: 'magic',
    dragon: 'dragon',
    colorless: 'feather',
    default: 'certificate'
  },
  DEBOUNCE_DELAY: 300,
  NOTIFICATION_DURATION: 3000,
  IMAGE_LOADING: {
    OBSERVER_ROOT_MARGIN: '200px',
    OBSERVER_THRESHOLD: 0.1
  },
  // Cardmarket set abbreviation map: TCGDex set ID → Cardmarket URL set code.
  // TCG Pocket main sets (a1, a2 …) are handled automatically (capitalise setId).
  // Only add entries where TCGDex ID ≠ Cardmarket code.
  CM_SET_CODE: {
    // TCG Pocket special sets
    'me01': 'MEW',
    'me02': 'PFL',
    // Classic Base-era
    'base1': 'BS',
    'base2': 'JU',
    'base3': 'FO',
    'base4': 'TR',
    'base5': 'BS2',
    'base6': 'LC',
    // Gen 2
    'gym1': 'G1',
    'gym2': 'G2',
    'neo1': 'N1',
    'neo2': 'N2',
    'neo3': 'N3',
    'neo4': 'N4',
  }
};

export default CONFIG;
