/**
 * db.js — IndexedDB wrapper (DBService).
 * Handles all persistent storage: card cache, user data (bought, favorites, notes, collections).
 * Falls back gracefully when IndexedDB is unavailable.
 *
 * Stores:
 *   - cards      (keyPath: id, indexes: collection, lastUpdated)
 *   - settings   (keyPath: key)  — cache metadata per collection
 *   - userData   (keyPath: key)  — user preferences, bought/favorites/notes/collections
 */

import CONFIG from './config.js';

const DBService = {
  db: null,
  connectionPromise: null,
  isConnecting: false,

  async init() {
    if (this.db && this.db.transaction) {
      return this.db;
    }

    if (this.isConnecting && this.connectionPromise) {
      return this.connectionPromise;
    }

    this.isConnecting = true;

    this.connectionPromise = new Promise((resolve, reject) => {
      try {
        const request = window.indexedDB.open(CONFIG.DB_NAME, CONFIG.DB_VERSION);

        request.onerror = (event) => {
          console.error('IndexedDB error:', event.target.error);
          this.isConnecting = false;
          reject(event.target.error);
        };

        request.onsuccess = (event) => {
          this.db = event.target.result;

          this.db.onclose = () => {
            console.log('IndexedDB connection closed unexpectedly');
            this.db = null;
            this.isConnecting = false;
          };

          this.db.onversionchange = () => {
            this.db.close();
            console.log('IndexedDB version change, connection closed');
            this.db = null;
            this.isConnecting = false;
            alert('Database updated in another tab. Please refresh this page.');
          };

          this.isConnecting = false;
          resolve(this.db);
        };

        request.onupgradeneeded = (event) => {
          const db = event.target.result;
          const oldVersion = event.oldVersion;

          // Recreate cards store on upgrade to flush old pokemontcg.io schema
          if (db.objectStoreNames.contains('cards') && oldVersion < 2) {
            db.deleteObjectStore('cards');
          }
          if (!db.objectStoreNames.contains('cards')) {
            const cardStore = db.createObjectStore('cards', { keyPath: 'id' });
            cardStore.createIndex('collection', 'collection', { unique: false });
            cardStore.createIndex('lastUpdated', 'lastUpdated', { unique: false });
          }

          if (!db.objectStoreNames.contains('settings')) {
            db.createObjectStore('settings', { keyPath: 'key' });
          }

          if (!db.objectStoreNames.contains('userData')) {
            db.createObjectStore('userData', { keyPath: 'key' });
          }
        };
      } catch (err) {
        this.isConnecting = false;
        reject(err);
      }
    });

    return this.connectionPromise;
  },

  async executeWithRetry(operation, maxRetries = 3) {
    let retries = 0;
    let lastError;

    while (retries < maxRetries) {
      try {
        await this.init();
        return await operation();
      } catch (error) {
        retries++;
        lastError = error;
        console.warn(`Database operation failed (attempt ${retries}/${maxRetries}):`, error);

        if (
          error.name === 'InvalidStateError' ||
          (error.message && error.message.includes('connection is closing'))
        ) {
          this.db = null;
          this.isConnecting = false;
          await new Promise(resolve => setTimeout(resolve, 300 * retries));
        }
      }
    }

    throw lastError || new Error('Database operation failed after multiple retries');
  },

  async saveCards(collection, cards) {
    return this.executeWithRetry(async () => {
      const tx = this.db.transaction('cards', 'readwrite');
      const store = tx.objectStore('cards');

      const txComplete = new Promise((resolve, reject) => {
        tx.oncomplete = resolve;
        tx.onerror = () => reject(tx.error);
        tx.onabort = () => reject(new Error('Transaction aborted'));
      });

      const collectionIndex = store.index('collection');
      const collectionRequest = collectionIndex.getAllKeys(collection);

      return new Promise((resolve, reject) => {
        collectionRequest.onsuccess = async (event) => {
          try {
            const existingKeys = event.target.result;

            for (const key of existingKeys) {
              store.delete(key);
            }

            const timestamp = Date.now();
            for (const card of cards) {
              card.collection = collection;
              card.lastUpdated = timestamp;
              store.put(card);
            }

            await txComplete;

            const settingsTx = this.db.transaction('settings', 'readwrite');
            const settingsStore = settingsTx.objectStore('settings');

            const settingsTxComplete = new Promise((settingsResolve, settingsReject) => {
              settingsTx.oncomplete = settingsResolve;
              settingsTx.onerror = () => settingsReject(settingsTx.error);
            });

            settingsStore.put({
              key: `collection_${collection}`,
              timestamp,
              cardsCount: cards.length
            });

            await settingsTxComplete;
            resolve();
          } catch (err) {
            reject(err);
          }
        };

        collectionRequest.onerror = (event) => reject(event.target.error);
      });
    });
  },

  async getCards(collection) {
    return this.executeWithRetry(async () => {
      const tx = this.db.transaction('cards', 'readonly');
      const store = tx.objectStore('cards');
      const index = store.index('collection');

      return new Promise((resolve, reject) => {
        const request = index.getAll(collection);
        request.onsuccess = (event) => resolve(event.target.result);
        request.onerror = (event) => reject(event.target.error);
      });
    });
  },

  async getCardMetadata(collection) {
    return this.executeWithRetry(async () => {
      const tx = this.db.transaction('settings', 'readonly');
      const store = tx.objectStore('settings');

      return new Promise((resolve, reject) => {
        const request = store.get(`collection_${collection}`);
        request.onsuccess = (event) => resolve(event.target.result || null);
        request.onerror = (event) => reject(event.target.error);
      });
    });
  },

  async saveUserData(key, data) {
    const plainData = toPlainObject(data);

    return this.executeWithRetry(async () => {
      const tx = this.db.transaction('userData', 'readwrite');
      const store = tx.objectStore('userData');

      return new Promise((resolve, reject) => {
        const request = store.put({ key, data: plainData, timestamp: Date.now() });
        request.onsuccess = () => resolve();
        request.onerror = (event) => reject(event.target.error);

        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    });
  },

  async getUserData(key) {
    return this.executeWithRetry(async () => {
      const tx = this.db.transaction('userData', 'readonly');
      const store = tx.objectStore('userData');

      return new Promise((resolve, reject) => {
        const request = store.get(key);
        request.onsuccess = (event) => {
          const result = event.target.result;
          resolve(result ? result.data : null);
        };
        request.onerror = (event) => reject(event.target.error);
      });
    });
  },

  async getAllUserData() {
    return this.executeWithRetry(async () => {
      const tx = this.db.transaction('userData', 'readonly');
      const store = tx.objectStore('userData');

      return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = (event) => {
          const dataMap = {};
          event.target.result.forEach(item => {
            dataMap[item.key] = item.data;
          });
          resolve(dataMap);
        };
        request.onerror = (event) => reject(event.target.error);
      });
    });
  },

  async exportAllData() {
    return this.executeWithRetry(async () => {
      const userData = await this.getAllUserData();
      const cardData = {};

      const tx = this.db.transaction('settings', 'readonly');
      const store = tx.objectStore('settings');

      return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = async (event) => {
          try {
            const collections = event.target.result
              .filter(item => item.key.startsWith('collection_'))
              .map(item => item.key.replace('collection_', ''));

            for (const collection of collections) {
              try {
                cardData[collection] = await this.getCards(collection);
              } catch (error) {
                console.warn(`Error getting cards for collection ${collection}:`, error);
                cardData[collection] = [];
              }
            }

            resolve({
              version: CONFIG.CACHE_VERSION,
              timestamp: Date.now(),
              userData,
              cardData
            });
          } catch (error) {
            reject(error);
          }
        };
        request.onerror = (event) => reject(event.target.error);
      });
    });
  },

  async importAllData(data) {
    if (!data || !data.userData || !data.cardData) {
      throw new Error('Invalid import data format');
    }

    for (const key of Object.keys(data.userData)) {
      await this.saveUserData(key, data.userData[key]);
    }

    for (const collection of Object.keys(data.cardData)) {
      if (data.cardData[collection].length > 0) {
        await this.saveCards(collection, data.cardData[collection]);
      }
    }

    return true;
  },

  closeConnection() {
    if (this.db) {
      try {
        this.db.close();
        console.log('Database connection closed cleanly');
      } catch (e) {
        console.error('Error closing database:', e);
      }
      this.db = null;
      this.isConnecting = false;
    }
  }
};

// Shared helper used by DBService.saveUserData — not exported publicly
function toPlainObject(obj) {
  if (obj === null || typeof obj !== 'object') return obj;
  try {
    return JSON.parse(JSON.stringify(obj));
  } catch (e) {
    console.error('Error converting reactive object to plain object:', e);
    return Array.isArray(obj) ? [...obj] : { ...obj };
  }
}

export default DBService;
