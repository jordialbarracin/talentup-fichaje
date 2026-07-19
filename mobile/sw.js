/* ============================================================
   TalentUP Fichaje — Service Worker
   Cache-first for app shell, network-first for API calls
   ============================================================ */

const CACHE_NAME = 'talentup-fichaje-v1';
const APP_SHELL = [
  '/mobile/',
  '/mobile/index.html',
  '/mobile/manifest.json',
  '/mobile/icons/icon-192.png',
  '/mobile/icons/icon-512.png'
];

// ===== INSTALL: cache app shell =====
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(APP_SHELL);
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

// ===== ACTIVATE: clean old caches =====
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// ===== FETCH: cache-first for shell, network-first for API =====
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // API calls — network first, fall back to cached response if offline
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then(response => {
          // Cache successful API responses for offline fallback
          const clone = response.clone();
          if (response.status === 200) {
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, clone);
            });
          }
          return response;
        })
        .catch(() => {
          // Offline: return cached response if available
          return caches.match(request).then(cached => {
            return cached || new Response(
              JSON.stringify({ error: 'offline', message: 'Sin conexión' }),
              { status: 503, headers: { 'Content-Type': 'application/json' } }
            );
          });
        })
    );
    return;
  }

  // App shell & static assets — cache first
  event.respondWith(
    caches.match(request).then(cached => {
      return cached || fetch(request).then(response => {
        // Cache new static assets
        if (response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        }
        return response;
      });
    })
  );
});
