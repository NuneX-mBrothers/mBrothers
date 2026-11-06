/* O site da mBrothers mudou-se para https://intrepidparallel.com/mbrothers/ (06/11/2026).
   Este worker substitui o antigo nos navegadores que ja tinham visitado o GitHub Pages: apaga as caches da mBrothers
   (so as que comecam por "mbrothers-": as do EF e do LogViewer estao na mesma origem e nao se tocam), desregista-se e
   recarrega as paginas abertas, que entao reencaminham para o endereco novo. */
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.filter(function (k) { return k.indexOf('mbrothers-') === 0; })
                               .map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.registration.unregister(); })
      .then(function () { return self.clients.matchAll({ type: 'window' }); })
      .then(function (clients) { clients.forEach(function (c) { c.navigate(c.url); }); })
  );
});
