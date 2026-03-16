/**
 * utils.js — Shared utilities and support services.
 *
 * Exports:
 *   utils             — pure helper functions (formatting, filtering, debounce, JSON export)
 *   LazyLoadService   — IntersectionObserver-based image lazy loading
 *   NotificationService — toast notification controller
 *   OfflineService    — online/offline event wiring
 */

import CONFIG from './config.js';

// ---------------------------------------------------------------------------
// Pure utility helpers
// ---------------------------------------------------------------------------

export const utils = {
  /**
   * Returns a debounced version of `func` that delays invocation by `wait` ms.
   */
  debounce(func, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  },

  /**
   * Format a price value as a USD string, or "N/A" if unavailable.
   */
  formatPrice(price) {
    return price != null ? `$${parseFloat(price).toFixed(2)}` : 'N/A';
  },

  /**
   * Extract release year from a card (TCGDex format: "YYYY-MM-DD").
   */
  getReleaseYear(card) {
    return card.set?.releaseDate ? card.set.releaseDate.split('-')[0] : 'N/A';
  },

  /**
   * Get a TCGPlayer price value for a given key from the first available price type.
   */
  getPriceValue(card, key) {
    if (!card.pricing?.tcgplayer) return null;
    const priceType = Object.keys(card.pricing.tcgplayer)[0];
    if (!priceType || !card.pricing.tcgplayer[priceType]) return null;
    return card.pricing.tcgplayer[priceType][key] ?? null;
  },

  /**
   * Map a Pokemon type string to a Font Awesome icon name.
   */
  getTypeIcon(type) {
    return CONFIG.TYPE_ICONS[type] || CONFIG.TYPE_ICONS.default;
  },

  /**
   * Trigger a browser download of an object as a JSON file.
   */
  downloadObjectAsJson(exportObj, exportName) {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(exportObj, null, 2));
    const a = document.createElement('a');
    a.setAttribute('href', dataStr);
    a.setAttribute('download', exportName + '.json');
    document.body.appendChild(a);
    a.click();
    a.remove();
  },

  /**
   * Return the best available price for a card (used for price-range filtering).
   * Returns 0 when no pricing is loaded yet.
   */
  getCardPrice(card) {
    if (card.pricing?.tcgplayer) {
      const priceObj = Object.values(card.pricing.tcgplayer)[0];
      return priceObj?.marketPrice || priceObj?.market || priceObj?.mid || 0;
    }
    if (card.pricing?.cardmarket) {
      return card.pricing.cardmarket.avg || card.pricing.cardmarket.trend || 0;
    }
    return 0;
  },

  /**
   * Safely convert a Vue reactive object to a plain JS object for storage.
   */
  toPlainObject(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    try {
      return JSON.parse(JSON.stringify(obj));
    } catch (e) {
      console.error('Error converting reactive object to plain object:', e);
      return Array.isArray(obj) ? [...obj] : { ...obj };
    }
  }
};

// ---------------------------------------------------------------------------
// Lazy image loading via IntersectionObserver
// ---------------------------------------------------------------------------

export const LazyLoadService = {
  observer: null,

  init() {
    if (!('IntersectionObserver' in window)) return;

    this.observer = new IntersectionObserver(
      (entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const component = entry.target.__vue__;
            if (component?.loadImage) {
              component.loadImage();
              observer.unobserve(entry.target);
            }
          }
        });
      },
      {
        rootMargin: CONFIG.IMAGE_LOADING.OBSERVER_ROOT_MARGIN,
        threshold: CONFIG.IMAGE_LOADING.OBSERVER_THRESHOLD
      }
    );
  },

  observe(el, component) {
    if (this.observer) {
      el.__vue__ = component;
      this.observer.observe(el);
    }
  },

  unobserve(el) {
    if (this.observer) {
      this.observer.unobserve(el);
    }
  }
};

// ---------------------------------------------------------------------------
// Toast notification controller
// ---------------------------------------------------------------------------

export const NotificationService = {
  _timeout: null,

  /**
   * Display a toast notification on the Vue app instance.
   *
   * @param {Object} app      — Vue app instance (must have a `notification` data property)
   * @param {Object} options
   * @param {string} options.title
   * @param {string} options.message
   * @param {string} [options.type='info']  — 'info' | 'success' | 'error' | 'warning'
   * @param {number} [options.duration]     — display time in ms
   */
  show(app, { title, message, type = 'info', duration = CONFIG.NOTIFICATION_DURATION }) {
    app.notification = { title, message, type, visible: true };
    clearTimeout(this._timeout);
    this._timeout = setTimeout(() => {
      app.notification.visible = false;
    }, duration);
  }
};

// ---------------------------------------------------------------------------
// Offline/online event wiring
// ---------------------------------------------------------------------------

export const OfflineService = {
  setup(app) {
    const updateOnlineStatus = () => {
      app.isOffline = !navigator.onLine;

      if (!navigator.onLine) {
        NotificationService.show(app, {
          title: "You're offline",
          message: 'Using cached data. Some features may be limited.',
          type: 'warning',
          duration: 5000
        });
      } else {
        NotificationService.show(app, {
          title: "You're back online",
          message: 'Connected to network',
          type: 'success',
          duration: 3000
        });
      }
    };

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);

    // Set initial state
    app.isOffline = !navigator.onLine;
  }
};
