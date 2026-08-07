/* ============================================================
   TalentUP Fichaje — Service Worker
   Cache-first for static assets · Network-first for API calls
   Offline fallback · Cache versioning
   ============================================================ */

const CACHE_VERSION = 'talentup-fichaje-v1';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

// App shell — core files needed offline
const APP_SHELL = [
  './',
  './index.html',
  './i18n.js',
  './src/app.js',
  './manifest.json',
  './icon-192.svg',
  './icon-512.svg',
  './offline.html'
];

// Static asset patterns (cache-first)
const STATIC_PATTERNS = [
  /\.(?:css|js|svg|png|jpg|jpeg|gif|webp|ico|woff2?|ttf|eot)$/i
];

// API patterns (network-first)
const API_PATTERNS = [
  /\/api\//i
];

/* ===== INSTALL: pre-cache app shell ===== */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

/* ===== ACTIVATE: clean up old cache versions ===== */
self.addEventListener('activate', (event) => {
  const validCaches = [STATIC_CACHE, API_CACHE, RUNTIME_CACHE];
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => !validCaches.includes(key))
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

/* ===== FETCH: route by request type ===== */
self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle GET; let the browser handle POST/PUT/DELETE/etc.
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Skip cross-origin non-https and chrome-extension requests
  if (url.protocol !== 'https:' && url.protocol !== 'http:') return;

  // --- Navigation requests: network-first, fall back to cached shell, then offline page ---
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache a fresh copy of the page in runtime cache
          const copy = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(async () => {
          // Try cached page, then cached shell, then offline page
          const cached = await caches.match(request);
          if (cached) return cached;
          const shell = await caches.match('./index.html');
          if (shell) return shell;
          const offline = await caches.match('./offline.html');
          if (offline) return offline;
          // Last resort: a minimal offline response
          return new Response(
            '<!DOCTYPE html><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TalentUP Fichaje — Sin conexión</title><body style="font-family:-apple-system,system-ui,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f5f5f7;color:#1d1d1f"><div style="text-align:center;padding:24px"><h1 style="font-size:1.25rem;margin-bottom:8px">Sin conexión</h1><p style="color:rgba(0,0,0,0.45)">Conéctate a internet para usar TalentUP Fichaje.</p></div></body>',
            { headers: { 'Content-Type': 'text/html; charset=utf-8' }, status: 503 }
          );
        })
    );
    return;
  }

  // --- API calls: network-first, fall back to cache ---
  if (API_PATTERNS.some((re) => re.test(url.pathname)) || url.pathname.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Only cache successful, non-opaque responses
          if (response.ok || response.type === 'opaque') {
            const copy = response.clone();
            caches.open(API_CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => caches.match(request).then((cached) => cached || Response.error()))
    );
    return;
  }

  // --- Static assets: cache-first, fall back to network ---
  const isStatic =
    STATIC_PATTERNS.some((re) => re.test(url.pathname)) ||
    APP_SHELL.some((shellPath) => url.pathname.endsWith(shellPath.replace('./', '/')));

  if (isStatic) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response.ok || response.type === 'opaque') {
            const copy = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        });
      })
    );
    return;
  }

  // --- Everything else: stale-while-revalidate ---
  event.respondWith(
    caches.match(request).then((cached) => {
      const fetchPromise = fetch(request)
        .then((response) => {
          if (response.ok || response.type === 'opaque') {
            const copy = response.clone();
            caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => cached || Response.error());
      return cached || fetchPromise;
    })
  );
});