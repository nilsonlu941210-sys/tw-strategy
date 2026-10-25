// 網路優先：有網路就拿最新的，沒網路才用快取
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(fetch(e.request).then(r => { const c = r.clone(); caches.open('v1').then(x => x.put(e.request, c)); return r; }).catch(() => caches.match(e.request, {ignoreSearch: true})));
});
