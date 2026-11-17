"""تجهيز المكتبة للتثبيت كتطبيق (PWA) على أندرويد وآيفون والكمبيوتر.
الاستخدام:  python3 tools/pwa.py        (ويُستدعى تلقائياً من آخر tools/configure.py)
يفعل:
 1) يولّد الأيقونات من شعار المكتبة بخلفية لون الهوية:
    assets/icon-192.png · assets/icon-512.png · assets/icon-maskable-512.png · assets/apple-touch-icon.png (180) · assets/favicon-32.png
 2) يكتب manifest.webmanifest (المسارات نسبية ./ لتعمل على أي مسار في GitHub Pages).
 3) يكتب sw.js (عامل خدمة خفيف: الصفحات من الشبكة أولاً، ونسخة احتياطية عند انقطاع الاتصال؛ لا يخزّن ملفات PDF).
 4) يضع وسوم التثبيت بين علامتي PWA في index.html و read.html و admin.html و fawaid.html.
"""
import json, re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.load(open(ROOT / "books.json", encoding="utf-8"))
site = data.get("site", {})
th = site.get("theme") or {}
PRIMARY, ACCENT, BG = th.get("primary", "#164e3b"), th.get("accent", "#c6a15b"), th.get("bg", "#f7f3e8")

title, author = site.get("title", "").strip(), site.get("author", "").strip()
# الاسم الكامل كما يظهر في رأس الموقع (brandTitle + brandSub)
FULL = " ".join(x for x in [(site.get("brandTitle") or title).strip(), (site.get("brandSub") or author).strip()] if x) or "المكتبة الرقمية"
def short_person(n):
    # «د. سعد بن ضيدان السبيعي» ← «د. سعد السبيعي»: اللقب + الاسم الأول + اسم العائلة فقط
    n = re.sub(r"\s+", " ", re.sub(r"أ\.\s*د\.", "أ.د.", re.sub(r"(د|أ|م)\.\s*", r"\1. ", n or ""))).strip()
    n = re.sub(r"^(مؤلفات|مكتبة|كتب)\s+", "", n)  # «مؤلفات الشيخ سلطان العمري» ← «الشيخ سلطان العمري»
    m = re.match(r"^((?:أ\.د\.|د\.|أ\.|م\.|الأستاذ الدكتور|الدكتور|الشيخ|الأستاذ|فضيلة الشيخ)\s+)?(.*)$", n)
    hon, rest = (m.group(1) or "").strip(), re.sub(r"^(عبد|أبو|أبي) (\S+)", "\\1~\\2", m.group(2)).split()
    if not rest: return n
    core = rest[0] if len(rest) == 1 else rest[0] + " " + rest[-1]
    if len(rest) >= 2 and rest[-2] in ("آل", "ابن", "بن", "أبو", "أبا", "ال"): core = rest[0] + " " + rest[-2] + " " + rest[-1]
    return (hon + " " + core).replace("~", " ").strip()
PERSON = short_person(site.get("authorName") or site.get("brandSub") or author)
# الاسم: «المكتبة الرقمية - د. سعد السبيعي» (يمكن تخصيصه بـ site.appName)
NAME = (site.get("appName") or "").strip() or ("المكتبة الرقمية - " + PERSON if PERSON else FULL)
SHORT = (site.get("appShortName") or "").strip()
if not SHORT:  # اسم قصير ≤ 12 حرفاً يظهر تحت الأيقونة
    last = (site.get("authorName") or author or NAME).split()[-1] if (site.get("authorName") or author or NAME).split() else "المكتبة"
    for cand in [PERSON, "د. " + last if re.search(r"(^|\s)(د\.|الدكتور)", PERSON) else "", "مكتبة " + last, last, "المكتبة"]:
        if cand and len(cand) <= 12: SHORT = cand; break
assert len(SHORT) <= 12, SHORT

MARK = ('<path d="M10 22c8-3.5 15-2.5 22 2.5v27c-7-5-14-6-22-2.5z M54 22c-8-3.5-15-2.5-22 2.5v27c7-5 14-6 22-2.5z" fill="{a}"/>'
        '<path d="M32 7l2.4 4.9 5.4.8-3.9 3.8.9 5.4L32 19.4l-4.8 2.5.9-5.4-3.9-3.8 5.4-.8z" fill="{b}"/>').format(a=ACCENT, b=BG)
# إن كان شعار رأس الموقع مختلفاً في هذه المكتبة نأخذه منه كما هو (بألوان الهوية)
_m = re.search(r'class="brand-mark"><svg viewBox="0 0 64 64"[^>]*>(.*?)</svg>', (ROOT / "index.html").read_text(encoding="utf-8"), re.S)
if _m:
    MARK = (_m.group(1).replace('style="fill:var(--t-accent)"', f'fill="{ACCENT}"').replace('style="fill:var(--t-bg)"', f'fill="{BG}"')
            .replace('style="fill:var(--t-primary)"', f'fill="{PRIMARY}"'))

def svg(size, scale):
    # الشعار في المنتصف؛ scale = نسبة عرض الشعار من الأيقونة (الشعار يشغل 44×45 من 64)
    s = scale * 64 / 44
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="{size}" height="{size}"><rect width="64" height="64" fill="{PRIMARY}"/>'
            f'<g transform="translate(32 32) scale({s:.4f}) translate(-32 -29.3)">{MARK}</g></svg>')

ICONS = [("icon-192.png", 192, .70), ("icon-512.png", 512, .70), ("icon-maskable-512.png", 512, .54),
         ("apple-touch-icon.png", 180, .66), ("favicon-32.png", 32, .80)]
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for fn, size, sc in ICONS:
            pg = br.new_page(viewport={"width": size, "height": size})
            pg.set_content(f'<html><body style="margin:0">{svg(size, sc)}</body></html>')
            pg.screenshot(path=str(ROOT / "assets" / fn), omit_background=False); pg.close()
        br.close()
    print("✓ الأيقونات:", ", ".join(f for f, _, _ in ICONS))
except Exception as ex:
    print("⚠ تعذّر توليد الأيقونات:", ex)

manifest = {
    "id": "./", "name": NAME, "short_name": SHORT,
    "description": site.get("shareDescription") or ("مكتبة رقمية مجانية: " + FULL + "، تُقرأ بتقليب الصفحات كالكتاب المطبوع."),
    "lang": "ar", "dir": "rtl", "start_url": "./", "scope": "./", "display": "standalone",
    "orientation": "any", "theme_color": PRIMARY, "background_color": PRIMARY, "categories": ["books", "education"],
    "icons": [
        {"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "assets/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
}
(ROOT / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("✓ manifest.webmanifest:", NAME, "|", SHORT)

(ROOT / "sw.js").write_text("""// عامل خدمة خفيف للتثبيت كتطبيق (يُولَّد من tools/pwa.py)
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
""", encoding="utf-8")
print("✓ sw.js")

app_title = SHORT
BLOCK = "\n".join([
    '<!-- PWA:START (يُولَّد تلقائياً: python3 tools/pwa.py) -->',
    '<link rel="manifest" href="manifest.webmanifest">',
    '<link rel="icon" type="image/png" sizes="32x32" href="assets/favicon-32.png">',
    '<link rel="icon" type="image/png" sizes="192x192" href="assets/icon-192.png">',
    '<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">',
    '<meta name="mobile-web-app-capable" content="yes">',
    '<meta name="apple-mobile-web-app-capable" content="yes">',
    f'<meta name="apple-mobile-web-app-title" content="{app_title}">',
    '<meta name="apple-mobile-web-app-status-bar-style" content="default">',
    '<script>if("serviceWorker" in navigator)addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){})})</script>',
    '<!-- PWA:END -->'])
OLD = [r'<link rel="apple-touch-icon"[^>]*>\n?', r'<link rel="icon" href="data:image/svg\+xml[^>]*>\n?']
for page in ["index.html", "read.html", "admin.html", "fawaid.html"]:
    p = ROOT / page
    if not p.exists(): continue
    s = p.read_text(encoding="utf-8")
    if "<!-- PWA:START" in s:
        s = re.sub(r"<!-- PWA:START.*?<!-- PWA:END -->", lambda m: BLOCK, s, flags=re.S)
    else:
        for rx in OLD: s = re.sub(rx, "", s)
        s = s.replace("</head>", BLOCK + "\n</head>", 1)
    p.write_text(s, encoding="utf-8"); print("✓ وسوم التثبيت:", page)
