/**
 * app.js — Vue 3 application entry point.
 *
 * Imports all services and components, defines the root Vue app, and mounts it.
 * Vue 3 is loaded via CDN in index.html as window.Vue — available globally here.
 *
 * App state overview:
 *   allCards          — currently displayed card list (fetched from API / cache)
 *   boughtCards       — { [cardId]: boolean } persisted in IndexedDB
 *   favoriteCards     — { [cardId]: cardObject } persisted in IndexedDB
 *   cardNotes         — { [cardId]: string }  persisted in IndexedDB
 *   customTabs        — string[] of extra Pokemon names added by user
 *   customCollections — user-created collection objects
 *   collectionCards   — { [collectionId]: cardId[] }
 */

import CONFIG from './config.js';
import DBService from './db.js';
import ApiService from './api.js';
import { utils, LazyLoadService, NotificationService, OfflineService } from './utils.js';
import { CardComponent, ModalComponent, NotificationComponent, ImportDialogComponent } from './components.js';

const { createApp } = Vue; // Vue loaded as global via CDN in index.html

const app = createApp({
  components: {
    'card-component': CardComponent,
    'modal-component': ModalComponent,
    'notification-component': NotificationComponent,
    'import-dialog-component': ImportDialogComponent
  },

  data() {
    return {
      // UI state
      loading: false,
      errorMessage: '',
      isOffline: false,
      currentView: 'all',
      showAdvancedFilters: false,
      showCollectionForm: false,
      showImportDialog: false,

      // Navigation
      currentCollection: 'charizard',
      currentQueryType: 'pokemon',
      views: [
        { id: 'all',      name: 'All Cards',           icon: 'fas fa-th-large' },
        { id: 'favorites', name: 'Favorites',           icon: 'fas fa-star' },
        { id: 'custom',   name: 'Custom Collections',  icon: 'fas fa-folder' },
        { id: 'add',      name: 'Add Pokemon',         icon: 'fas fa-plus' }
      ],

      // Card data
      allCards: [],
      boughtCards: {},
      cardNotes: {},
      favoriteCards: {},

      // Tabs
      defaultPokemonTabs: CONFIG.DEFAULT_POKEMON.map(name => ({ name })),
      customTabs: [],

      // Collections
      customCollections: [],
      collectionCards: {},
      collectionQueries: {},
      newCollection: { name: '', description: '', type: 'manual' },

      // Add Pokemon form
      newPokemonInput: '',

      // Modal
      selectedCard: null,
      cardNoteText: '',
      noteSaved: false,

      // Search / filter state
      searchFilters: {
        query: '',
        filterValue: 'all',
        sortValue: 'printYear',
        reverseOrder: false,
        foilOnly: false,
        priceMin: '',
        priceMax: ''
      },

      // Toast notification
      notification: {
        title: '',
        message: '',
        type: 'info',
        visible: false
      }
    };
  },

  computed: {
    pokemonTabs() {
      return [...this.defaultPokemonTabs, ...this.customTabs.map(name => ({ name }))];
    },

    filteredCards() {
      const query = this.searchFilters.query.toLowerCase();
      const { filterValue, sortValue, foilOnly, reverseOrder } = this.searchFilters;
      const priceMin = parseFloat(this.searchFilters.priceMin) || 0;
      const priceMax = parseFloat(this.searchFilters.priceMax) || Infinity;

      let filtered = this.allCards.filter(card => {
        const matchesSearch =
          (card.name && card.name.toLowerCase().includes(query)) ||
          (card.set?.name && card.set.name.toLowerCase().includes(query)) ||
          (card.number && card.number.toString().includes(query)) ||
          (card.rarity && card.rarity.toLowerCase().includes(query));

        if (!matchesSearch) return false;

        if (foilOnly) {
          const isHoloRarity = card.rarity?.toLowerCase().includes('holo');
          const isHoloVariant = card.variants?.holo;
          if (!isHoloRarity && !isHoloVariant) return false;
        }

        if (priceMin > 0 || priceMax < Infinity) {
          const price = utils.getCardPrice(card);
          if (price < priceMin || price > priceMax) return false;
        }

        if (filterValue === 'bought'    && !this.boughtCards[card.id])   return false;
        if (filterValue === 'notBought' &&  this.boughtCards[card.id])   return false;
        if (filterValue === 'favorites' && !this.favoriteCards[card.id]) return false;

        return true;
      });

      filtered.sort((a, b) => {
        switch (sortValue) {
          case 'name':
            return a.name.localeCompare(b.name);
          case 'set':
            return (a.set?.name || '').localeCompare(b.set?.name || '');
          case 'number':
            return (parseInt(a.number) || 0) - (parseInt(b.number) || 0);
          case 'rarity':
            return (a.rarity || '').localeCompare(b.rarity || '');
          case 'printYear': {
            const yearA = parseInt(a.set?.releaseDate || '0', 10);
            const yearB = parseInt(b.set?.releaseDate || '0', 10);
            return yearB - yearA; // newest first
          }
          default:
            return 0;
        }
      });

      if (reverseOrder) filtered.reverse();

      return filtered;
    },

    favoriteCardsList() {
      return Object.values(this.favoriteCards).filter(v => v && typeof v === 'object');
    },

    boughtCount() {
      return Object.keys(this.boughtCards).filter(id =>
        this.allCards.some(card => card.id === id) && this.boughtCards[id]
      ).length;
    },

    favoriteCount() {
      return Object.keys(this.favoriteCards).filter(id => this.favoriteCards[id]).length;
    }
  },

  methods: {
    // -----------------------------------------------------------------------
    // Storage helpers
    // -----------------------------------------------------------------------

    async loadFromStorage() {
      try {
        if (!DBService.db) await DBService.init();

        const [boughtCards, cardNotes, favoriteCards, customTabs, customCollections, collectionCards, queryTypes] =
          await Promise.all([
            DBService.getUserData(CONFIG.LOCAL_STORAGE_KEYS.BOUGHT),
            DBService.getUserData(CONFIG.LOCAL_STORAGE_KEYS.NOTES),
            DBService.getUserData(CONFIG.LOCAL_STORAGE_KEYS.FAVORITES),
            DBService.getUserData(CONFIG.LOCAL_STORAGE_KEYS.CUSTOM_TABS),
            DBService.getUserData(CONFIG.LOCAL_STORAGE_KEYS.CUSTOM_COLLECTIONS),
            DBService.getUserData(CONFIG.LOCAL_STORAGE_KEYS.COLLECTION_CARDS),
            DBService.getUserData(CONFIG.LOCAL_STORAGE_KEYS.QUERY_TYPES)
          ]);

        // Fall back to localStorage for users upgrading from the old version
        this.boughtCards       = boughtCards       || JSON.parse(localStorage.getItem(CONFIG.LOCAL_STORAGE_KEYS.BOUGHT))              || {};
        this.cardNotes         = cardNotes         || JSON.parse(localStorage.getItem(CONFIG.LOCAL_STORAGE_KEYS.NOTES))               || {};
        this.favoriteCards     = favoriteCards     || JSON.parse(localStorage.getItem(CONFIG.LOCAL_STORAGE_KEYS.FAVORITES))           || {};
        this.customTabs        = customTabs        || JSON.parse(localStorage.getItem(CONFIG.LOCAL_STORAGE_KEYS.CUSTOM_TABS))         || [];
        this.customCollections = customCollections || JSON.parse(localStorage.getItem(CONFIG.LOCAL_STORAGE_KEYS.CUSTOM_COLLECTIONS))  || [];
        this.collectionCards   = collectionCards   || JSON.parse(localStorage.getItem(CONFIG.LOCAL_STORAGE_KEYS.COLLECTION_CARDS))    || {};
        this.collectionQueries = queryTypes || {};

        // One-time migration: if data only exists in localStorage, move it to IndexedDB
        if (!boughtCards && localStorage.getItem(CONFIG.LOCAL_STORAGE_KEYS.BOUGHT)) {
          await this.migrateDataToIndexedDB();
        }
      } catch (error) {
        console.error('Error loading from storage:', error);
        this.showNotification({
          title: 'Storage Error',
          message: 'Could not load your collection data. Using default settings.',
          type: 'error'
        });
        this.boughtCards = {};
        this.cardNotes = {};
        this.favoriteCards = {};
        this.customTabs = [];
        this.customCollections = [];
        this.collectionCards = {};
        this.collectionQueries = {};
      }
    },

    async migrateDataToIndexedDB() {
      try {
        for (const key of Object.values(CONFIG.LOCAL_STORAGE_KEYS)) {
          const raw = localStorage.getItem(key);
          if (raw) {
            await DBService.saveUserData(key, JSON.parse(raw));
          }
        }
        this.showNotification({
          title: 'Data Migrated',
          message: 'Your collection data has been upgraded to use improved storage.',
          type: 'success'
        });
      } catch (error) {
        console.error('Error migrating data to IndexedDB:', error);
      }
    },

    async saveToStorage(key, data) {
      try {
        const plainData = utils.toPlainObject(data);
        if (DBService.db) {
          await DBService.saveUserData(key, plainData);
        }
        localStorage.setItem(key, JSON.stringify(plainData));
      } catch (error) {
        console.error('Error saving to storage:', error);
        try {
          const plainData = utils.toPlainObject(data);
          localStorage.setItem(key, JSON.stringify(plainData));
        } catch (e) {
          console.error('Fatal storage error:', e);
        }
      }
    },

    // -----------------------------------------------------------------------
    // Card loading
    // -----------------------------------------------------------------------

    async loadCards(forceRefresh = false) {
      this.loading = true;
      this.errorMessage = '';

      try {
        const cards = await ApiService.fetchCards(this.currentCollection, {
          forceRefresh,
          queryType: this.currentQueryType
        });
        this.allCards = cards;
        // Lazy-migrate old boolean favorites to full card objects
        let migrated = false;
        cards.forEach(card => {
          if (this.favoriteCards[card.id] === true) {
            this.favoriteCards[card.id] = card;
            migrated = true;
          }
        });
        if (migrated) {
          await this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.FAVORITES, this.favoriteCards);
        }
      } catch (error) {
        console.error('Error fetching cards:', error);
        this.errorMessage = navigator.onLine
          ? `Failed to load cards: ${error.message}`
          : 'You are offline. Some cards may not be available.';
        this.showNotification({ title: 'Loading Error', message: error.message, type: 'error' });
      } finally {
        this.loading = false;
      }
    },

    refreshCards() {
      this.loadCards(true);
      this.showNotification({
        title: 'Refreshing Cards',
        message: 'Getting the latest data for ' + this.currentCollection,
        type: 'info'
      });
    },

    // -----------------------------------------------------------------------
    // Navigation
    // -----------------------------------------------------------------------

    changeView(viewId) {
      this.currentView = viewId;
    },

    selectCollection(collectionId, queryType = 'pokemon') {
      this.currentCollection = collectionId;
      this.currentQueryType = queryType;
      this.loadCards();
    },

    toggleAdvancedFilters() {
      this.showAdvancedFilters = !this.showAdvancedFilters;
    },

    // -----------------------------------------------------------------------
    // Card interactions
    // -----------------------------------------------------------------------

    async toggleCardBought(cardId) {
      this.boughtCards[cardId] = !this.boughtCards[cardId];
      await this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.BOUGHT, this.boughtCards);

      if (this.boughtCards[cardId]) {
        this.showNotification({
          title: 'Card Marked as Bought',
          message: 'Card has been added to your collection',
          type: 'success'
        });
      }
    },

    async toggleCardFavorite(card) {
      const cardId = card.id;
      try {
        if (this.favoriteCards[cardId]) {
          delete this.favoriteCards[cardId];
        } else {
          this.favoriteCards[cardId] = card;
        }
        await this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.FAVORITES, this.favoriteCards);

        if (this.favoriteCards[cardId]) {
          this.showNotification({
            title: 'Card Favorited',
            message: 'Card has been added to your favorites',
            type: 'success'
          });
        }
      } catch (error) {
        console.error('Error toggling favorite:', error);
        this.showNotification({
          title: 'Operation Failed',
          message: 'Could not update favorite status. Please try again.',
          type: 'error'
        });
      }
    },

    // Open modal + lazy-load pricing (Stage 2 fetch)
    async openCardModal(card) {
      this.selectedCard = card;
      this.cardNoteText = this.cardNotes[card.id] || '';
      this.noteSaved = false;

      if (!card.pricing?.loaded) {
        try {
          const detail = await ApiService.fetchCardDetail(card.id);

          const pricingData = {
            loaded: true,
            tcgplayer: detail.pricing?.tcgplayer || null,
            cardmarket: detail.pricing?.cardmarket || null
          };

          // Update allCards so the cache carries pricing after modal close
          const idx = this.allCards.findIndex(c => c.id === card.id);
          if (idx !== -1) {
            this.allCards[idx].pricing = pricingData;
            if (detail.illustrator) this.allCards[idx].illustrator = detail.illustrator;
            if (detail.description) this.allCards[idx].description = detail.description;
          }

          // Also update selectedCard reference
          if (this.selectedCard?.id === card.id) {
            this.selectedCard.pricing = pricingData;
            if (detail.illustrator) this.selectedCard.illustrator = detail.illustrator;
            if (detail.description) this.selectedCard.description = detail.description;
          }
        } catch (error) {
          console.error('Error fetching card detail:', error);
          const noData = { loaded: true, tcgplayer: null, cardmarket: null };
          const idx = this.allCards.findIndex(c => c.id === card.id);
          if (idx !== -1) this.allCards[idx].pricing = noData;
          if (this.selectedCard?.id === card.id) this.selectedCard.pricing = noData;
        }
      }
    },

    closeCardModal() {
      this.selectedCard = null;
    },

    async saveCardNote() {
      if (!this.selectedCard) return;

      this.cardNotes[this.selectedCard.id] = this.cardNoteText;
      await this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.NOTES, this.cardNotes);

      this.noteSaved = true;
      setTimeout(() => { this.noteSaved = false; }, 1500);

      this.showNotification({
        title: 'Note Saved',
        message: 'Your note has been saved for this card',
        type: 'success'
      });
    },

    // -----------------------------------------------------------------------
    // Pokemon tab management
    // -----------------------------------------------------------------------

    addNewPokemon() {
      const pokemonName = this.newPokemonInput.trim();
      if (!pokemonName) {
        this.showNotification({ title: 'Validation Error', message: 'Please enter a Pokemon name', type: 'error' });
        return;
      }

      const exists = this.pokemonTabs.some(tab => tab.name.toLowerCase() === pokemonName.toLowerCase());
      if (exists) {
        this.showNotification({ title: 'Duplicate Pokemon', message: 'This Pokemon is already in your collection!', type: 'warning' });
        return;
      }

      this.customTabs.push(pokemonName);
      this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.CUSTOM_TABS, this.customTabs);
      this.newPokemonInput = '';
      this.changeView('all');
      this.selectCollection(pokemonName.toLowerCase(), 'pokemon');

      this.showNotification({
        title: 'Pokemon Added',
        message: `${pokemonName} has been added to your collection tabs`,
        type: 'success'
      });
    },

    handleTabRemoval(pokemonName) {
      const defaultNames = this.defaultPokemonTabs.map(t => t.name.toLowerCase());
      if (defaultNames.includes(pokemonName.toLowerCase())) {
        this.showNotification({
          title: 'Cannot Remove',
          message: 'Default Pokemon cannot be removed from the collection.',
          type: 'warning'
        });
        return;
      }

      if (confirm(`Remove ${pokemonName} from your collection tabs?`)) {
        this.customTabs = this.customTabs.filter(name => name.toLowerCase() !== pokemonName.toLowerCase());
        this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.CUSTOM_TABS, this.customTabs);

        if (this.currentCollection === pokemonName.toLowerCase()) {
          this.selectCollection('charizard', 'pokemon');
        }

        this.showNotification({ title: 'Tab Removed', message: `${pokemonName} removed from collection`, type: 'success' });
      }
    },

    // -----------------------------------------------------------------------
    // Custom collections
    // -----------------------------------------------------------------------

    async saveCollection() {
      if (!this.newCollection.name.trim()) {
        this.showNotification({ title: 'Validation Error', message: 'Please enter a collection name', type: 'error' });
        return;
      }

      const collection = {
        id: 'col_' + Date.now(),
        name: this.newCollection.name.trim(),
        description: this.newCollection.description.trim(),
        type: this.newCollection.type,
        created: Date.now(),
        lastModified: Date.now()
      };

      this.customCollections.push(collection);
      await this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.CUSTOM_COLLECTIONS, this.customCollections);

      this.collectionCards[collection.id] = [];
      await this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.COLLECTION_CARDS, this.collectionCards);

      this.showCollectionForm = false;
      this.newCollection = { name: '', description: '', type: 'manual' };

      this.showNotification({
        title: 'Collection Created',
        message: `"${collection.name}" collection has been created`,
        type: 'success'
      });
    },

    getCollectionCardCount(collectionId) {
      return this.collectionCards[collectionId]?.length || 0;
    },

    viewCollection(collectionId) {
      const collection = this.customCollections.find(c => c.id === collectionId);
      if (!collection) return;
      this.showNotification({ title: 'Collection View', message: `Viewing collection: ${collection.name}`, type: 'info' });
    },

    editCollection(collectionId) {
      const collection = this.customCollections.find(c => c.id === collectionId);
      if (!collection) return;
      this.showNotification({ title: 'Edit Collection', message: `Editing collection: ${collection.name}`, type: 'info' });
    },

    async deleteCollection(collectionId) {
      const collection = this.customCollections.find(c => c.id === collectionId);
      if (!collection) return;

      if (confirm(`Are you sure you want to delete the collection "${collection.name}"?`)) {
        this.customCollections = this.customCollections.filter(c => c.id !== collectionId);
        await this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.CUSTOM_COLLECTIONS, this.customCollections);

        delete this.collectionCards[collectionId];
        await this.saveToStorage(CONFIG.LOCAL_STORAGE_KEYS.COLLECTION_CARDS, this.collectionCards);

        this.showNotification({ title: 'Collection Deleted', message: `"${collection.name}" has been deleted`, type: 'success' });
      }
    },

    // -----------------------------------------------------------------------
    // Export / Import
    // -----------------------------------------------------------------------

    async exportData() {
      try {
        if (!DBService.db) await DBService.init();
        const exportData = await DBService.exportAllData();
        utils.downloadObjectAsJson(exportData, 'pokemon-collection-export');
        this.showNotification({ title: 'Export Complete', message: 'Your collection data has been exported', type: 'success' });
      } catch (error) {
        console.error('Error exporting data:', error);
        this.showNotification({ title: 'Export Failed', message: 'Could not export data: ' + error.message, type: 'error' });
      }
    },

    async processImportedData(data) {
      try {
        if (!data?.userData || !data?.cardData) throw new Error('Invalid import data format');
        if (!DBService.db) await DBService.init();
        await DBService.importAllData(data);
        await this.loadFromStorage();
        await this.loadCards();
        this.showNotification({ title: 'Import Complete', message: 'Your collection data has been imported successfully', type: 'success' });
      } catch (error) {
        console.error('Error importing data:', error);
        this.showNotification({ title: 'Import Failed', message: 'Could not import data: ' + error.message, type: 'error' });
      }
    },

    // -----------------------------------------------------------------------
    // Notifications
    // -----------------------------------------------------------------------

    showNotification(options) {
      NotificationService.show(this, options);
    }
  },

  async mounted() {
    try {
      await DBService.init();
      LazyLoadService.init();
      OfflineService.setup(this);
      await this.loadFromStorage();
      await this.loadCards();

      // Debounced search watcher
      const debouncedSearch = utils.debounce(() => {}, CONFIG.DEBOUNCE_DELAY);
      this.$watch('searchFilters', debouncedSearch, { deep: true });
    } catch (error) {
      console.error('Error during app initialization:', error);
      this.errorMessage = 'There was a problem initializing the app. Please try reloading.';
    }
  },

  beforeUnmount() {
    DBService.closeConnection();
  }
});

app.mount('#app');
