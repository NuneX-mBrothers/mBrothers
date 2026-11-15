/* 15/11/2026: o site da mBrothers passou a ser o da Intrepid Parallel, na raiz de https://intrepidparallel.com/, e o
   /mbrothers/ reencaminha para lá (301, para sempre). Este worker substitui o antigo nos navegadores que já tinham
   visitado o /mbrothers/: apaga as caches da mBrothers (só as que começam por "mbrothers-": as do EF e do LogViewer
   estão na mesma origem e não se tocam) e desregista-se.
   ⛔ Ao contrário do docs/sw.js, NÃO recarrega as páginas abertas: enquanto o /mbrothers/ ainda servir a página antiga,
      ela voltava a registar este worker, ele recarregava-a, e assim sem fim. Assim é seguro em qualquer ordem.
   ⚠ O servidor serve o /mbrothers/sw.js sem o reencaminhar (o navegador não aceita um worker que reencaminha). */
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) {
  e.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.filter(function (k) { return k.indexOf('mbrothers-') === 0; })
                               .map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.registration.unregister(); })
  );
});
