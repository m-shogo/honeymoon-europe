'use strict';
// ふたりの欧州手帖：オフライン用（scripts/build-magazine.py が生成）
const CORE = 'techo-core-63b0597d62';
const MEDIA = 'techo-media';
const CORE_URLS = ["./", "index.html", "flights.html", "day01.html", "day02.html", "day03.html", "day04.html", "day05.html", "day06.html", "day07.html", "day08.html", "day09.html", "day10.html", "day11.html", "day12.html", "day13.html", "assets/magazine.css?v=acd9d8df", "assets/magazine.js?v=26a72d9d", "manifest.webmanifest", "assets/favicon.svg", "assets/favicon-32.png", "assets/icon-180.png", "assets/icon-192.png", "assets/icon-512.png"];
const MEDIA_HOSTS = ['upload.wikimedia.org', 'fonts.googleapis.com', 'fonts.gstatic.com'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CORE).then(c => c.addAll(CORE_URLS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('techo-core-') && k !== CORE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (MEDIA_HOSTS.includes(url.hostname)) {
    e.respondWith((async () => {
      const cache = await caches.open(MEDIA);
      const hit = await cache.match(req.url);
      if (hit) return hit;
      try {
        const res = await fetch(req.url, { mode: 'cors', credentials: 'omit' });
        if (res.ok) cache.put(req.url, res.clone());
        return res;
      } catch (err) { return fetch(req); }
    })());
    return;
  }
  if (url.origin !== self.location.origin || !url.pathname.startsWith(new URL(self.registration.scope).pathname)) return;
  e.respondWith((async () => {
    const cache = await caches.open(CORE);
    try {
      const res = await Promise.race([fetch(req), new Promise((_, rej) => setTimeout(() => rej(new Error('slow')), 4000))]);
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    } catch (err) {
      const hit = await cache.match(req, { ignoreSearch: req.mode === 'navigate' }) || await cache.match(req.url.split('#')[0]);
      if (hit) return hit;
      if (req.mode === 'navigate') return cache.match('index.html');
      throw err;
    }
  })());
});
