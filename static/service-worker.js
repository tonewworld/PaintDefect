self.addEventListener('install', event => {
  event.waitUntil(
    caches.open('paintdefect-v1').then(cache => cache.addAll([
      '/',
      '/templates/index.html'
    ]))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(resp => resp || fetch(event.request))
  );
});