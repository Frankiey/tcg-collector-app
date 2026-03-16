/**
 * components.js — Vue 3 component definitions.
 *
 * Each component uses a <template id="..."> block defined in index.html.
 * This keeps the HTML templates human-readable in one place and lets JS
 * stay purely behavioural.
 *
 * Exports:
 *   CardComponent
 *   ModalComponent
 *   NotificationComponent
 *   ImportDialogComponent
 */

import CONFIG from './config.js';
import { utils, LazyLoadService } from './utils.js';

// ---------------------------------------------------------------------------
// Card — individual card tile shown in the grid
// ---------------------------------------------------------------------------

export const CardComponent = {
  template: '#card-template',
  props: {
    card: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      imageLoading: true,
      imageObserved: false
    };
  },
  computed: {
    isBought() {
      return this.$root.boughtCards[this.card.id] || false;
    },
    isFavorite() {
      return this.$root.favoriteCards[this.card.id] || false;
    }
  },
  mounted() {
    if (!this.card.images.small) {
      this.imageLoading = false;
      return;
    }
    this.$nextTick(() => {
      if (this.$el && this.$refs.cardImage) {
        if (!('loading' in HTMLImageElement.prototype)) {
          // Browser lacks native lazy loading — use IntersectionObserver
          LazyLoadService.observe(this.$el, this);
        } else {
          this.imageObserved = true;
        }
      }
    });
  },
  beforeUnmount() {
    if (this.$el && !('loading' in HTMLImageElement.prototype)) {
      LazyLoadService.unobserve(this.$el);
    }
  },
  methods: {
    toggleBought(e) {
      e.stopPropagation();
      this.$emit('toggle-bought', this.card.id);
    },
    toggleFavorite(e) {
      e.stopPropagation();
      this.$emit('toggle-favorite', this.card);
    },
    openModal() {
      this.$emit('open-modal', this.card);
    },
    loadImage() {
      if (this.imageObserved) return;
      this.imageObserved = true;
    },
    onImageLoaded() {
      this.imageLoading = false;
    }
  }
};

// ---------------------------------------------------------------------------
// Modal — card detail overlay (opens on card click)
// ---------------------------------------------------------------------------

export const ModalComponent = {
  template: '#modal-template',
  props: {
    card: {
      type: Object,
      required: true
    },
    note: {
      type: String,
      default: ''
    },
    noteSaved: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      PRICE_LABELS: CONFIG.PRICE_LABELS
    };
  },
  mounted() {
    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', this.handleKeyDown);
  },
  beforeUnmount() {
    document.body.style.overflow = 'auto';
    window.removeEventListener('keydown', this.handleKeyDown);
  },
  methods: {
    close() {
      this.$emit('close');
    },
    save() {
      this.$emit('save-note');
    },
    handleKeyDown(e) {
      if (e.key === 'Escape') this.close();
    },
    getTypeIcon(type) {
      return utils.getTypeIcon(type);
    },
    formatPrice(price) {
      return utils.formatPrice(price);
    },
    getPriceValue(card, key) {
      return utils.getPriceValue(card, key);
    },
    /**
     * Build a Cardmarket search URL for this card.
     * Uses CM_SET_CODE map for sets where the TCGDex ID ≠ Cardmarket code.
     * Falls back to capitalising the set ID (covers TCG Pocket sets automatically).
     */
    cardmarketUrl(card) {
      const setId = card.set?.id;
      const number = card.number;
      const setCode = setId
        ? (CONFIG.CM_SET_CODE[setId] || (setId.charAt(0).toUpperCase() + setId.slice(1)))
        : null;

      if (card.name && setCode && number) {
        const paddedNumber = String(number).padStart(3, '0');
        const searchString = encodeURIComponent(`${card.name} (${setCode} ${paddedNumber})`);
        return `https://www.cardmarket.com/en/Pokemon/Products/Search?category=-1&searchString=${searchString}&searchMode=v2`;
      }

      return 'https://www.cardmarket.com/en/Pokemon/Products/Singles';
    }
  }
};

// ---------------------------------------------------------------------------
// Notification — toast overlay (bottom-right)
// ---------------------------------------------------------------------------

export const NotificationComponent = {
  template: '#notification-template',
  props: {
    title: { type: String, required: true },
    message: { type: String, required: true },
    type: {
      type: String,
      default: 'info',
      validator: (value) => ['info', 'success', 'error', 'warning'].includes(value)
    },
    visible: { type: Boolean, default: false }
  },
  methods: {
    getIcon() {
      const icons = {
        info: 'fas fa-info-circle',
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle'
      };
      return icons[this.type] || icons.info;
    }
  }
};

// ---------------------------------------------------------------------------
// ImportDialog — file picker overlay for importing JSON collection data
// ---------------------------------------------------------------------------

export const ImportDialogComponent = {
  template: '#import-dialog-template',
  data() {
    return {
      selectedFile: null,
      importError: null
    };
  },
  methods: {
    cancel() {
      this.$emit('cancel');
    },
    handleFileSelect(event) {
      this.selectedFile = event.target.files[0];
      this.importError = null;
    },
    importData() {
      if (!this.selectedFile) {
        this.importError = 'Please select a file';
        return;
      }

      const reader = new FileReader();

      reader.onload = (e) => {
        try {
          const jsonData = JSON.parse(e.target.result);
          this.$emit('import', jsonData);
          this.$emit('cancel');
        } catch (error) {
          this.importError = 'Invalid JSON file';
          console.error('Error parsing import file:', error);
        }
      };

      reader.onerror = () => {
        this.importError = 'Error reading file';
      };

      reader.readAsText(this.selectedFile);
    }
  }
};
