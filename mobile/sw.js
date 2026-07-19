/* ============================================================
   TalentUP Fichaje — Service Worker
   Cache-first for app shell only; /api/ requests are never cached
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

// ===== FETCH: cache-first for shell, network-only for API =====
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // API calls — network-first without caching
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request).catch(() => {
        return new Response(
          JSON.stringify({ error: 'offline', message: 'Sin conexion' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
      })
    );
    return;
  }

  // App shell & static assets — network-first, cache as fallback
  event.respondWith(
    fetch(request).then(response => {
      if (response.status === 200 && request.method === 'GET') {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
      }
      return response;
    }).catch(() => {
      return caches.match(request).then(cached => {
        if (cached) return cached;
        return new Response('Sin conexion', { status: 503, headers: { 'Content-Type': 'text/plain' } });
      });
    })
  );
});
