"""يجلب إحصاءات الدول من GoatCounter ويحفظها في stats.json (يُشغَّل تلقائياً من GitHub Actions)."""
import json, os, sys, urllib.request, datetime

code = json.load(open("books.json", encoding="utf-8")).get("site", {}).get("counter", "").strip()
token = os.environ.get("GOATCOUNTER_TOKEN", "").strip()
if not code or not token:
    print("لا يوجد رمز عداد أو مفتاح API — تم التخطي"); sys.exit(0)

base = code if code.startswith("http") else f"https://{code}.goatcounter.com"
end = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
qs = f"start=2026-01-01&end={end}"

import time
def get(path):
    # إعادة المحاولة 4 مرات عند انقطاع مؤقت في الشبكة أو الخادم
    for i in range(4):
        try:
            req = urllib.request.Request(f"{base}/api/v0/{path}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if i == 3: raise
            time.sleep(10 * (i + 1))

failed = []

total = 0
try:
    t = get(f"stats/total?{qs}")
    total = int(t.get("total_unique") or t.get("total") or 0)
except Exception as e:
    print("total:", e); failed.append("total")

last28 = 0
try:
    s28 = (datetime.date.today() - datetime.timedelta(days=27)).isoformat()
    t = get(f"stats/total?start={s28}&end={end}")
    last28 = int(t.get("total_unique") or t.get("total") or 0)
except Exception as e:
    print("last28:", e); failed.append("last28")

countries = []
try:
    loc = get(f"stats/locations?{qs}&limit=50")
    for s in loc.get("stats", []):
        cid = (s.get("id") or s.get("code") or "").strip()
        cnt = int(s.get("count_unique") or s.get("count") or 0)
        if cid and cnt and cid.lower() not in ("(unknown)", "unknown"):
            countries.append({"code": cid.split("-")[0].upper(), "name": s.get("name", ""), "count": cnt})
except Exception as e:
    print("locations:", e); failed.append("locations")

# عند تعذّر الجلب: نُبقي الإحصاءات السابقة كما هي ولا نُفشل المهمة (تُعاد المحاولة في الساعة التالية)
if failed:
    print("::warning::تعذّر جلب الإحصاءات مؤقتاً (" + "، ".join(failed) + ") — بقيت الإحصاءات السابقة"); sys.exit(0)

# دمج الأقاليم في دولها
merged = {}
for c in countries:
    m = merged.setdefault(c["code"], {"code": c["code"], "name": c["name"], "count": 0}); m["count"] += c["count"]
out = {"updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "total": total, "last28": last28,
       "countries": sorted(merged.values(), key=lambda x: -x["count"])}
old = None
try: old = json.load(open("stats.json", encoding="utf-8"))
except Exception: pass
if old and {k: v for k, v in old.items() if k != "updated"} == {k: v for k, v in out.items() if k != "updated"}:
    print("لا تغيير"); sys.exit(0)
json.dump(out, open("stats.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("تم التحديث:", out)
