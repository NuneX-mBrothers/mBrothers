/* mBrothers service worker — offline support without staleness.
   Strategy:
   - HTML & same-origin JS  → network-first (always fresh when online; cache is
     only a fallback). This keeps the BUILD version honest.
   - Everything else (fonts, images) → cache-first (immutable enough). */
const CACHE = 'mbrothers-v10.5';
const CORE = [
  './', './index.html', './app.js', './favicon.svg',
  './icon-192.png', './icon-512.png', './og.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const freshFirst = url.origin === location.origin &&
    (req.mode === 'navigate' || url.pathname.endsWith('.html') || url.pathname.endsWith('.js'));

  if (freshFirst) {
    e.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then((m) => m || caches.match('./index.html')))
    );
    return;
  }

  e.respondWith(
    caches.match(req).then((m) => m || fetch(req).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
      return res;
    }))
  );
});
