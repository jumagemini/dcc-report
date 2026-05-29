// static/js/db-helpers.js
window.openOfflineDB = function() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('OfflineQueue', 2);  // version bumped to 2

    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('pending-requests')) {
        db.createObjectStore('pending-requests', { keyPath: 'id', autoIncrement: true });
      }
      if (!db.objectStoreNames.contains('pending-metadata')) {
        db.createObjectStore('pending-metadata', { keyPath: 'id', autoIncrement: true });
      }
    };

    request.onsuccess = async (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('pending-requests') || !db.objectStoreNames.contains('pending-metadata')) {
        db.close();
        indexedDB.deleteDatabase('OfflineQueue');
        const retryDB = await window.openOfflineDB();
        resolve(retryDB);
        return;
      }
      resolve(db);
    };

    request.onerror = (e) => reject(e.target.error);
  });
};