const CACHE_NAME = 'dcc-reports-v2';
const PRECACHE_URLS = [
  '/',
  '/dashboard/',
  '/static/css/bootstrap.min.css',
  '/static/images/kplc.png',
  '/static/images/ict.png',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png',
];

// Install – pre‑cache
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        // Cache each file individually, ignoring failures
        return Promise.allSettled(
          PRECACHE_URLS.map(url =>
            cache.add(url).catch(err => {
              console.warn(`[SW] Failed to cache: ${url}`, err);
            })
          )
        );
      })
      .then(() => {
        console.log('[SW] Pre‑caching complete (some files may have been skipped).');
        return self.skipWaiting();
      })
  );
});

// Activate – clean old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME)
                  .map(name => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

// Background Sync
self.addEventListener('sync', event => {
  if (event.tag === 'sync-institutions') {
    event.waitUntil(replayQueuedRequests());
  }
});

// Fetch – network first
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  if (event.request.url.includes('/api/') ||
      event.request.url.includes('/admin/') ||
      event.request.url.includes('/accounts/')) {
    return;
  }
  event.respondWith(
    fetch(event.request)
      .then(response => {
        const responseClone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, responseClone));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

// Replay queued requests from IndexedDB
async function replayQueuedRequests() {
  const db = await openDB();
  const tx = db.transaction('pending-requests', 'readonly');
  const store = tx.objectStore('pending-requests');
  const all = await store.getAll();

  for (const item of all) {
    try {
      const response = await fetch(item.url, {
        method: 'POST',
        body: item.body,        // the FormData is stored as a Blob
        headers: item.headers,
      });
      if (response.ok) {
        // Remove the request from the queue
        const deleteTx = db.transaction('pending-requests', 'readwrite');
        await deleteTx.objectStore('pending-requests').delete(item.id);
        await deleteTx.done;
      }
    } catch (e) {
      // Will retry on next sync
    }
  }
}

function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('OfflineQueue', 1);
    request.onupgradeneeded = e => {
      e.target.result.createObjectStore('pending-requests', { keyPath: 'id', autoIncrement: true });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}