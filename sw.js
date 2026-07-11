// CACHE wird NICHT mehr von Hand hochgezählt (v38, v39, ...) — der
// pre-commit-Hook (.git/hooks/pre-commit, siehe scripts/update_sw_cache.py)
// schreibt hier automatisch einen Hash über alle SHELL-Dateien rein, sobald
// eine davon Teil eines Commits ist. Wichtig: der Hash muss als Literal HIER
// in der Datei stehen (nicht zur Laufzeit berechnet) — Browser erkennen ein
// Service-Worker-Update ausschliesslich per Byte-Vergleich der sw.js-Datei
// selbst, nicht daran, was sie zur Laufzeit tut. Rein zur Laufzeit gehashtes
// SHELL hätte also nie ein Update ausgelöst, egal wie oft sich die
// gecachten Dateien inhaltlich ändern. Identisches Prinzip wie im
// Schwester-Repo (General), siehe dortige sw.js.
const CACHE = 'lernplan-051264075826';
const SHELL = ['./','./index.html','./manifest.json'];

self.addEventListener('install', e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', e=>{
  e.waitUntil(
    caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', e=>{
  e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});
