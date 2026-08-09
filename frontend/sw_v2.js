/* ============================================================
   TalentUP Fichaje — Service Worker v2
   ----------------------------------------------------------------------------
   Design system v2: tokens de design_system.css (8 agosto 2026).
   - Cache-first para assets estaticos · Network-first para API
   - Cola offline para POST de fichajes (sincronizacion automatica)
   - Offline fallback con la paleta del design system
   - Cache versionado con bump automatico por assets del design system
   ----------------------------------------------------------------------------
   Tokens de design system usados en el fallback offline (no en runtime):
     --brand:          #FF6B35   (naranja — acento, no protagonista)
     --bg-app:         #f5f5f7   (fondo de la app)
     --bg-surface:     #ffffff   (tarjetas)
     --text-primary:   #1d1d1f   (texto principal)
     --text-secondary: #6e6e73   (texto de apoyo)
     --danger:         #FF3B30   (estados de error)
     --success:        #34C759   (fichaje confirmado)
   Principio 9.2 del doc de vision: PWA en tema claro, no hay modo oscuro.
   ============================================================ */

const CACHE_VERSION = 'talentup-fichaje-v2';
const STATIC_CACHE = `${CACHE_VERSION}-static`;
const API_CACHE = `${CACHE_VERSION}-api`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;
const OFFLINE_QUEUE_DB = 'talentup-offline-queue';
const OFFLINE_QUEUE_STORE = 'pending-clockings';

/* App shell v2 — ficheros del nuevo design system.
   design_system.css es la fuente de verdad de tokens; sin el, la PWA
   pierde coherencia visual offline. */
const APP_SHELL = [
  './',
  './index.html',
  './dashboard_structure.html',
  './i18n.js',
  './src/app.js',
  './design_system.css',
  './manifest.json',
  './manifest_v2.json',
  './icon-16.svg',
  './icon-32.svg',
  './icon-192.svg',
  './icon-512.svg',
  './icon-maskable.svg',
  './apple-touch-icon.svg',
  './shortcut-dashboard.svg',
  './shortcut-fichajes.svg',
  './shortcut-empleados.svg',
  './shortcut-incidencias.svg',
  './offline.html'
];

/* Patrones de asset estatico (cache-first). Incluye .css/.svg nuevos. */
const STATIC_PATTERNS = [
  /\.(?:css|js|svg|png|jpg|jpeg|gif|webp|ico|woff2?|ttf|eot)$/i
];

/* Patrones de API (network-first). */
const API_PATTERNS = [
  /\/api\//i
];

/* Metodos mutables que van a la cola offline si la red falla. */
const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

/* ============================================================
   IndexedDB — cola de fichajes offline
   ============================================================ */
function openQueueDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(OFFLINE_QUEUE_DB, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(OFFLINE_QUEUE_STORE)) {
        db.createObjectStore(OFFLINE_QUEUE_STORE, { keyPath: 'id', autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function enqueuePending(request) {
  try {
    const body = await request.clone().text();
    const db = await openQueueDB();
    const tx = db.transaction(OFFLINE_QUEUE_STORE, 'readwrite');
    tx.objectStore(OFFLINE_QUEUE_STORE).add({
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body,
      timestamp: Date.now()
    });
    await new Promise((res, rej) => { tx.oncomplete = res; tx.onerror = () => rej(tx.error); });
    // Avisa al cliente de que hay un fichaje en cola (badge --warning en UI).
    const clients = await self.clients.matchAll({ includeUncontrolled: true });
    clients.forEach((c) => c.postMessage({ type: 'OFFLINE_QUEUE_UPDATED', action: 'enqueue' }));
  } catch (e) {
    console.warn('[SW] No se pudo encolar el fichaje offline:', e.message);
  }
}

async function flushQueue() {
  let db;
  try {
    db = await openQueueDB();
    const tx = db.transaction(OFFLINE_QUEUE_STORE, 'readonly');
    const allReq = tx.objectStore(OFFLINE_QUEUE_STORE).getAll();
    const pending = await new Promise((res, rej) => { allReq.onsuccess = () => res(allReq.result); allReq.onerror = () => rej(allReq.error); });
    if (!pending.length) return;

    for (const item of pending) {
      try {
        const res = await fetch(item.url, {
          method: item.method,
          headers: item.headers,
          body: item.body
        });
        if (res.ok) {
          const delTx = db.transaction(OFFLINE_QUEUE_STORE, 'readwrite');
          delTx.objectStore(OFFLINE_QUEUE_STORE).delete(item.id);
          await new Promise((r) => { delTx.oncomplete = r; });
        }
      } catch (e) {
        // Red sigue caida; dejar en cola para el proximo intento.
        break;
      }
    }
    const clients = await self.clients.matchAll({ includeUncontrolled: true });
    clients.forEach((c) => c.postMessage({ type: 'OFFLINE_QUEUE_UPDATED', action: 'flush' }));
  } catch (e) {
    console.warn('[SW] flushQueue fallo:', e.message);
  } finally {
    if (db) db.close();
  }
}

/* ============================================================
   INSTALL — pre-cachear el app shell v2
   ============================================================ */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

/* ============================================================
   ACTIVATE — limpiar caches antiguas + reclamar clientes
   ============================================================ */
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
      .then(() => flushQueue())
  );
});

/* ============================================================
   FETCH — enrutado por tipo de peticion
   ============================================================ */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Solo GET se gestiona aqui; los mutables van a la cola offline.
  if (request.method !== 'GET') {
    if (MUTATING_METHODS.has(request.method) && API_PATTERNS.some((re) => re.test(url.pathname))) {
      event.respondWith(
        fetch(request).catch(async () => {
          await enqueuePending(request);
          return new Response(
            JSON.stringify({
              offline: true,
              queued: true,
              message: 'Sin conexion: fichaje guardado en cola. Se sincronizara al recuperar la red.'
            }),
            { headers: { 'Content-Type': 'application/json; charset=utf-8' }, status: 202 }
          );
        })
      );
    }
    return;
  }

  if (url.protocol !== 'https:' && url.protocol !== 'http:') return;

  // --- Navegacion: network-first -> cached -> shell -> offline ---
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(RUNTIME_CACHE).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(async () => {
          const cached = await caches.match(request);
          if (cached) return cached;
          const shell = await caches.match('./index.html');
          if (shell) return shell;
          const dashboard = await caches.match('./dashboard_structure.html');
          if (dashboard) return dashboard;
          const offline = await caches.match('./offline.html');
          if (offline) return offline;
          // Fallback inline con la paleta del design system (tokens del doc).
          return new Response(
            '<!DOCTYPE html><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#FF6B35"><title>TalentUP Fichaje — Sin conexion</title><style>body{font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0;background:#f5f5f7;color:#1d1d1f;-webkit-font-smoothing:antialiased}.card{background:#fff;border-radius:16px;padding:48px 40px;max-width:360px;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,.04),0 4px 12px rgba(0,0,0,.06)}.icon{display:inline-flex;align-items:center;justify-content:center;width:64px;height:64px;border-radius:16px;background:#FF6B35;margin-bottom:24px}h1{font-size:1.375rem;font-weight:600;letter-spacing:-0.028em;margin-bottom:8px}p{color:#6e6e73;font-size:.875rem;line-height:1.5;margin-bottom:24px}.btn{display:inline-flex;padding:10px 20px;border-radius:980px;background:#FF6B35;color:#fff;font-weight:500;font-size:.875rem;text-decoration:none}</style><body><div class="card"><div class="icon"><svg width="36" height="36" viewBox="0 0 32 32" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="13" cy="16.5" r="7"/><path d="M9.5 16.5 L12 19 L15.5 14.5"/><path d="M21.5 10 A6.5 6.5 0 0 1 21.5 23" opacity=".95"/></svg></div><h1>Sin conexion</h1><p>No hay conexion a internet. TalentUP Fichaje necesita conexion para registrar fichajes.</p><a href="./index.html" class="btn">Reintentar</a></div></body>',
            { headers: { 'Content-Type': 'text/html; charset=utf-8' }, status: 503 }
          );
        })
    );
    return;
  }

  // --- API GET: network-first, fallback a cache ---
  if (API_PATTERNS.some((re) => re.test(url.pathname)) || url.pathname.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
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

  // --- Assets estaticos: cache-first, fallback a red ---
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

  // --- Resto: stale-while-revalidate ---
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

/* ============================================================
   SYNC — Background Sync: vaciar la cola al recuperar red
   ============================================================ */
if ('sync' in self.registration) {
  self.addEventListener('sync', (event) => {
    if (event.tag === 'talentup-flush-queue') {
      event.waitUntil(flushQueue());
    }
  });
}

// Reintento manual ante reconexion (safari no soporta Background Sync).
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'FLUSH_OFFLINE_QUEUE') {
    event.waitUntil(flushQueue());
  }
});