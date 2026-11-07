// 網路優先：有網路就拿最新的，沒網路才用快取
// v2（2026-11-07）：signals.json 一律存成同一個鍵，離線時拿到的是「最近一次」而不是最舊的一份；啟用時清掉舊快取
const CACHE = 'v2';
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const u = new URL(e.request.url); u.search = ''; const key = u.toString();
  e.respondWith(fetch(e.request, {cache: 'no-store'}).then(r => { if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put(key, c)) } return r; }).catch(() => caches.match(key)));
});
