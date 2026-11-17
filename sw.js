// عامل خدمة خفيف للتثبيت كتطبيق (يُولَّد من tools/pwa.py)
// الصفحات: من الشبكة أولاً دائماً (فلا تظهر نسخة قديمة)، ومن النسخة المحفوظة فقط عند انقطاع الاتصال.
// بقية الملفات (PDF والصور والخطوط) لا يتدخّل فيها، فتبقى كما هي مع ذاكرة المتصفح العادية.
const CACHE = "lib-pages-v1";
self.addEventListener("install", (e) => { self.skipWaiting(); });
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((ks) => Promise.all(ks.filter((k) => k.startsWith("lib-pages-") && k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  const r = e.request;
  if (r.method !== "GET" || r.mode !== "navigate") return;
  e.respondWith(fetch(r).then((res) => {
    if (res && res.ok) { const c = res.clone(); const u = new URL(r.url); u.search = ""; caches.open(CACHE).then((ca) => ca.put(u.href, c)); }
    return res;
  }).catch(() => caches.match(r, { ignoreSearch: true }).then((m) => m || caches.match(new URL("./", self.registration.scope).href))));
});
