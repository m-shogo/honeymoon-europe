'use strict';
const CACHE='honeymoon-companion-20261118-v1';
const LOCAL=['./','index.html','assets/companion.css','assets/companion.js','assets/companion-core.js','assets/companion-data.json','assets/venice.jpg','assets/icon.svg','manifest.webmanifest'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(LOCAL))));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('honeymoon-companion-')&&k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET'||u.origin!==self.location.origin||!LOCAL.some(p=>new URL(p,self.registration.scope).pathname===u.pathname))return;e.respondWith((async()=>{try{const r=await fetch(e.request);if(r.ok){const c=await caches.open(CACHE);await c.put(e.request,r.clone());return r;}throw Error();}catch{const cached=await caches.match(e.request);if(cached)return cached;if(e.request.mode==='navigate')return caches.match(new URL('index.html',self.registration.scope).href);return Response.error();}})());});
