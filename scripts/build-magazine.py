#!/usr/bin/env python3
"""旅行雑誌ページ magazine/ を生成する（標準ライブラリのみ）。

正本:
  - 本文・行程         scripts/magazine_content.py
  - スポットの料金等   assets/companion-data.json（001〜086）, data/shopping-additions-087-093.json
  - 写真クレジット     data/photo-credits-001-061.csv, data/expansion-places.json, data/shopping-photo-credits.json
写真はWikimedia Commonsの画像を直接参照する（リポジトリに画像を増やさない）。
  追加の写真（移動・料理・お土産・コラージュ）は data/magazine-photo-candidates.json と data/magazine-photos.json（選定）から。

  python3 scripts/build-magazine.py
"""
import csv
import datetime as dt
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "magazine"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from magazine_content import DAYS, FLIGHTS  # noqa: E402

BUILT = "2026-11-24"
# 版：1/31出発（magazine/）と2/1出発（magazine/feb01/）。ED は今作っている版。
EDITIONS = {"0131": {"key": "0131", "root": "", "prefix": "", "sub": "", "label": "1/31（日）出発",
                     "note": "貼り付けた表の曜日（1/31が金曜など）は2025年の暦。2027年は1/31が日曜。表の注意書き（2/7日曜はボケリア休み、火曜はルーブル休館）は2027年の曜日と一致するので、2027年の曜日で組んでいる。"},
            "0201": {"key": "0201", "root": "../", "prefix": "feb01-", "sub": "feb01/", "label": "2/1（月）出発", "note": ""}}
ED = EDITIONS["0131"]
WEEK_JA = "月火水木金土日"
WEEK_EN = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

CITY = {
    "venice": ("ヴェネツィア", 45.434, 12.338, 1),
    "rome": ("ローマ", 41.9028, 12.4964, 1),
    "barcelona": ("バルセロナ", 41.3874, 2.1686, 1),
    "paris": ("パリ", 48.8566, 2.3522, 1),
    "normandy": ("モンサンミッシェル", 48.636, -1.511, 1),
    "sky": ("東京", 35.549, 139.78, 9),
}
THEME_COLOR = {"venice": "#0d5559", "rome": "#9c4226", "barcelona": "#1c4a94",
               "paris": "#1d2a47", "normandy": "#44545b", "sky": "#13254a"}

e = lambda s: html.escape(str(s or ""), quote=True)


# ------------------------------------------------------------------ データ読み込み
def load_spots():
    spots = {}
    for s in json.loads((ROOT / "assets/companion-data.json").read_text())["spots"]:
        spots[s["id"]] = dict(s, local=s.get("query", "").split(",")[0])
    for s in json.loads((ROOT / "data/shopping-additions-087-093.json").read_text()):
        spots[s["id"]] = dict(s, local=s.get("localName") or s["name"])
    # 063 ゴンドラは旅手帖データに無いため、料金調査（spot-prices）から補う
    prices = {p["id"]: p for p in json.loads((ROOT / "data/spot-prices-2027-af-jan31.json").read_text())["spots"]}
    g = prices.get("063")
    if g and "063" not in spots:
        spots["063"] = {"id": "063", "name": "ゴンドラ乗船（30分）", "local": "Gondola", "category": "体験", "priority": "★★★",
                        "fee": g["notes"], "duration": "30分", "official": g["sourceUrl"],
                        "caution": "強風・増水・悪天候で中止あり", "query": "Gondola, Venezia",
                        "summary": "ユーザー希望（時間が合えば）。リポジトリの予算に計上済み。", "checked": "2026-11-23"}
    # 旅手帖データの注意書きには別案（2/1出発）の日付が入っているため、この13日間の曜日に合わせて上書き
    overrides = {
        "001": {"caution": "特別行事で時間変更あり。2/6（土）は冬季の通常時間（月〜土9–18）の曜日"},
        "005": {"caution": "最終入場 平日17:45／土日16:30。日曜は午後のみ"},
        "009": {"caution": "日曜休み（2/7）。2/5（金）・2/6（土）・2/8（月）は営業曜日"},
        "017": {"caution": "近接エリアは時間・曜日で開始時刻に差（公式掲載）。清掃等で変更。現地支払いはカード"},
        "032": {"caution": "2027年公式カレンダーで2/7（日）・2/11（木）休館を確認。2/4（木）は通常の開館曜日（念のため再確認）"},
        "043": {"caution": "日・月休み。2/2（火）は営業曜日"},
        "048": {"caution": "日付・時刻枠を公式で選んで購入。具体的な時刻枠は未取得", "hours": "訪問日の詳細営業時間は公式カレンダーで確認"},
        "052": {"caution": "火曜・1/1・5/1・12/25休館。2/10（水）は夜21時まで開く曜日（公式掲載）"},
    }
    for sid, o in overrides.items():
        if sid in spots:
            spots[sid].update(o)
    return spots


def use_edition(key):
    """版を切り替える（本文・便・予約の規則・スポットの注意書きを差し替え）。"""
    global ED, OUT_DIR
    ED = EDITIONS[key]
    OUT_DIR = OUT / ED["sub"] if ED["sub"] else OUT
    if key == "0201":
        import magazine_edition_0201 as E2
        globals().update(E2.build())
        for sid, cau in E2.SPOT_CAUTIONS.items():
            SPOTS[sid]["caution"] = cau
        EDITIONS["0201"]["note"] = E2.WEEKDAY_NOTE


def wm(url, width):
    """Commonsのサムネイルを指定幅（標準サイズ）に。"""
    url = url.split("?")[0].replace("//thumb.wikimedia.org/", "//upload.wikimedia.org/")
    return re.sub(r"/\d+px-", f"/{width}px-", url)


def load_photos():
    photos = {}
    with open(ROOT / "data/photo-credits-001-061.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if "要確認" in r["license"] or "commons.wikimedia.org" not in r["source_url"]:
                continue  # 再利用条件が未確認の写真は載せない
            photos[r["no"]] = r
    # 041 は Tripadvisor画像のため、Commonsの写真（旧Myマップ作業で確認済み）に差し替え
    photos["041"] = {
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/03/Venezia_-_Merceria_dell%27Orologio_from_above.jpg/1280px-Venezia_-_Merceria_dell%27Orologio_from_above.jpg",
        "source_url": "https://commons.wikimedia.org/wiki/File:Venezia_-_Merceria_dell%27Orologio_from_above.jpg",
        "author": "Mark Longair", "license": "CC BY-SA 2.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/2.0"}
    for r in json.loads((ROOT / "data/expansion-places.json").read_text()):
        if r.get("image_url"):
            photos[r["no"]] = r
    for r in json.loads((ROOT / "data/shopping-photo-credits.json").read_text()):
        photos[r["id"]] = r
    return photos


SPOTS = load_spots()
PHOTOS = load_photos()


# ------------------------------------------------------------------ 計算
def sun_times(date, lat, lon, tz):
    """NOAAの簡易式による日の出・日の入り（現地時刻）。"""
    n = date.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    ha = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(math.radians(lat)) * math.cos(decl))
                                - math.tan(math.radians(lat)) * math.tan(decl)))
    rise = 720 - 4 * (lon + ha) - eqt + tz * 60
    sset = 720 - 4 * (lon - ha) - eqt + tz * 60
    return rise, sset


def hm(m):
    m = round(m)
    return f"{m // 60:02d}:{m % 60:02d}"


def flight_minutes(f):
    d = dt.datetime.strptime(f["dep"], "%Y-%m-%d %H:%M") - dt.timedelta(hours=f["tz"][0])
    a = dt.datetime.strptime(f["arr"], "%Y-%m-%d %H:%M") - dt.timedelta(hours=f["tz"][1])
    return int((a - d).total_seconds() // 60)


def date_of(day):
    return dt.date.fromisoformat(day["date"])


# ------------------------------------------------------------------ 部品
ICONS = {
    "plane": '<path d="M2 13l8-2V5.5a2 2 0 014 0V11l8 2v2l-8-1.5V18l2.5 2v1.5L12 20.5 7.5 21.5V20l2.5-2v-4.5L2 15z" fill="currentColor"/>',
    "train": '<rect x="5" y="3" width="14" height="14" rx="3" fill="none" stroke="currentColor" stroke-width="2"/><path d="M5 11h14M9 17l-3 4M15 17l3 4" stroke="currentColor" stroke-width="2" fill="none"/><circle cx="9" cy="14" r="1" fill="currentColor"/><circle cx="15" cy="14" r="1" fill="currentColor"/>',
    "bus": '<rect x="4" y="3" width="16" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="2"/><path d="M4 11h16M7 18v3M17 18v3" stroke="currentColor" stroke-width="2"/>',
    "metro": '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M7.5 16V8l4.5 6 4.5-6v8" fill="none" stroke="currentColor" stroke-width="2"/>',
    "boat": '<path d="M3 15c3 3 15 3 18 0l-2-5H5z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 10V3l5 5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M2 20c2 1 4 1 6 0s4-1 6 0 4 1 6 0" fill="none" stroke="currentColor" stroke-width="1.5"/>',
    "walk": '<circle cx="13" cy="4" r="2" fill="currentColor"/><path d="M10 21l2-7 3 3v5M9 12l1-4 4 1 2 4 3 1M12 14l-1-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "sight": '<path d="M3 20h18M5 20V10M9 20V10M15 20V10M19 20V10M3 10l9-6 9 6z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>',
    "food": '<path d="M7 3v8M5 3v5a2 2 0 004 0V3M7 11v10M17 3c-2 2-2 6 0 8v10" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>',
    "shop": '<path d="M5 8h14l-1 13H6z" fill="none" stroke="currentColor" stroke-width="2"/><path d="M9 10V6a3 3 0 016 0v4" fill="none" stroke="currentColor" stroke-width="2"/>',
    "hotel": '<path d="M3 20V6M3 14h18v6M21 14v-3a3 3 0 00-3-3h-7v6" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="7" cy="11" r="2" fill="currentColor"/>',
    "night": '<path d="M20 15A8 8 0 019 4a8 8 0 1011 11z" fill="none" stroke="currentColor" stroke-width="2"/>',
}


def icon(kind):
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{ICONS.get(kind, ICONS["sight"])}</svg>'


# ------------------------------------------------------------------ 写真
from magazine_content import (TL_PHOTOS, HIGHLIGHT, PHRASES, DAY_LANG, DAY_LANG_NOTE, DAY_PHRASE_FOCUS,  # noqa: E402
                              BOOKING_RULES, MANUAL_BOOKINGS, HOTEL_CITY, PHOTO_SPOTS, RETURN_PACKING, EMERGENCY_LINKS)

KIND_LABEL = {"plane": "FLIGHT", "train": "TRAIN", "bus": "BUS", "metro": "METRO", "boat": "BOAT",
              "walk": "WALK", "sight": "SIGHT", "food": "EAT", "shop": "SHOP", "hotel": "HOTEL", "night": "NIGHT"}
MOVE_KINDS = {"plane", "train", "bus", "metro", "boat"}
HERO_FALLBACK = {1: "p:af-777", 13: "p:tokyo-night"}


def load_extra_photos():
    cand_path = ROOT / "data/magazine-photo-candidates.json"
    pick_path = ROOT / "data/magazine-photos.json"
    cand = json.loads(cand_path.read_text()) if cand_path.exists() else {}
    picks = json.loads(pick_path.read_text()).get("picks", {}) if pick_path.exists() else {}
    out = {}
    for k, v in cand.items():
        items = v.get("items") or []
        p = picks.get(k, 0)
        if p is None or p == "skip" or not items:
            continue
        it = items[p] if isinstance(p, int) and p < len(items) else next((x for x in items if x["title"] == p), None)
        if it:
            out[k] = {"image_url": it["thumb"], "source_url": it["source_url"], "author": it["author"],
                      "license": it["license"], "license_url": it.get("license_url", "")}
    return out


PHOTOS.update(load_extra_photos())


def load_dinners():
    """記念日ディナー候補（リポジトリの生活スポット記録）をスポット・写真として追加。"""
    out = []
    for x in json.loads((ROOT / "data/map-amenities.json").read_text())["places"]:
        if x.get("type") != "記念日ディナー候補":
            continue
        sid = "d-" + x["id"].split("-")[-1]
        book = next((u for u in x.get("extraSources", []) if "zenchef" in u or "reserver" in u), x.get("source"))
        SPOTS[sid] = {"id": sid, "name": x["name"].split("｜")[-1], "local": x["address"].split(",")[0],
                      "category": "記念日ディナー", "priority": "★★★", "fee": x.get("fee"), "hours": x.get("hours"),
                      "caution": "服装：" + (x.get("dress") or "予約時に確認"), "summary": (x.get("note") or "").split("。")[0] + "。",
                      "official": book, "booking": "🎟 予約：" + (x.get("booking") or ""), "coords": x.get("coords"),
                      "checked": x.get("checked"), "nearby": x.get("nearby"), "query": x.get("query"), "menu": x.get("source")}
        ph = x.get("photo") or {}
        if ph.get("imageUrl"):
            PHOTOS[sid] = {"image_url": ph["imageUrl"], "source_url": ph["source"], "author": ph.get("author", ""),
                           "license": ph.get("license", ""), "license_url": ph.get("licenseUrl", "")}
        out.append(sid)
    return out


DINNERS = load_dinners()


def pinfo(key):
    """スポットID・写真キーから写真情報を返す。"""
    return PHOTOS.get(key) if key else None


def purl(key, width=960):
    p = pinfo(key)
    return wm(p["image_url"], width) if p else None


def credit(key, short=False):
    p = pinfo(key)
    if not p:
        return ""
    author = re.sub(r"\s*\[\d+\]", "", p.get("author") or "")
    author = author if len(author) < 40 else author[:38] + "…"
    lic = e(p["license"])
    if short:
        return f'<a href="{e(p["source_url"])}" target="_blank" rel="noopener">© {e(author)} / {lic}</a>'
    licl = f'<a href="{e(p["license_url"])}" target="_blank" rel="noopener">{lic}</a>' if p.get("license_url") else lic
    return f'<a href="{e(p["source_url"])}" target="_blank" rel="noopener">{e(author)}</a> / {licl}（Wikimedia Commons）'


def img(key, width, alt, cls="ph", eager=False, cap=True):
    u = purl(key, width)
    if not u:
        return f'<figure class="{cls} none"></figure>'
    load = "" if eager else ' loading="lazy"'
    fc = f"<figcaption>{credit(key, True)}</figcaption>" if cap else ""
    return f'<figure class="{cls}"><img src="{e(u)}" alt="{e(alt)}"{load} decoding="async">{fc}</figure>'


def tl_photo_key(day_n, t, sid):
    if sid and pinfo(sid):
        return sid
    if sid and pinfo(f"x:{sid}:1"):
        return f"x:{sid}:1"
    return TL_PHOTOS.get((day_n, t))


def parse_film(text):
    works, cur = [], None
    for line in (text or "").splitlines():
        line = line.strip()
        if line.startswith("作品："):
            cur = {"work": line[3:]}
            works.append(cur)
        elif cur is not None and "：" in line:
            k, v = line.split("：", 1)
            if k in ("関係", "場面", "出典"):
                cur[k] = v
    return works


def booking_lines(s):
    out = []
    for line in (s.get("booking") or "").splitlines():
        line = line.strip()
        if line.startswith("🎟"):
            out.append(("予約", line.replace("🎟 予約：", "")))
        elif line[:1] in "☔🌦🌤":
            out.append(("天気", line))
    return out


def maps_link(s):
    if s.get("coords"):
        la, lo = s["coords"]
        return f"https://www.google.com/maps/search/?api=1&query={la},{lo}"
    from urllib.parse import quote
    return "https://www.google.com/maps/search/?api=1&query=" + quote(s.get("query") or s["name"])


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Anton&family=Caveat:wght@600;700'
         '&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=Zen+Maru+Gothic:wght@500;700;900&display=swap" rel="stylesheet">')

DAY_COLOR = {"venice": "#0d7480", "rome": "#c4502f", "barcelona": "#1f56c6", "paris": "#283a6b", "normandy": "#3f6577", "sky": "#18306b"}


def asset_v(name):
    import hashlib
    return hashlib.sha1((OUT / "assets" / name).read_bytes()).hexdigest()[:8]


CSS_V, JS_V = asset_v("magazine.css"), asset_v("magazine.js")


def head(title, desc, theme):
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="{DAY_COLOR.get(theme, '#18306b')}">
<title>{e(title)}</title>
{FONTS}
<link rel="stylesheet" href="{ED['root']}assets/magazine.css?v={CSS_V}">
<link rel="icon" href="{ED['root']}assets/favicon.svg" type="image/svg+xml">
<link rel="icon" href="{ED['root']}assets/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{ED['root']}assets/icon-180.png">
<link rel="manifest" href="{ED['root']}manifest.webmanifest">
<meta name="apple-mobile-web-app-title" content="欧州手帖">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
</head>
"""


def edition_switch(current):
    file = f"day{current:02d}.html" if isinstance(current, int) else f"{current}.html"
    other = EDITIONS["0201" if ED["key"] == "0131" else "0131"]
    href = ("feb01/" if ED["key"] == "0131" else "../") + file
    return f'<a class="edsw-mini" href="{href}" data-edition-switch="{other["key"]}" title="{e(other["label"])}の版へ">{ED["label"].split("（")[0]}出発 ⇄</a>'


def mast(current):
    links = []
    for d in DAYS:
        cur = ' aria-current="page"' if current == d["n"] else ""
        dd = date_of(d)
        links.append(f'<a href="day{d["n"]:02d}.html"{cur} style="--dc:{DAY_COLOR[d["theme"]]}" title="DAY {d["n"]} {dd.month}/{dd.day} {e(d["place"])}">{d["n"]:02d}</a>')
    cur = ' aria-current="page"' if current == "flights" else ""
    links.append(f'<a href="flights.html"{cur} style="--dc:#ef4f3b" title="空の旅">✈</a>')
    return f"""<header class="mast"><div class="mast__in">
<a class="mast__logo" href="index.html"><i>♡</i><span>ふたりの欧州手帖</span></a>
{edition_switch(current)}
<a class="today" href="day01.html" data-today data-start="{DAYS[0]['date']}" data-days="{len(DAYS)}" hidden>今日</a>
<nav class="days" aria-label="日付">{''.join(links)}</nav>
</div></header>"""


def sky_svg(seed=0):
    stars = []
    for i in range(80):
        x = (i * 137.5 + seed * 31) % 1200
        y = (i * 71.3 + seed * 17) % 560
        r = 0.6 + (i % 5) * 0.4
        stars.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#fff" opacity="{0.25 + (i % 4) * 0.18:.2f}"/>')
    return f"""<svg viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
<defs><linearGradient id="sk" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0b1838"/><stop offset=".6" stop-color="#25407e"/><stop offset="1" stop-color="#f08a5d"/></linearGradient></defs>
<rect width="1200" height="800" fill="url(#sk)"/>{''.join(stars)}
<path d="M-40 640 C 300 420, 760 300, 1240 120" fill="none" stroke="#ffd23f" stroke-width="2.5" stroke-dasharray="3 12" stroke-linecap="round"/>
</svg>"""


def section(title, en, inner, sub="", sid=""):
    idattr = f' id="{sid}"' if sid else ""
    s = f'<span class="sec__sub">{e(sub)}</span>' if sub else ""
    return (f'<section class="sec"{idattr}><div class="sec__head"><span class="sec__en">{e(en)}</span>'
            f'<h2 class="sec__title">{title}</h2>{s}</div>{inner}</section>')


# ------------------------------------------------------------------ 日別ページ
MAP_MID = "1gKS7F8p3_YdS952P8K2jDE28-1epSAM"  # 作成済みのMy Maps（README記載、公開表示）
MAP_VIEW = {"venice": (45.4371, 12.3326, 14), "rome": (41.8986, 12.4769, 14), "barcelona": (41.3926, 2.1700, 14),
            "paris": (48.8606, 2.3376, 13), "normandy": (48.6361, -1.5115, 15), "sky": (45.0, 7.0, 5)}


def map_html(theme, height=460, label=""):
    la, lo, z = MAP_VIEW[theme]
    src = f"https://www.google.com/maps/d/embed?mid={MAP_MID}&ll={la},{lo}&z={z}"
    big = f"https://www.google.com/maps/d/viewer?mid={MAP_MID}&ll={la},{lo}&z={z}"
    return (f'<div class="map"><iframe src="{e(src)}" loading="lazy" title="{e(label or "My Maps")}" style="height:{height}px" referrerpolicy="no-referrer-when-downgrade"></iframe></div>'
            f'<div class="map__foot"><span>📍 作成済みのMy Maps（観光・食事・お土産・トイレなどのピン）。ピンをタップすると写真と情報。</span>'
            f'<a class="btn" href="{e(big)}" target="_blank" rel="noopener">大きな地図で開く ↗</a></div>')


def spot_badges(s):
    out = []
    films = parse_film(s.get("film"))
    if s.get("official") and dict(booking_lines(s)).get("予約"):
        out.append('<span class="badge book">🎟 予約</span>')
    fee = s.get("fee") or ""
    if fee.startswith("外") or "外観無料" in fee:
        out.append('<span class="badge free">外から無料</span>')
    elif "無料" in fee and "有料" not in fee:
        out.append('<span class="badge free">入場無料</span>')
    if films:
        out.append('<span class="badge film">🎬 聖地</span>')
    return out


def spot_detail(sid, f):
    """アコーディオンを開いたときの中身（写真コラージュ・歴史・映画・メモ・情報）。"""
    s = SPOTS[sid]
    keys = [k for k in [sid, f"x:{sid}:1", f"x:{sid}:2"] if pinfo(k)]
    n = len(keys)
    cls = "collage" + ("" if n >= 3 else f" n{max(n, 1)}")
    figs = "".join(img(k, 1280 if j == 0 else 960, s["name"]) for j, k in enumerate(keys))
    left = [f'<div class="det__name"><b>{e(s["name"])}</b><span class="stars">{e(s.get("priority", ""))}</span><span class="det__en">{e(s["local"])}</span></div>']
    if s.get("summary"):
        left.append(f'<p class="feat__summary">{e(s["summary"])}</p>')
    if f.get("history"):
        left.append(f'<div class="history"><p>{e(f["history"])}</p></div>')
    for w in parse_film(s.get("film")):
        src = f' <a href="{e(w["出典"].split(" | ")[0])}" target="_blank" rel="noopener">出典↗</a>' if w.get("出典") else ""
        left.append(f'<div class="cine"><b>{e(w["work"])}</b><small>{e(w.get("関係", ""))}</small><br>{e(w.get("場面", ""))}{src}</div>')
    if f.get("tip"):
        left.append(f'<p class="note"><span class="hand">For two ♡</span>{e(f["tip"])}</p>')
    rows = [("料金", s.get("fee")), ("時間", s.get("hours")), ("滞在", s.get("duration")), ("注意", s.get("caution"))]
    rows += booking_lines(s)
    rows += [("近く", s.get("nearby")), ("食べる", s.get("food")), ("買う", s.get("souvenir"))]
    dl = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in rows if v)
    btns = [f'<a class="btn" href="{e(maps_link(s))}" target="_blank" rel="noopener">📍 Googleマップ</a>']
    if s.get("official"):
        btns.append(f'<a class="btn main" href="{e(s["official"])}" target="_blank" rel="noopener">公式・予約 ↗</a>')
    right = f'<dl class="info">{dl}</dl><div class="btns">{"".join(btns)}</div>'
    if s.get("checked"):
        right += f'<p class="checked">料金・時間の確認日：{e(s["checked"])}（2027年の訪問日に再確認）</p>'
    if s.get("menu"):
        right = right.replace('<div class="btns">', f'<div class="btns"><a class="btn" href="{e(s["menu"])}" target="_blank" rel="noopener">🍽 メニュー（公式）</a>', 1)
    col = f'<div class="{cls}">{figs}</div>' if figs else ""
    alts = ""
    if sid in DINNERS:
        others = [x for x in DINNERS if x != sid]
        alts = (f'<div class="alts"><h4>🥂 ほかの記念日ディナー候補</h4><div class="cards">{"".join(scard_html(x) for x in others)}</div>'
                '<p class="checked">料金は2026年11月の公式メニュー。2027年の価格・コース・空席は予約時に確認。</p></div>')
    return f'{col}<div class="feat__grid"><div>{"".join(left)}</div><div>{right}</div></div>{alts}'


def plain_detail(k, title, note):
    return (f'<div class="collage n1 small">{img(k, 1280, title)}</div>' if k and pinfo(k) else "") + \
           (f'<p class="feat__summary" style="margin-top:14px">{e(note)}</p>' if note else "")


def panel(pid, icon_, title, en, inner, count="", open_=False):
    c = f'<small>{e(count)}</small>' if count else ""
    return (f'<details class="panel" id="{pid}"{" open" if open_ else ""}><summary class="panel__head">'
            f'<span class="panel__ic">{icon_}</span><span class="panel__t"><b>{title}</b><em>{e(en)}</em></span>{c}<span class="chev" aria-hidden="true"></span></summary>'
            f'<div class="panel__body">{inner}</div></details>')


NOBOOK = ("予約不要", "対象外", "店舗別", "飲食店ごと", "個別確認")


def bookable(sid):
    """予約・チケットの対象か（予約不要の街歩き・市場などは除く）。"""
    if sid in BOOKING_RULES:
        return True
    if sid in ("062",):  # 真実の口は前売り制度なし（任意の寄付）
        return False
    s = SPOTS.get(sid) or {}
    b = dict(booking_lines(s)).get("予約") or ""
    return bool(s.get("official") and b and not any(w in b for w in NOBOOK))


def booking_open(sid, visit):
    rule = BOOKING_RULES.get(sid)
    if rule and rule[0]:
        return visit - dt.timedelta(days=rule[0])
    return None


def dist_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


CITY_NAMES = {"venice": "ヴェネツィア", "rome": "ローマ", "barcelona": "バルセロナ", "paris": "パリ"}
CITY_LANG = {"venice": "it", "rome": "it", "barcelona": "es", "paris": "fr"}


def hotel_phrase(city):
    L = PHRASES[CITY_LANG[city]]
    row = next(r for r in L["rows"] if r[1].startswith("このホテルまで"))
    return row[2], row[4], L["lang"]


def hotel_chip(n, day):
    city = HOTEL_CITY.get(n)
    if not city:
        return f'<div class="chip"><small>🛏 宿泊</small><b>{e(day["stay"])}</b></div>'
    loc, en, lang = hotel_phrase(city)
    return (f'<button type="button" class="chip chip--hotel" data-hotel="{city}" data-city-name="{CITY_NAMES[city]}" '
            f'data-phrase="{e(loc)}" data-phrase-en="{e(en)}" data-lang="{lang}"><small>🛏 {e(day["stay"])}</small>'
            f'<b data-hotel-label>ホテルを登録する</b><em>タップで住所カード（タクシーで見せる）</em></button>')


HOTEL_DIALOG = """<dialog class="hdlg" id="hotel-dlg" aria-label="ホテル住所カード">
<div class="hdlg__view">
<p class="hdlg__city" data-v="city"></p>
<p class="hdlg__phrase" data-v="phrase"></p><p class="hdlg__en" data-v="phrase-en"></p>
<p class="hdlg__name" data-v="name"></p><p class="hdlg__addr" data-v="addr"></p><p class="hdlg__tel" data-v="tel"></p>
<div class="hdlg__btns"><a class="btn" data-v="map" target="_blank" rel="noopener">📍 Googleマップで開く</a><button type="button" class="btn" data-hd="edit">✏️ 編集</button><button type="button" class="btn main" data-hd="close">閉じる</button></div>
</div>
<form class="hdlg__edit" method="dialog">
<h3>🏨 <span data-v="city2"></span>のホテル</h3>
<label>ホテル名<input name="name" autocomplete="off" placeholder="例：Hotel ○○"></label>
<label>住所（現地の表記で）<textarea name="addr" rows="3" placeholder="例：Calle ○○ 12, 30121 Venezia"></textarea></label>
<label>電話（任意）<input name="tel" inputmode="tel" autocomplete="off" placeholder="+39 ..."></label>
<p class="hdlg__note">この端末のブラウザにだけ保存されます。予約番号やパスポート番号は入れないでください。</p>
<div class="hdlg__btns"><button type="button" class="btn" data-hd="close">やめる</button><button type="button" class="btn main" data-hd="save">保存して表示</button></div>
</form>
</dialog>"""


HOURS = json.loads((ROOT / "data/opening-hours-2027.json").read_text())


def _mins(t):
    h_, m_ = t.split(":")
    return int(h_) * 60 + int(m_)


def hours_on(sid, d):
    """その日の営業 [開く, 閉まる, 最終入場] と規則。休みなら値は None。規則がなければ (None, None)。"""
    r = HOURS["spots"].get(sid)
    if not r:
        return None, None
    v = r.get("dates", {}).get(d.isoformat(), r["week"][d.weekday()])
    return r, v


def hours_text(v):
    if not v:
        return "休み"
    o, c, last = v
    c = "24:00" if c == "23:59" else c
    return f"{o}–{c}" + (f"・最終{last}" if last else "")


def check_item(t, kind, sid, d):
    """予定の時刻と営業時間を照らす。(状態, ひとこと) 状態は ok / warn / ng。外から眺める予定（walk）は照らさない。"""
    r, v = hours_on(sid, d)
    if not r or kind in ("walk",) or ":" not in t:
        return None
    if not v:
        return "ng", f"{WEEK_JA[d.weekday()]}曜は休み"
    o, c, last = v
    lim = last or c
    tm = _mins(t)
    if tm < _mins(o):
        return "warn", f"{o}に開く。予定が早すぎる"
    if tm > _mins(lim):
        return "ng", (f"最終入場{last}を過ぎる" if last else f"{c}に閉まった後")
    if _mins(lim) - tm <= 20:
        return "warn", (f"最終入場{last}の直前" if last else f"{c}の閉まる直前")
    return "ok", "時間内"


def day_events(day):
    d = date_of(day).isoformat()
    city = {"normandy": "paris", "sky": "paris"}.get(day["theme"], day["theme"])
    return [x for x in HOURS["events"] if x["city"] == city and x["from"] <= d <= x["to"]]


def hours_panel(day):
    d = date_of(day)
    rows, seen, bad = [], set(), 0
    for t, kind, title, note, sid in day["timeline"]:
        if not sid or (sid, t) in seen:
            continue
        r, v = hours_on(sid, d)
        if not r:
            continue
        seen.add((sid, t))
        ck = check_item(t, kind, sid, d)
        st, msg = ck if ck else ("out", "外から眺める予定（中の時間は参考）")
        bad += st in ("warn", "ng")
        mark = {"ok": "✓", "warn": "▲", "ng": "✕", "out": "・"}[st]
        rows.append(f'<li class="hr hr--{st}"><time>{e(t)}</time><div><b>{e(r["name"])}</b>'
                    f'<span class="hr__h">{WEEK_JA[d.weekday()]}曜 {e(hours_text(v))}</span>'
                    f'<span class="hr__v">{mark} {e(msg)}</span><small>{e(r["note"])}（{e(r["basis"])}・{e(r["checked"])}確認 <a href="{e(r["src"])}" target="_blank" rel="noopener">出典↗</a>）</small></div></li>')
    ev = "".join(f'<div class="hr-ev">📣 {e(x["text"])} <a href="{e(x["src"])}" target="_blank" rel="noopener">出典↗</a></div>' for x in day_events(day))
    if not rows and not ev:
        return None
    lead = (f'<p class="panel__lead">{d.month}/{d.day}（{WEEK_JA[d.weekday()]}）の曜日で、予定の時刻と営業時間・最終入場を照らし合わせた結果。'
            f'営業時間は{e(HOURS["checked"])}までの確認で、2027年の直前告知（祝日・行事・ストライキ・工事）で変わることがある。予約の前と前日に公式で確認。</p>')
    return lead + ev + f'<ol class="hrs">{"".join(rows)}</ol>', bad, len(rows)


TRANSPORT = json.loads((ROOT / "data/transport-options.json").read_text())


def entry_panel():
    en = TRANSPORT["entry"]
    items = "".join(f'<li><b>{e(t)}</b><p>{e(x)} <a href="{e(u)}" target="_blank" rel="noopener">出典↗</a></p></li>' for t, x, u in en["items"])
    return panel("sec-entry", "🛂", en["title"], "Entry rules",
                 f'<ul class="entry">{items}</ul><p class="checked">{e(TRANSPORT["checked"])}にEU公式などで確認。出発の1か月前と前日にもう一度。</p>', "EES・ETIAS")


def move_panel(n):
    m = TRANSPORT["days"].get(str(n))
    if not m:
        return None
    head = "".join(f"<th>{e(c)}</th>" for c in m["cols"])
    body = "".join("<tr>" + "".join(f"<td>{e(c)}</td>" for c in r) + "</tr>" for r in m["rows"])
    tips = "".join(f"<li>{e(t)}</li>" for t in m["tips"])
    links = "".join(f'<a class="btn" href="{e(u)}" target="_blank" rel="noopener">{e(t)} ↗</a>' for t, u in m["links"])
    return (f'<p class="panel__lead">{e(m["lead"])}</p><div class="mv-wrap"><table class="mv"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'
            f'<ul class="em__links plain">{tips}</ul><div class="btns">{links}</div>'
            f'<p class="checked">{e(TRANSPORT["checked"])}時点の公式・予約サイトの掲載から。<a href="{e(m["src"])}" target="_blank" rel="noopener">出典↗</a></p>'), m["title"]


HOTEL_CANDIDATES = json.loads((ROOT / "data/hotel-candidates.json").read_text())


def hotel_candidates_panel(n):
    """その都市に着いた日だけ、シートのホテル候補（未決定）を並べる。"""
    city = HOTEL_CITY.get(n)
    c = HOTEL_CANDIDATES["cities"].get(city)
    if not c or HOTEL_CITY.get(n - 1) == city:
        return None
    from urllib.parse import quote
    cards = []
    for h in sorted(c["hotels"], key=lambda x: x["rank"]):
        dec = c.get("decided") == h["name"]
        rows = [("💴", f'{h["price"]}（{c["nights"]}泊）'), ("🍳", h["meal"]), ("🛏", h["bed"]), ("🚶", h["access"]), ("⭐", "クチコミ " + h["review"])]
        dl = "".join(f'<li><span>{a}</span>{e(b)}</li>' for a, b in rows)
        maps = "https://www.google.com/maps/search/?api=1&query=" + quote(h["local"] + ", " + h["addr"])
        cards.append(
            f'<article class="hc{" hc--on" if dec else ""}" data-hc="{e(h["local"])}">'
            f'<div class="hc__top"><span class="hc__rank">{h["rank"]}<small>位</small></span>'
            f'<div><h4>{e(h["name"])}</h4><p class="hc__local">{e(h["local"])}</p></div><span class="hc__score">{e(h["score"])}</span></div>'
            f'<ul class="hc__facts">{dl}</ul>'
            f'<p class="hc__pc"><b>◎</b>{e(h["pros"])}</p><p class="hc__pc hc__pc--c"><b>△</b>{e(h["cons"])}</p>'
            f'<p class="hc__addr">📍 {e(h["addr"])}</p>'
            f'<div class="btns"><a class="btn" href="{e(h["url"])}" target="_blank" rel="noopener">HISで見る ↗</a>'
            f'<a class="btn" href="{e(maps)}" target="_blank" rel="noopener">📍 地図</a>'
            f'<button type="button" class="btn main" data-hotel-pick="{city}" data-name="{e(h["local"])}" data-addr="{e(h["addr"])}">🏨 ここに決めた</button></div>'
            '</article>')
    lead = (f'<p class="panel__lead">ふたりのシートにある{c["label"]}のホテル候補（<b>まだ未決定</b>）。順位はシートのランキング、点数はシートの総合評価。'
            f'{e(c["price_note"])}。「ここに決めた」を押すと、この端末のホテル住所カード（タクシー用）に名前と住所が入ります。</p>')
    note = (f'<p class="checked">シートは{e(HOTEL_CANDIDATES["source"].split("（")[1].split("に読み取り")[0])}時点の内容。'
            f'住所は{e(HOTEL_CANDIDATES["address_checked"].split("。")[0])}に公式・観光局・大手予約サイトの掲載で照合。予約後は確認書の住所を正に。</p>')
    return lead + f'<div class="hcs">{"".join(cards)}</div>' + note, f'{len(c["hotels"])}軒・未決定'


WEATHER_CHIP = {"☔": ("rain", "☔ 雨でもOK"), "🌦": ("mix", "🌦 半分屋外"), "🌤": ("sun", "🌤 屋外")}
TZ = {"venice": "Europe/Rome", "rome": "Europe/Rome", "barcelona": "Europe/Madrid", "paris": "Europe/Paris",
      "normandy": "Europe/Paris", "sky": "Asia/Tokyo"}
CITY_JA = {"venice": "ヴェネツィア", "rome": "ローマ", "barcelona": "バルセロナ", "paris": "パリ", "normandy": "ノルマンディー"}
FX_DEFAULT = json.loads((ROOT / "data/spot-prices-2027-af-jan31.json").read_text()).get("approx_fx_eur_jpy", 170)


def weather_of(s):
    w = dict(booking_lines(s)).get("天気") or ""
    return WEATHER_CHIP.get(w[:1])


def city_weather_url(theme):
    cid = {"normandy": "paris"}.get(theme, theme)
    for c in json.loads((ROOT / "assets/companion-data.json").read_text())["cities"]:
        if c["id"] == cid:
            return c.get("weatherOfficial")
    return None


def rain_panel(day, theme):
    city = CITY_JA.get(theme)
    if not city:
        return ""
    today = {x[4] for x in day["timeline"] if x[4]}
    jsday = (date_of(day).weekday() + 1) % 7  # 旅手帖の休業ルールは日曜=0
    rules = json.loads((ROOT / "assets/companion-data.json").read_text())["scheduleRules"]["rules"]
    closed = {r["id"] for r in rules if jsday in (r.get("closedWeekdays") or [])}
    alts = [sid for sid, s in SPOTS.items() if s.get("city") in (city, city.replace("ヴェネツィア", "ベネチア"))
            and sid not in today and sid not in closed and (weather_of(s) or ("",))[0] == "rain" and pinfo(sid)][:4]
    outdoor = [SPOTS[x]["name"] for x in today if x in SPOTS and (weather_of(SPOTS[x]) or ("",))[0] == "sun"]
    url = city_weather_url(theme)
    lead = (f'<p class="panel__lead">今日の屋外中心の場所：{e("・".join(outdoor) or "なし")}。雨・強風のときは、下の屋内の候補と入れ替えを。'
            f'営業日・予約は各公式で確認。</p>')
    btn = f'<a class="btn main" href="{e(url)}" target="_blank" rel="noopener">☁ {city}の天気予報（公式）↗</a>' if url else ""
    cards = "".join(scard_html(x) for x in alts)
    return lead + f'<div class="btns" style="margin-bottom:16px">{btn}</div>' + (f'<div class="cards">{cards}</div>' if cards else "")


def transit_panel(theme):
    cid = {"normandy": "paris", "sky": "paris"}.get(theme, theme)
    c = next((x for x in json.loads((ROOT / "assets/companion-data.json").read_text())["cities"] if x["id"] == cid), None)
    if not c:
        return ""
    from urllib.parse import quote
    word = {"venice": "sciopero", "rome": "sciopero", "barcelona": "huelga", "paris": "grève"}[cid]
    links = [("🚇 市内交通の運行状況（公式）", c.get("transit")), ("🚕 タクシー（公式・アプリ）", c.get("taxi")),
             ("🚄 鉄道の予約・運行（公式）", c.get("rail")),
             (f"📰 ストライキのニュースを探す（「{word}」）", "https://news.google.com/search?q=" + quote(f"{c['local']} {word}"))]
    lis = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)} ↗</a></li>' for t, u in links if u)
    return (f'<p class="panel__lead">イタリア・スペイン・フランスは交通のストライキが事前に告知されることが多い。移動の前日と当日の朝に確認。'
            f'現地の言葉でストライキは「{word}」。{e(c.get("tip", ""))}</p><ul class="em__links">{lis}</ul>')


def album_panel(n):
    return f"""<div class="album-day" data-album="{n}">
<label class="btn main album-add">📷 この日の写真を追加<input type="file" accept="image/*" multiple data-album-input hidden></label>
<div class="album-grid" data-album-grid></div>
<p class="panel__lead">写真はこのスマホのブラウザの中だけに保存されます（共有リンクには入りません）。保存の前に軽くするため、長い辺1600pxに縮めます。大切な写真は写真アプリにも残してください。</p>
</div>"""


def money_panel(n):
    return f"""<div class="money" data-money data-day="{n}">
<div class="fx"><label>💶 <input type="number" inputmode="decimal" min="0" step="0.01" data-fx-eur placeholder="ユーロ"> €</label><span>＝</span><b data-fx-yen>— 円</b>
<label class="fx__rate">1€＝<input type="number" inputmode="decimal" min="1" step="0.1" data-fx-rate value="{FX_DEFAULT}">円</label></div>
<p class="money__note">レートの初期値はリポジトリの予算メモ（2026-11-23）の参考値。旅行前に最新に直してください。カードの請求額とは差が出ます。</p>
<form class="exp" data-exp-form autocomplete="off">
<input name="what" placeholder="何に（例：ジェラート）" required>
<input name="eur" type="number" inputmode="decimal" min="0" step="0.01" placeholder="€" required>
<select name="who"><option value="a" data-name-a>A</option><option value="b" data-name-b>B</option></select>
<button class="btn main" type="submit">追加</button>
</form>
<div class="names">払う人の名前：<input data-name="a" maxlength="8" placeholder="A"><input data-name="b" maxlength="8" placeholder="B"></div>
<ul class="exp-list" data-exp-list></ul>
<div class="exp-sum" data-exp-sum></div>
</div>"""


def emergency_panel():
    links = "".join(f'<li><a href="{e(u)}" target="_blank" rel="noopener">{e(t)} ↗</a></li>' for t, u in EMERGENCY_LINKS)
    fields = [("card", "カード会社の紛失・盗難の窓口（電話）"), ("insurance", "海外旅行保険の緊急連絡先・証券の場所"),
              ("passport", "パスポートの写真の保存場所・メモ")]
    inputs = "".join(f'<label class="em__f">{e(lab)}<textarea rows="2" data-gmemo="em-{k}"></textarea></label>' for k, lab in fields)
    return f"""<div class="em">
<a class="em__112" href="tel:112"><b>112</b><span>EU共通の緊急番号（警察・救急・消防）<small>タップで発信</small></span></a>
<ol class="em__steps"><li>安全な場所へ。けがや危険があれば112。</li><li>盗難は近くの警察で届け出て、盗難証明をもらう（保険の請求に必要）。</li>
<li>カードはすぐ止める（下に窓口をメモ）。</li><li>パスポートは大使館・総領事館へ（帰国のための渡航書の手続き）。</li></ol>
<ul class="em__links">{links}</ul>
<p class="panel__lead">電話番号・受付時間は公式サイトで確認してください。下のメモはこの端末に保存され、「ふたりで共有」でも送れます。カード番号・パスポート番号は書かないでください。</p>
{inputs}</div>"""


def share_panel():
    return """<div class="share" data-share>
<p class="panel__lead">ホテル・予約済み・メモ・お土産のチェック・支出メモは、それぞれのスマホに保存されています。下のボタンで今の内容を<b>リンクにして相手に送る</b>と、相手が開いたときに取り込めます（同じ項目は「チェックはどちらかが付けていれば付く」「メモは両方を残す」で合わせます）。</p>
<div class="btns"><button type="button" class="btn main" data-share-make>📤 共有リンクを作って送る</button></div>
<p class="share__state" data-share-state></p>
<textarea class="share__url" data-share-url rows="3" readonly hidden></textarea>
<p class="panel__lead">内容はリンクの「#」より後ろに入り、Webサーバーには送られません。LINEなどの相手にだけ送ってください。予約番号・パスポート番号は入れない前提です。</p>
</div>
<dialog class="hdlg" id="import-dlg"><div class="hdlg__edit"><h3>📥 相手の記録を取り込みますか？</h3><p data-import-summary></p>
<div class="hdlg__btns"><button type="button" class="btn" data-import="cancel">やめる</button><button type="button" class="btn main" data-import="ok">取り込む</button></div></div></dialog>"""


PHRASE_IC = {"挨拶": "👋", "普段": "🙏", "ご飯": "🍽", "お土産": "🛍", "ホテル": "🛏", "移動": "🚕", "トイレ": "🚻", "困ったとき": "🆘", "乾杯": "🥂", "機内": "✈"}


def phrases_html(n):
    code = DAY_LANG.get(n, "fr")
    L = PHRASES[code]
    focus = DAY_PHRASE_FOCUS.get(n, [])
    rows_all = [r for r in L["rows"] if r[0] != "機内" or n in (1, 13)]
    cats = list(dict.fromkeys(r[0] for r in rows_all))
    cats = [c for c in focus if c in cats] + [c for c in cats if c not in focus]
    rows_all.sort(key=lambda r: cats.index(r[0]))
    tabs = '<button type="button" class="on" data-cat="today">⭐ 今日よく使う</button>' + "".join(
        f'<button type="button" data-cat="{e(c)}">{PHRASE_IC.get(c, "")} {e(c)}</button>' for c in cats) + '<button type="button" data-cat="all">すべて</button>'
    rows = []
    for cat, ja, loc, rd, en in rows_all:
        f = "1" if cat in focus else ""
        hid = "" if f else " hidden"
        rows.append(f'<div class="pr" data-cat="{e(cat)}" data-focus="{f}"{hid}><div class="pr__ja"><span>{PHRASE_IC.get(cat, "")}</span>{e(ja)}</div>'
                    f'<div class="pr__loc"><b lang="{L["lang"][:2]}">{e(loc)}</b><small>{e(rd)}</small>'
                    f'<button type="button" class="say" data-say="{e(loc)}" data-lang="{L["lang"]}" aria-label="{e(loc)}を読み上げる">🔊</button></div>'
                    f'<div class="pr__en"><b lang="en">{e(en)}</b><button type="button" class="say" data-say="{e(en)}" data-lang="en-US" aria-label="{e(en)}を読み上げる">🔊</button></div></div>')
    note = DAY_LANG_NOTE.get(n, "")
    head = (f'<div class="pr-head"><span class="pr-lang">{e(L["local"])}<small>{e(L["name"])}</small></span><span class="pr-lang en">English<small>英語</small></span></div>')
    return (f'<p class="panel__lead">{e(note)} 最初は「今日よく使う」場面（{"・".join(focus)}）だけを表示。カタカナの読みは目安。🔊で発音を再生（端末の読み上げ機能。やわらかい女性の声を優先して選びます）。</p>'
            f'<div class="pr-tabs" role="group" aria-label="場面">{tabs}</div>{head}<div class="prs">{"".join(rows)}</div>'), L


def scard_html(sid):
    s = SPOTS[sid]
    mini = " ・ ".join(x for x in [s.get("hours"), s.get("duration")] if x)
    buy = f'<div class="buy"><b>買う</b> {e(s.get("souvenir"))}</div>' if s.get("souvenir") else ""
    return (f'<a class="scard" href="{e(maps_link(s))}" target="_blank" rel="noopener">{img(sid, 960, s["name"])}'
            f'<div class="scard__body"><h4>{e(s["name"])}</h4><p>{e(s.get("summary"))}</p>{buy}<div class="mini">📍 {e(mini)}</div></div></a>')


def photo_chip(n, sset):
    ps = PHOTO_SPOTS.get(n)
    if not ps:
        return ""
    place, text, sun = ps
    when = f'<em>おすすめ：日の入り{hm(sset)}の少し前（{hm(sset - 40)}〜{hm(sset)}ごろ）</em>' if sun == "set" else ""
    return f'<div class="chip wide photo"><small>📸 ふたりの写真スポット</small><b>{e(place)}</b><span>{e(text)}</span>{when}</div>'


def day_page(day):
    n = day["n"]
    d = date_of(day)
    wd = d.weekday()
    theme = day["theme"]
    cname, lat, lon, tz = CITY[theme]
    rise, sset = sun_times(d, lat, lon, tz)
    used = []
    feats = {f["id"]: f for f in day["features"]}

    def use(k):
        if k and pinfo(k) and k not in used:
            used.append(k)
        return k

    # ---- ヒーロー
    hk = day["hero"] if day["hero"] and pinfo(day["hero"]) else HERO_FALLBACK.get(n)
    if hk and pinfo(hk):
        use(hk)
        bg = f'<img src="{e(purl(hk, 1280))}" alt="" fetchpriority="high">'
        cr = f'<div class="hero__credit">Photo: {credit(hk)}</div>'
    else:
        bg, cr = sky_svg(n), ""
    hero = f"""<section class="hero hero--day"><div class="hero__bg">{bg}</div>{cr}
<div class="hero__sticker"><div><small>Today's</small><b>{e(HIGHLIGHT.get(n, ''))}</b></div></div>
<div class="hero__in">
<span class="hero__pill"><b>DAY {n:02d}</b>{d.month}月{d.day}日（{WEEK_JA[wd]}）· {e(day['stay'])}</span>
<p class="hero__city">{e(day['local'])}</p>
<h1 class="hero__copy">{day['title']}</h1>
<a class="hero__go" href="#sec-plan" data-open="sec-plan">今日の日程へ ↓</a>
</div></section>"""

    # ---- 今日のルート（写真の帯）
    stops = []
    for i, (t, kind, title, note, sid) in enumerate(day["timeline"], 1):
        k = use(tl_photo_key(n, t, sid))
        ph = f'<figure class="ph"><span class="num">{i}</span><img src="{e(purl(k, 500))}" alt="" loading="lazy"></figure>' if k and pinfo(k) else f'<figure class="ph none"><span class="num">{i}</span></figure>'
        stops.append(f'<a class="stop" href="#t{i}" data-open="t{i}">{ph}<time>{e(t)}</time><b>{e(title)}</b></a>')
    strip = (f'<section class="strip" aria-label="今日のルート"><div class="strip__head"><span class="hand">Today\'s route</span>'
             f'<span>{len(stops)}か所 ／ タップでその場所の詳しい情報へ</span></div><div class="strip__row">{"".join(stops)}</div></section>')

    # ---- イントロ
    shoes = "".join(f'<i class="{"on" if i < day["load"] else ""}"></i>' for i in range(5))
    load_word = ["", "ゆったり", "ふつう", "しっかり歩く", "よく歩く", "この旅で最大級"][day["load"]]
    intro = f"""<div class="intro">
<div><div class="intro__kicker">{e(day['kicker'])}</div><p class="intro__lede">{e(day['lede'])}</p></div>
<div class="chips">
<div class="chip wide"><small>🚆 きょうの移動</small><b>{e(day['move'])}</b></div>
{hotel_chip(n, day)}
<div class="chip"><small>👟 歩く量</small><b><span class="shoes">{shoes}</span>{load_word}</b></div>
<div class="chip wide"><small>☀ {e(cname)}の日の出・日の入</small><b>{hm(rise)} → {hm(sset)}</b></div>
{photo_chip(n, sset)}
<div class="chip wide wx" data-wx data-date="{day['date']}" data-lat="{lat}" data-lon="{lon}" data-tz="{TZ.get(theme, 'Europe/Paris')}"><small>🌤 {e(cname)}の天気予報</small><b data-wx-text>予報は{(date_of(day) - dt.timedelta(days=15)).month}/{(date_of(day) - dt.timedelta(days=15)).day}ごろから</b><em data-wx-note>16日先までの予報（Open-Meteo）</em></div>
<div class="chip wide clock" data-clock data-tz="{TZ.get(theme, 'Europe/Paris')}" data-city="{e(cname)}"><small>🕗 いまの時刻</small><b data-clock-text>—</b></div>
</div></div>"""

    # ---- 日程（アコーディオン）
    rows = []
    prev = None  # (座標, 名前) 直前のスポット。移動の項目でリセット
    ride = "水上バス・水上タクシー" if theme == "venice" else "地下鉄・タクシー"
    for i, (t, kind, title, note, sid) in enumerate(day["timeline"], 1):
        here = SPOTS.get(sid, {}).get("coords") if sid else None
        if here and prev:
            km = dist_km(prev[0], here)
            if km < 0.15:
                rows.append(f'<li class="walk"><span>🚶 {e(prev[1])}のすぐ近く</span></li>')
            elif km * 1.3 <= 1.9 or (kind in ("walk", "shop") and km * 1.3 <= 3):  # 街歩きの予定は歩く前提
                mins = max(3, round(km * 1.3 / 4.5 * 60))
                rows.append(f'<li class="walk"><span>🚶 {e(prev[1])}から 徒歩 約{mins}分（{km * 1.3:.1f}km）</span></li>')
            else:
                rows.append(f'<li class="walk far"><span>🚇 {e(prev[1])}から 約{km:.1f}km（直線・徒歩なら{round(km * 1.3 / 4.5 * 60)}分）・{ride}が便利</span></li>')
        if kind in MOVE_KINDS:
            prev = None
        elif here:
            prev = (here, SPOTS[sid]["name"])
        k = use(tl_photo_key(n, t, sid))
        thumb = f'<span class="th"><img src="{e(purl(k, 500))}" alt="" loading="lazy"></span>' if k and pinfo(k) else '<span class="th none"></span>'
        chips = []
        if sid and sid in SPOTS:
            s = SPOTS[sid]
            if s.get("duration"):
                chips.append(f'<span class="badge">⏱ {e(s["duration"])}</span>')
            chips += spot_badges(s)
            hr_r, hr_v = hours_on(sid, date_of(day))
            if hr_r and kind != "walk":
                ck = check_item(t, kind, sid, date_of(day))
                cls = {"ok": "", "warn": " hr-warn", "ng": " hr-ng"}.get(ck[0] if ck else "ok", "")
                chips.append(f'<span class="badge hrb{cls}">🕘 {WEEK_JA[date_of(day).weekday()]}曜 {e(hours_text(hr_v))}</span>')
            wc = weather_of(s)
            if wc:
                chips.append(f'<span class="badge w-{wc[0]}">{wc[1]}</span>')
            if bookable(sid):
                chips.append('<span class="badge booked" data-booked-badge>✓ 予約済み</span>')
        move = " move" if kind in MOVE_KINDS else ""
        bk = f' data-book="{sid}"' if sid and bookable(sid) else ""
        summ = (f'<time>{e(t)}</time>{thumb}<span class="tx"><span class="kind">{icon(kind)}{KIND_LABEL.get(kind, "")}</span>'
                f'<b class="ttl">{e(title)}</b>{f"<span class=nt>{e(note)}</span>" if note else ""}'
                f'{f"<span class=chips>{chr(10).join(chips)}</span>" if chips else ""}</span>')
        if sid and sid in SPOTS:
            for kk in [sid, f"x:{sid}:1", f"x:{sid}:2"]:
                use(kk)
            body = spot_detail(sid, feats.get(sid, {}))
            if bk:
                body = (f'<label class="bookme"><input type="checkbox" data-book-toggle="{sid}">'
                        f'<span>🎟 予約済みにする<small>チケットを買ったらチェック。この端末に保存</small></span></label>') + body
            star = " star" if sid in feats else ""
            rows.append(f'<li class="it{move}{star}" id="t{i}"{bk}><details class="acc"><summary>{summ}<span class="chev" aria-hidden="true"></span></summary>'
                        f'<div class="acc__body">{body}<button type="button" class="acc__close" data-close>閉じる ▲</button></div></details></li>')
        elif k and pinfo(k):
            rows.append(f'<li class="it{move}" id="t{i}"><details class="acc"><summary>{summ}<span class="chev" aria-hidden="true"></span></summary>'
                        f'<div class="acc__body">{plain_detail(k, title, "")}<button type="button" class="acc__close" data-close>閉じる ▲</button></div></details></li>')
        else:
            rows.append(f'<li class="it{move}" id="t{i}"><div class="acc"><div class="sum">{summ}</div></div></li>')
    rp, sp = max(0, min(100, rise / 14.4)), max(0, min(100, sset / 14.4))
    sunbar = "" if theme == "sky" else f'<div class="sunbar"><span>☀ {hm(rise)}</span><span class="sunbar__bar" style="--rise:{rp:.1f}%;--set:{sp:.1f}%"></span><span>☾ {hm(sset)}</span></div>'
    tools = '<div class="tl-tools"><span>★ は今日の見どころ。タップで写真・歴史・映画・料金がひらく。🚶の時間は直線距離からの目安</span><button type="button" class="btn" data-toggle-all>すべて開く</button></div>'
    nowbar = '<div class="nowbar" data-nowbar hidden></div>'
    timeline = (f'<section class="sec" id="sec-plan" data-now-date="{day["date"]}" data-now-tz="{TZ.get(theme, "Europe/Paris")}"><div class="sec__head"><span class="sec__en">Schedule</span><h2 class="sec__title">今日の日程</h2>'
                f'<span class="sec__sub">時刻は予約前の目安。予約した時刻・列車・便に合わせて組み直す。</span></div>{nowbar}{sunbar}{tools}<ol class="tl2">{"".join(rows)}</ol></section>')

    panels = []
    nav = [("sec-plan", "🗓", "日程")]
    # ---- 地図
    if theme != "sky":
        panels.append(panel("sec-map", "🗺", "地図", "Map", map_html(theme, 460, f"{cname}の地図"), cname, open_=True))
        nav.append(("sec-map", "🗺", "地図"))
    # ---- 移動の選び方
    mv = move_panel(n)
    if mv:
        panels.append(panel("sec-move", "🚆", mv[1], "Getting there", mv[0], "時刻・料金の比較", open_=True))
        nav.append(("sec-move", "🚆", "移動"))
    # ---- 入国の手続き（1日目・2日目）
    if n in (1, 2):
        panels.append(entry_panel())
        nav.append(("sec-entry", "🛂", "入国"))
    # ---- ホテル候補（その都市に着いた日）
    hc = hotel_candidates_panel(n)
    if hc:
        panels.append(panel("sec-hotels", "🏨", "ホテル候補", "Where to stay", hc[0], hc[1]))
        nav.append(("sec-hotels", "🏨", "ホテル"))
    # ---- 寄り道
    shops = [s for s in day.get("shops", []) if s in SPOTS and not any(s == x[4] for x in day["timeline"])]
    if shops:
        for s in shops:
            use(s)
        panels.append(panel("sec-shop", "🛍", "寄り道・商店街", "Streets", f'<div class="cards">{"".join(scard_html(s) for s in shops)}</div>', f"{len(shops)}か所"))
        nav.append(("sec-shop", "🛍", "寄り道"))
    # ---- 持ち物（DAY1）
    if day.get("packing"):
        items = "".join(f'<li><label><input type="checkbox" data-k="pack-{i}"><span>{e(x)}</span></label></li>' for i, x in enumerate(day["packing"]))
        panels.append(panel("sec-pack", "🧳", "持ち物チェック", "Packing", f'<ul class="checks">{items}</ul>', f"{len(day['packing'])}点", open_=True))
        nav.append(("sec-pack", "🧳", "持ち物"))
    # ---- 食べたい
    if day["eats"]:
        fs = []
        for a, b in day["eats"]:
            k = use(f"e:{a}") if pinfo(f"e:{a}") else None
            ph = f'<figure class="ph"><img src="{e(purl(k, 500))}" alt="{e(a)}" loading="lazy"></figure>' if k else '<figure class="ph none"></figure>'
            cr = f'<div class="cr">{credit(k, True)}</div>' if k else ""
            fs.append(f'<div class="food">{ph}<h4>{e(a)}</h4><p>{e(b)}</p>{cr}</div>')
        panels.append(panel("sec-food", "🍝", "食べたいもの", "Eat & Drink", f'<div class="foods">{"".join(fs)}</div>', f"{len(fs)}品"))
        nav.append(("sec-food", "🍝", "食べる"))
    # ---- お土産
    if day["souvenirs"]:
        gs = []
        for i, (a, b, c) in enumerate(day["souvenirs"]):
            k = use(f"s:{a}") if pinfo(f"s:{a}") else None
            ph = f'<img src="{e(purl(k, 500))}" alt="{e(a)}" loading="lazy">' if k else ""
            cr = f'<span class="cr">{credit(k, True)}</span>' if k else ""
            gs.append(f'<label class="gift"><input type="checkbox" data-k="sv-{i}" aria-label="{e(a)}を買った">'
                      f'<span class="ph{"" if k else " none"}" style="display:block">{ph}<span class="heart">♥</span></span>'
                      f'<h4>{e(a)}</h4><em>📍 {e(b)}</em>{f"<small>{e(c)}</small>" if c else ""}{cr}</label>')
        panels.append(panel("sec-gift", "🎁", "お土産リスト", "Souvenirs", '<p class="panel__lead">♥ をタップすると「GET!」に。この端末に保存されます。</p>' + f'<div class="gifts">{"".join(gs)}</div>', f"{len(gs)}点"))
        nav.append(("sec-gift", "🎁", "お土産"))
    # ---- 豆知識・注意
    tv = "".join(f'<div class="tv"><h4>{e(a)}</h4><p>{e(b)}</p></div>' for a, b in day["mame"])
    al = "".join(f"<li>{e(c)}</li>" for c in day["cautions"])
    todo = ""
    if day.get("verify"):
        todo = '<div class="todo"><h4>▲ 予約前に確認すること</h4><ul>' + "".join(f"<li>{e(v)}</li>" for v in day["verify"]) + "</ul></div>"
    cnt = f"注意{len(day['cautions'])}" + (f"・要確認{len(day['verify'])}" if day.get("verify") else "")
    panels.append(panel("sec-tips", "💡", "豆知識と、気をつけること", "Good to know",
                        f'{todo}<div class="alert"><span class="alert__t">気をつけて</span><ul>{al}</ul></div><div class="trivia" style="margin-top:30px">{tv}</div>', cnt))
    nav.append(("sec-tips", "💡", "注意"))
    # ---- 営業時間チェック
    hp = hours_panel(day)
    if hp:
        cnt = (f"要注意{hp[1]}件" if hp[1] else "すべて時間内") + f"・{hp[2]}か所"
        panels.append(panel("sec-hours", "🕘", "営業時間チェック", "Opening hours", hp[0], cnt, open_=bool(hp[1])))
        nav.append(("sec-hours", "🕘", "営業"))
    # ---- チケット
    tix, seen = [], set()
    for _, _, _, _, sid in day["timeline"]:
        if not sid or sid in seen or sid not in SPOTS:
            continue
        seen.add(sid)
        s = SPOTS[sid]
        b = dict(booking_lines(s)).get("予約")
        if not s.get("official") or not b:
            continue
        tix.append(f'<a class="tk" data-book="{sid}" href="{e(s["official"])}" target="_blank" rel="noopener">{img(sid, 500, s["name"], cap=False)}'
                   f'<div class="tk__b"><b>{e(s["name"])}</b><span>🎟 {e(b)}</span><span>💶 {e(s.get("fee", ""))}</span></div><span class="tk__go">OFFICIAL</span></a>')
    if tix:
        panels.append(panel("sec-tix", "🎟", "予約・チケット", "Tickets", f'<div class="tix">{"".join(tix)}</div>'
                            '<p class="tix-note">予約時期は2026年11月時点の公式情報からの目安。購入は公式サイトから。</p>', f"{len(tix)}件"))
        nav.append(("sec-tix", "🎟", "予約"))
    # ---- ふりかえり（DAY13）
    if day.get("recap"):
        al_ = []
        for x in DAYS:
            xd = date_of(x)
            xk = x["hero"] if x["hero"] and pinfo(x["hero"]) else HERO_FALLBACK.get(x["n"])
            im = f'<img src="{e(purl(xk, 500))}" alt="" loading="lazy">' if xk and pinfo(xk) else ""
            al_.append(f'<a href="day{x["n"]:02d}.html" style="--dc:{DAY_COLOR[x["theme"]]}">{im}<span><b>DAY {x["n"]:02d}</b><small>{xd.month}/{xd.day} {e(x["local"])}</small></span></a>')
        panels.append(panel("sec-album", "📷", "13日間のアルバム", "Our 13 days", f'<div class="album">{"".join(al_)}</div>'
                            '<div class="memo" style="margin-top:22px"><textarea data-memo="best" placeholder="いちばんの思い出は？"></textarea></div>'
                            '<div class="memo"><textarea data-memo="gifts" placeholder="お土産を渡す人リスト"></textarea></div>', open_=True))
        nav.append(("sec-album", "📷", "アルバム"))
    # ---- 雨の日
    rp_html = rain_panel(day, theme)
    if rp_html:
        panels.append(panel("sec-rain", "☔", "雨の日は・天気", "Rainy day", rp_html, "屋内の候補"))
        nav.append(("sec-rain", "☔", "雨の日"))
    # ---- 帰国の前に（DAY12）
    if n == 12:
        items = "".join(f'<li><label><input type="checkbox" data-k="ret-{i}"><span>{e(x)}</span></label></li>' for i, x in enumerate(RETURN_PACKING))
        panels.append(panel("sec-return", "🧳", "帰国の前に", "Before flying home", f'<ul class="checks">{items}</ul>', f"{len(RETURN_PACKING)}項目", open_=True))
        nav.append(("sec-return", "🧳", "帰国前"))
    # ---- 交通
    tr = transit_panel(theme)
    if tr:
        panels.append(panel("sec-transit", "🚇", "交通・運行情報", "Transit", tr, "ストライキの確認"))
        nav.append(("sec-transit", "🚇", "交通"))
    # ---- お金
    panels.append(panel("sec-money", "💶", "お金・ふたりの割り勘", "Money", money_panel(n), "円換算・支出メモ"))
    nav.append(("sec-money", "💶", "お金"))
    # ---- 緊急
    panels.append(panel("sec-sos", "🆘", "困ったとき・緊急連絡先", "Emergency", emergency_panel(), "112"))
    nav.append(("sec-sos", "🆘", "緊急"))
    # ---- ひとことフレーズ
    ph_inner, L = phrases_html(n)
    n_pr = ph_inner.count('class="pr"')
    panels.append(panel("sec-talk", "🗣", "ひとことフレーズ", f"{L['local']} & English", ph_inner, f"{L['name'].split('（')[0]}・{n_pr}文"))
    nav.append(("sec-talk", "🗣", "会話"))
    # ---- アルバム
    panels.append(panel("sec-photos", "📷", "ふたりの写真", "Our photos", album_panel(n), "この日の思い出"))
    nav.append(("sec-photos", "📷", "写真"))
    # ---- メモ
    panels.append(panel("sec-memo", "✏️", "ふたりのメモ", "Notes", '<div class="memo"><textarea data-memo="day" placeholder="ホテル名、予約時刻、行きたいお店…"></textarea>'
                        '<small>この端末のブラウザだけに保存されます。予約番号やパスポート番号は書かないでください。'
                        '相手のスマホに送るときは<a href="index.html#sec-share">表紙の「ふたりで共有」</a>から。</small></div>'))
    nav.append(("sec-memo", "✏️", "メモ"))

    subnav = '<nav class="subnav" aria-label="このページの中"><div class="subnav__in">' + "".join(
        f'<a href="#{pid}" data-open="{pid}"><span>{ic}</span>{e(lab)}</a>' for pid, ic, lab in nav) + "</div></nav>"

    # ---- 前後
    def nav_card(x, cls, label):
        xd = date_of(x)
        xk = x["hero"] if x["hero"] and pinfo(x["hero"]) else HERO_FALLBACK.get(x["n"])
        im = f'<img src="{e(purl(xk, 960))}" alt="" loading="lazy">' if xk and pinfo(xk) else ""
        return (f'<a class="{cls}" href="day{x["n"]:02d}.html" style="--nc:{DAY_COLOR[x["theme"]]}">{im}<small>{label}</small>'
                f'<b>DAY {x["n"]:02d} {e(x["local"])}</b><span>{xd.month}/{xd.day}（{WEEK_JA[xd.weekday()]}）{e(x["title"].replace("<br>", ""))}</span></a>')
    prev_ = nav_card(DAYS[n - 2], "", "← Back") if n > 1 else '<a href="index.html" style="--nc:#ef4f3b"><small>← Cover</small><b>Contents</b><span>表紙と目次</span></a>'
    next_ = nav_card(DAYS[n], "r", "Next →") if n < len(DAYS) else '<a class="r" href="flights.html" style="--nc:#18306b"><small>Next →</small><b>In the sky</b><span>空の旅（航空ページ）</span></a>'
    pager = f'<nav class="next">{prev_}{next_}</nav>'
    offline = ('<div class="offline" data-offline="day"><div><b>📥 電波がなくても見られるように</b>'
               '<span data-offline-state>このページの文字とデザインは、一度開くと自動で保存されます。</span></div>'
               f'<button type="button" class="btn main" data-save-day>この日の写真も保存（{len(used)}枚）</button></div>')

    creds = "".join(f"<li>{credit(k)}</li>" for k in used)
    foot = f"""<footer class="foot">
<details><summary>写真クレジット（{len(used)}枚・Wikimedia Commons）と、この手帖について</summary>
<ol>{creds or '<li>写真なし</li>'}</ol>
<p>行程は2026-11-24に受け取った13日間の表（未予約の仮案）。料金・営業時間・予約の目安はリポジトリの確認記録（確認日は各スポットに記載）。日の出・日の入りは計算値（NOAA近似式）。歴史・豆知識は一般的な解説で、現地の案内を優先。写真は場所のイメージで、撮影時期・天候は訪問時と異なる。地図は作成済みのMy Mapsを埋め込み表示。作成：{BUILT}</p></details>
</footer>"""

    body = (f'<body data-theme="{theme}" data-page="{ED['prefix']}day{n:02d}" data-root="{ED['root']}" data-edition="{ED['key']}">{mast(n)}<main>{hero}{strip}'
            f'<div class="wrap">{intro}</div>{subnav}<div class="wrap">{timeline}<div class="panels">{"".join(panels)}</div>{offline}{pager}{foot}</div></main>'
            f'{HOTEL_DIALOG if HOTEL_CITY.get(n) else ""}'
            f'<a class="totop" href="#" aria-label="ページの先頭へ">↑</a>'
            f'<script src="{ED['root']}assets/magazine.js?v={JS_V}" defer></script></body></html>')
    title = f'DAY {n:02d} {d.month}/{d.day}（{WEEK_JA[wd]}）{day["local"]}｜ふたりの欧州手帖'
    return head(title, day["lede"], theme) + body


# ------------------------------------------------------------------ 航空ページ
FLIGHT_PHOTOS = {1: ("p:af-777", "p:haneda-t3"), 2: ("p:cdg-2e", "p:alps-window"), 6: ("p:vueling", "p:fco"),
                 9: ("p:bcn-plane", "p:bcn-airport"), 12: ("p:af-night", "p:af-cabin")}


def flights_page():
    cards, used = [], []
    for f in FLIGHTS:
        mins = flight_minutes(f)
        dd = dt.datetime.strptime(f["dep"], "%Y-%m-%d %H:%M")
        ad = dt.datetime.strptime(f["arr"], "%Y-%m-%d %H:%M")
        plus = (ad.date() - dd.date()).days
        ks = [k for k in FLIGHT_PHOTOS.get(f["day"], ()) if pinfo(k)]
        used += ks
        photos = "".join(img(k, 960, f["code"]) for k in ks)
        warn = "warn" if "要確認" in f["status"] or "?" in f["code"] or "未定" in f["code"] else ""
        notes = "".join(f"<li>{e(x)}</li>" for x in f["notes"])
        cards.append(f"""<article class="flight" id="f{f['day']}">
<div class="flight__main">
<div class="flight__top"><span class="code">{e(f['code'])}</span><span class="pill">{e(f['airline'])}</span><span class="pill">{e(f['kind'])}</span><span class="pill {warn}">{e(f['status'])}</span></div>
<div class="route">
<div><div class="ap">{e(f['from'][0])}</div><div class="city">{e(f['from'][1])}</div><div class="term">{e(f['from'][2])}</div>
<div class="t">{dd:%H:%M}<small>{dd.month}/{dd.day}（{WEEK_JA[dd.weekday()]}）現地時間</small></div></div>
<div class="mid"><span class="pl">✈</span>{mins // 60}時間{mins % 60:02d}分</div>
<div class="r"><div class="ap">{e(f['to'][0])}</div><div class="city">{e(f['to'][1])}</div><div class="term">{e(f['to'][2])}</div>
<div class="t">{ad:%H:%M}{' +' + str(plus) if plus else ''}<small>{ad.month}/{ad.day}（{WEEK_JA[ad.weekday()]}）現地時間</small></div></div>
</div>
<ul>{notes}</ul>
<a class="btn" href="day{f['day']:02d}.html">DAY {f['day']:02d} のページへ →</a>
</div>
<div class="flight__photos">{photos}</div>
</article>""")

    out_t, in_t = flight_minutes(FLIGHTS[0]), flight_minutes(FLIGHTS[-1])
    airline = f"""<div class="alines">
<div class="aline"><h4>🇫🇷 エールフランス</h4><ul>
<li>フランスのフラッグキャリア。1933年設立。</li>
<li>航空連合スカイチームの創設メンバー（2000年）。KLMオランダ航空とグループ。</li>
<li>マイレージは「フライング・ブルー」。運賃クラスで積算率が変わる。</li>
<li>羽田〜パリ線（AF274/AF279）の一部の便に、新しいファーストクラス「ラ・プルミエール」を搭載した777-300ER（2026年3月の報道）。</li>
</ul></div>
<div class="aline"><h4>🌙 長距離便の過ごし方</h4><ul>
<li>行きのAF279は{out_t // 60}時間{out_t % 60:02d}分、帰りのAF274は{in_t // 60}時間{in_t % 60:02d}分（時刻表から計算）。ロシア上空を避けるルートで長め。</li>
<li>行きは深夜発・早朝着。1回目の食事のあとすぐ寝ると、パリの朝に体が合いやすい。</li>
<li>帰りは夜発・日本の夜着。前半で寝て、後半は起きておく。</li>
<li>座席指定・特別機内食は予約後にWebで。ハネムーンであることを伝えるのも◎（対応は保証されない）。</li>
</ul></div>
<div class="aline"><h4>🇪🇸 欧州内の2便</h4><ul>
<li>ローマ→バルセロナ：表は便名空欄。同時刻のVueling VY6007をリポジトリで確認済み（空席は未確認）。</li>
<li>Vuelingはバルセロナが拠点のLCC。安い運賃は座席下の小さな荷物だけのことがある。</li>
<li>バルセロナ→パリ：15:40発は2/8（月）の時刻表に見当たらない記録あり。Air France AF1649（15:00発）が候補。</li>
<li>シェンゲン圏内なので出入国審査はないが、パスポートは必ず手元に。</li>
</ul></div>
</div>"""
    rules = """<div class="trivia">
<div class="tv"><h4>液体は100ml</h4><p>機内持込の液体は1容器100ml以下・透明袋1つが基本。ワインやオリーブオイルは預け荷物へ。空港によって基準が違うことがある。</p></div>
<div class="tv"><h4>モバイルバッテリーは機内へ</h4><p>リチウム電池は預け荷物に入れられない。機内での使用・充電の制限は航空会社の最新案内を確認。</p></div>
<div class="tv"><h4>EES（欧州出入国システム）</h4><p>2025年10月から段階導入。最初のシェンゲン入国（今回はパリCDG）で指紋と顔写真を登録し、出国時も照合。初回は列が長くなりがち。</p></div>
</div>
<div class="alert"><span class="alert__t">気をつけて</span><ul>
<li>表の時刻とリポジトリの調査時刻が違う便がある（AF1426、バルセロナ→パリ、帰国日）。発券時の確定書面で必ず上書きする。</li>
<li>別々に買った航空券どうしは、遅延しても乗継の保護がない。欧州内便は前後に余裕を。</li>
<li>LCCはチェックイン締切・手荷物サイズが厳格。オンラインチェックインを前日に。</li>
</ul></div>"""
    hk = "p:af-777"
    hero_bg = f'<img src="{e(purl(hk, 1280))}" alt="" fetchpriority="high">' if pinfo(hk) else sky_svg(99)
    hero = f"""<section class="hero"><div class="hero__bg">{hero_bg}</div>{f'<div class="hero__credit">Photo: {credit(hk)}</div>' if pinfo(hk) else ''}
<div class="hero__sticker"><div><small>5 flights</small><b>空の旅<br>ガイド</b></div></div>
<div class="hero__in"><span class="hero__pill"><b>FLIGHTS</b>羽田 ⇄ パリ ＋ 欧州内</span>
<p class="hero__city">In the sky</p><h1 class="hero__copy">空の旅も、<br>旅のうち。</h1></div></section>"""
    creds = "".join(f"<li>{credit(k)}</li>" for k in dict.fromkeys(used + ([hk] if pinfo(hk) else [])))
    body = (f'<body data-theme="sky" data-page="{ED['prefix']}flights" data-root="{ED['root']}" data-edition="{ED['key']}">{mast("flights")}<main>{hero}<div class="wrap">'
            + section("搭乗ガイド", "Boarding guide", "".join(cards), "所要時間は表の発着時刻と時差から計算。機材・ターミナルは予約画面と当日の案内を優先。")
            + section("航空会社と機内", "Airlines", airline)
            + section("空港と手荷物のルール", "Airport rules", rules)
            + '<nav class="next"><a href="day13.html" style="--nc:#18306b"><small>← Back</small><b>DAY 13 Tokyo</b><span>帰国</span></a><a class="r" href="index.html" style="--nc:#ef4f3b"><small>Cover →</small><b>Contents</b><span>表紙と目次</span></a></nav>'
            + f'<footer class="foot"><h4>PHOTO CREDITS（Wikimedia Commons）</h4><ol>{creds}</ol><h4>SOURCES</h4><p>便名・時刻：2026-11-24にユーザーから受け取った表、およびリポジトリの <code>data/itinerary-2027-af-jan31.json</code>・<code>docs/2027-af-jan31-feasibility-day-by-day.md</code>。777-300ER・ラ・プルミエールはCAPA（2026-03）と便追跡サイトの記録。写真は機材・空港のイメージで、実際の便の機体とは限らない。作成：{BUILT}</p></footer>'
            + f'</div></main><script src="{ED['root']}assets/magazine.js?v={JS_V}" defer></script></body></html>')
    return head("空の旅｜ふたりの欧州手帖", "羽田〜パリ往復のエールフランス便と、欧州内の乗継・LCC便の搭乗ガイド。", "sky") + body


# ------------------------------------------------------------------ 表紙
def route_map():
    pts = {"Paris": (2.35, 48.86), "Mont-St-Michel": (-1.51, 48.64), "Venezia": (12.34, 45.43),
           "Roma": (12.50, 41.90), "Barcelona": (2.17, 41.39)}
    W, H = 900, 560
    lo0, lo1, la0, la1 = -5.5, 16.5, 40.0, 50.4

    def P(name):
        lo, la = pts[name]
        return (60 + (lo - lo0) / (lo1 - lo0) * (W - 120), 50 + (la1 - la) / (la1 - la0) * (H - 110))

    def arc(a, b, bend=0.22):
        (x1, y1), (x2, y2) = P(a), P(b)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = x2 - x1, y2 - y1
        return f"M{x1:.0f} {y1:.0f} Q{mx - dy * bend:.0f} {my + dx * bend:.0f} {x2:.0f} {y2:.0f}"
    legs = [(arc("Paris", "Venezia", -0.18), "plane"), (f"M{P('Venezia')[0]:.0f} {P('Venezia')[1]:.0f} L{P('Roma')[0]:.0f} {P('Roma')[1]:.0f}", "train"),
            (arc("Roma", "Barcelona", 0.2), "plane"), (arc("Barcelona", "Paris", 0.2), "plane"), (arc("Paris", "Mont-St-Michel", 0.25), "bus")]
    paths = ""
    for d_, kind in legs:
        style = {"plane": 'stroke="#ef4f3b" stroke-dasharray="2 10" stroke-linecap="round" stroke-width="4"',
                 "train": 'stroke="#c4502f" stroke-width="5"', "bus": 'stroke="#3f6577" stroke-dasharray="10 6" stroke-width="4"'}[kind]
        paths += f'<path d="{d_}" fill="none" {style}/>'
    info = {"Paris": ("D9–12", "#283a6b"), "Mont-St-Michel": ("D10", "#3f6577"), "Venezia": ("D2–3", "#0d7480"), "Roma": ("D4–5", "#c4502f"), "Barcelona": ("D6–8", "#1f56c6")}
    dots = ""
    for name in pts:
        x, y = P(name)
        lab, col = info[name]
        anchor, dx = ("end", -16) if name == "Mont-St-Michel" else ("start", 16)
        dots += (f'<circle cx="{x:.0f}" cy="{y:.0f}" r="13" fill="{col}" stroke="#fff" stroke-width="4"/>'
                 f'<text x="{x + dx:.0f}" y="{y + 2:.0f}" text-anchor="{anchor}" font-family="Anton, Impact, sans-serif" font-size="34" fill="{col}">{name.upper()}</text>'
                 f'<text x="{x + dx:.0f}" y="{y + 26:.0f}" text-anchor="{anchor}" font-family="Zen Maru Gothic, sans-serif" font-weight="900" font-size="16" fill="#3a2e28">{lab}</text>')
    legend = ('<g font-family="Zen Maru Gothic, sans-serif" font-weight="700" font-size="15" fill="#3a2e28" transform="translate(60 530)">'
              '<line x1="0" x2="34" y1="-5" y2="-5" stroke="#ef4f3b" stroke-width="4" stroke-dasharray="2 10" stroke-linecap="round"/><text x="42" y="0">飛行機</text>'
              '<line x1="120" x2="154" y1="-5" y2="-5" stroke="#c4502f" stroke-width="5"/><text x="162" y="0">高速鉄道</text>'
              '<line x1="258" x2="292" y1="-5" y2="-5" stroke="#3f6577" stroke-width="4" stroke-dasharray="10 6"/><text x="300" y="0">バスツアー</text></g>')
    sea = ('<text x="390" y="470" font-family="Caveat, cursive" font-size="34" fill="#7aa0b0">Mediterranean Sea</text>'
           '<text x="70" y="120" font-family="Caveat, cursive" font-size="26" fill="#7aa0b0">La Manche</text>'
           '<text x="70" y="40" font-family="Zen Maru Gothic, sans-serif" font-weight="900" font-size="15" fill="#a29387">東京から ✈ 約15時間</text>')
    return f'<div class="mapbox"><svg viewBox="0 0 {W} {H}" role="img" aria-label="周遊ルート図">{sea}{paths}{dots}{legend}</svg></div>'



def booking_list():
    """表紙の「予約しなきゃリスト」。発売日（訪問日から計算）の早い順。"""
    items, seen = [], set()
    for d in DAYS:
        visit = date_of(d)
        for t, kind, title, note, sid in d["timeline"]:
            if not sid or sid in seen or not bookable(sid):
                continue
            seen.add(sid)
            s = SPOTS[sid]
            rule = BOOKING_RULES.get(sid)
            text = rule[1] if rule else (dict(booking_lines(s)).get("予約") or "")
            op = booking_open(sid, visit)
            items.append({"id": sid, "visit": visit, "open": op, "name": s["name"], "text": text, "url": s.get("official"),
                          "icon": "🎟", "day": d["n"], "key": (1, op.isoformat() if op else "9", visit.isoformat())})
    for bid, date, ic, name, text in MANUAL_BOOKINGS:
        v = dt.date.fromisoformat(date)
        n = (v - date_of(DAYS[0])).days + 1
        items.append({"id": bid, "visit": v, "open": None, "name": name, "text": text, "url": None, "icon": ic, "day": max(1, n),
                      "key": (0, "", v.isoformat())})
    items.sort(key=lambda x: x["key"])
    rows = []
    for it in items:
        v = it["visit"]
        when = (f'<span class="bk__open" data-open-date="{it["open"].isoformat()}">発売の目安 {it["open"].month}/{it["open"].day}ごろ</span>'
                if it["open"] else ('<span class="bk__open now">いますぐ確認</span>' if it["key"][0] == 0 else '<span class="bk__open">公式で確認</span>'))
        link = f'<a class="btn" href="{e(it["url"])}" target="_blank" rel="noopener">公式 ↗</a>' if it["url"] else ""
        rows.append(f'<li class="bk" data-book="{e(it["id"])}"><label class="bk__check"><input type="checkbox" data-book-toggle="{e(it["id"])}" aria-label="{e(it["name"])}を予約済みにする"></label>'
                    f'<div class="bk__main"><b>{it["icon"]} {e(it["name"])}</b><span class="bk__meta">{when}'
                    f'<a class="bk__day" href="day{it["day"]:02d}.html">{v.month}/{v.day}（{WEEK_JA[v.weekday()]}）DAY{it["day"]:02d}</a></span>'
                    f'<small>{e(it["text"])}</small></div>{link}</li>')
    done = '<p class="bk__sum" data-book-sum></p>'
    return (f'<p class="panel__lead">予約したら左の□にチェック（この端末に保存。各日のページの「予約済み」と連動）。発売日は2026年11月時点の確認記録と、今回の訪問日から計算した目安です。</p>'
            f'{done}<ol class="bks">{"".join(rows)}</ol>')


def index_edition_block():
    a = "index.html" if ED["key"] == "0131" else "../index.html"
    b = "feb01/index.html" if ED["key"] == "0131" else "index.html"
    on = lambda k: ' class="on" aria-current="page"' if ED["key"] == k else ""
    return (f'<div class="edsw"><span>出発日はまだ未定。2つの版を用意しています：</span>'
            f'<a href="{a}" data-edition-switch="0131"{on("0131")}>✈ 1/31（日）出発 → 2/12 着</a>'
            f'<a href="{b}" data-edition-switch="0201"{on("0201")}>✈ 2/1（月）出発 → 2/13 着</a></div>')


def hours_summary():
    """表紙：この版の曜日で、営業時間に注意がいる予定と、曜日で変えたところ。"""
    items, total = [], 0
    for day in DAYS:
        d = date_of(day)
        for t, kind, title, note, sid in day["timeline"]:
            ck = check_item(t, kind, sid, d) if sid else None
            if ck and ck[0] != "ok":
                r, v = hours_on(sid, d)
                items.append(f'<li class="hr hr--{ck[0]}"><time>{d.month}/{d.day}</time><div><b><a href="day{day["n"]:02d}.html#sec-hours">DAY{day["n"]:02d} {e(t)} {e(r["name"])}</a></b>'
                             f'<span class="hr__h">{WEEK_JA[d.weekday()]}曜 {e(hours_text(v))}</span><span class="hr__v">{e(ck[1])}</span></div></li>')
            total += bool(ck)
    changed = "".join(f"<li>{e(x)}</li>" for x in WEEKDAY_CHANGES[ED["key"]])
    inner = (f'<p class="panel__lead">{e(ED["label"])}の曜日で、{total}か所の予定の時刻を営業時間・最終入場と照らした（{e(HOURS["checked"])}までの確認）。'
             '休館日に当たる予定はなし。各日のページの「🕘 営業時間チェック」に詳細と出典。</p>'
             + (f'<ol class="hrs">{"".join(items)}</ol>' if items else "")
             + f'<h4 style="margin:22px 0 8px">曜日と営業時間に合わせて組み替えたところ</h4><ul class="em__links plain">{changed}</ul>')
    return panel("sec-hours", "🕘", "営業時間チェック", "Opening hours", inner, f"要注意{len(items)}件")


WEEKDAY_CHANGES = {
    "0131": ["ローマ到着日（2/3 水）：フォロ・ロマーノは冬の最終入場15:30。コロッセオの後は入れないので、外の歩道から眺める予定に。",
             "バルセロナの日曜（2/7）：カタルーニャ音楽堂のガイド見学は15:30が最後。16:30→15:00に早め、エル・ボルンを後に。",
             "モンサンミッシェル（2/9 火）：マイバス社の公式行程に合わせて、島を出るのを16:10に。",
             "2/7（日）はボケリア市場・お店が休みなので、市場とお土産は土曜（2/6）と月曜の朝（2/8）に。"],
    "0201": ["ローマ到着日（2/4 木）：フォロ・ロマーノは冬の最終入場15:30。コロッセオの後は入れないので、外の歩道から眺める予定に。",
             "バルセロナ到着日（2/6 土）：サンタ・カテリーナ市場は土曜15:30で閉まるので、ペトリチョル通りに。",
             "バルセロナ：2/7が日曜になるので、グエル公園・カサ・ミラ・音楽堂の日（日曜でも開く所）とサグラダ・お土産の日（月曜）を入れ替え。",
             "バルセロナの日曜（2/7）：カタルーニャ音楽堂のガイド見学は15:30が最後。15:00の枠に。",
             "モンサンミッシェル（2/10 水）：マイバス社は2月は第1日曜以外毎日出発（公式）。島を出るのは16:10。",
             "パリ（2/11 木）：ルーブルは木曜は18時まで（最終17時）。朝いちばんに入る。夜は入籍1周年のディナー。"],
}


def index_page():
    panels, used = [], []
    for sid, label, jp, day in [("036", "Venezia", "ヴェネツィア DAY2–3", 2), ("017", "Roma", "ローマ DAY4–5", 4),
                                ("001", "Barcelona", "バルセロナ DAY6–8", 6), ("048", "Paris", "パリ DAY9–12", 9),
                                ("060", "Mont-St-Michel", "モンサンミッシェル DAY10", 10)]:
        used.append(sid)
        panels.append(f'<a class="cover__p" href="day{day:02d}.html"><img src="{e(purl(sid, 960))}" alt="{e(SPOTS[sid]["name"])}"><span><small>{jp}</small>{label}</span></a>')
    cards = []
    for d in DAYS:
        dd = date_of(d)
        k = d["hero"] if d["hero"] and pinfo(d["hero"]) else HERO_FALLBACK.get(d["n"])
        im = f'<img src="{e(purl(k, 960))}" alt="" loading="lazy">' if k and pinfo(k) else ""
        if k:
            used.append(k)
        cards.append(f'<a class="dcard" href="day{d["n"]:02d}.html" style="--dc:{DAY_COLOR[d["theme"]]}">{im}'
                     f'<span class="n">{d["n"]:02d}<small>{dd.month}/{dd.day}（{WEEK_JA[dd.weekday()]}）</small></span><span class="tag">{e(HIGHLIGHT.get(d["n"], ""))}</span>'
                     f'<span class="city">{e(d["place"])}</span><h3>{e(d["title"].replace("<br>", ""))}</h3><p>{e(d["move"])}</p></a>')
    k = "p:af-777"
    cards.append(f'<a class="dcard" href="flights.html" style="--dc:#18306b">{f"<img src={chr(34)}{e(purl(k, 960))}{chr(34)} alt={chr(34)}{chr(34)} loading={chr(34)}lazy{chr(34)}>" if pinfo(k) else ""}'
                 f'<span class="n">✈<small>5 flights</small></span><span class="tag">航空ガイド</span><span class="city">IN THE SKY</span><h3>空の旅も、旅のうち。</h3><p>エールフランス往復・欧州内の乗継とLCC</p></a>')
    basics = """<div class="basics">
<div class="basic"><div class="ic">📅</div><h4>曜日について</h4><p>{ED["note"]}</p></div>
<div class="basic"><div class="ic">🕗</div><h4>時差は−8時間</h4><p>イタリア・スペイン・フランスは日本の−8時間。現地の朝9時＝日本の夕方5時。</p></div>
<div class="basic"><div class="ic">💶</div><h4>お金はユーロ</h4><p>3か国ともユーロ。タッチ決済のクレジットカードが主役。小銭はトイレやチップ用に少し。</p></div>
<div class="basic"><div class="ic">🔌</div><h4>電源</h4><p>Cタイプ（丸ピン2本）でほぼ対応、230V。</p></div>
<div class="basic"><div class="ic">🆘</div><h4>緊急は112</h4><p>EU共通の緊急番号。パスポートの写真は別の場所にも保存。</p></div>
<div class="basic"><div class="ic">🧥</div><h4>2月は真冬</h4><p>運河・海・丘の上は風が冷たい。教会は肩と膝を隠す。石畳なので底の厚い靴。</p></div>
<div class="basic"><div class="ic">👜</div><h4>スリ対策</h4><p>駅・地下鉄・有名広場が多発地帯。リュックは前、スマホはテーブルに置かない、署名・ミサンガは無視。</p></div>
<div class="basic"><div class="ic">🎭</div><h4>カーニバルの季節</h4><p>ヴェネツィアは1/23〜2/9（公式）、バルセロナは2/4〜2/10（地元メディア）。2都市ともお祭りの季節に滞在する。</p></div>
</div>"""
    plain_apos = lambda x: x.replace("\u2019", "\u0027")  # 読み上げ用に ’ を ' に
    PHR_BASIC = [
        ("#0d7480", "ITALIANO", "it-IT", [("Buongiorno", "ブオンジョルノ", "こんにちは"), ("Grazie", "グラツィエ", "ありがとう"),
                                         ("Il conto, per favore", "イル コント ペル ファヴォーレ", "お会計お願いします"),
                                         ("Dov’è il bagno?", "ドヴェ イル バーニョ？", "トイレはどこ？")]),
        ("#1f56c6", "ESPAÑOL · CATALÀ", "es-ES", [("Hola", "オラ", "こんにちは"), ("Gracias / Gràcies", "グラシアス ／ グラシエス（カタルーニャ語）", "ありがとう"),
                                                 ("La cuenta, por favor", "ラ クエンタ ポル ファボール", "お会計お願いします"),
                                                 ("¿Dónde está el baño?", "ドンデ エスタ エル バーニョ？", "トイレはどこ？（カタルーニャ語は On és el lavabo?＝オン エス エル ラバブ？）")]),
        ("#283a6b", "FRANÇAIS", "fr-FR", [("Bonjour", "ボンジュール", "こんにちは（入店時に必ず）"), ("Merci", "メルスィ", "ありがとう"),
                                          ("L’addition, s’il vous plaît", "ラディスィオン スィル ヴ プレ", "お会計お願いします"),
                                          ("Où sont les toilettes ?", "ウ ソン レ トワレット？", "トイレはどこ？")]),
    ]
    phr = '<div class="phr">' + "".join(
        f'<div style="background:{bg}"><h4>{h}</h4><dl>' + "".join(
            f'<div class="phr__row"><dt lang="{lang[:2]}">{e(loc)}</dt><span class="phr__kana">{e(kana)}</span><dd>{e(ja)}</dd>'
            f'<button type="button" class="say" data-say="{e(plain_apos(loc))}" data-lang="{lang}" aria-label="{e(loc)}を読み上げる">🔊</button></div>'
            for loc, kana, ja in rows) + '</dl></div>' for bg, h, lang, rows in PHR_BASIC) + \
        '<p class="phr__note">カタカナは目安。🔊で発音を再生（端末の読み上げ機能）。各日のページの「ひとことフレーズ」にもっとたくさん。</p></div>'
    creds = "".join(f"<li>{credit(k)}</li>" for k in dict.fromkeys(used + (["p:af-777"] if pinfo("p:af-777") else [])))
    body = f"""<body data-theme="sky" data-page="{ED['prefix']}index" data-root="{ED['root']}" data-edition="{ED['key']}">
<header class="cover">{''.join(panels)}
<div class="cover__t"><div><span class="hand">Our honeymoon in Europe</span><h1>Buon viaggio!</h1><p>ふたりの欧州手帖</p></div></div>
<div class="cover__stk"><div><b>13</b>DAYS<br>4 CITIES</div></div>
</header>
<div class="wrap">
{index_edition_block()}
<section class="todaybar" data-todaybar data-start="{DAYS[0]['date']}" data-days="{len(DAYS)}" data-depart="{date_of(DAYS[0]).month}/{date_of(DAYS[0]).day}（{WEEK_JA[date_of(DAYS[0]).weekday()]}）22:55 羽田発"></section>
{panel("sec-book", "🎟", "予約しなきゃリスト", "To book", booking_list(), "発売の早い順", open_=True)}
{hours_summary()}
{entry_panel()}
{panel("sec-share", "📤", "ふたりで共有", "Share", share_panel(), "リンクで送る")}
{panel("sec-sos", "🆘", "困ったとき・緊急連絡先", "Emergency", emergency_panel(), "112")}
{panel("sec-money", "💶", "お金・ふたりの割り勘", "Money", money_panel(0), "全日の合計")}
{section("13日間のもくじ", "Contents", f'<div class="dgrid">{"".join(cards)}</div>', f"{date_of(DAYS[0]).month}/{date_of(DAYS[0]).day} 羽田発 → {date_of(DAYS[-1]).month}/{date_of(DAYS[-1]).day} 羽田着（{ED['label']}の版）　カードをタップして各日のページへ")}
{section("旅のルート", "Route", route_map(), "位置関係のイメージ図（緯度経度から描いた概略。海岸線は省略）")}
{panel("sec-offline", "📥", "電波がなくても見られるように", "Offline", '<div class="offline" data-offline="all"><div><b>旅行の前に、Wi‑Fiでまとめて保存</b><span data-offline-state>ページの文字とデザインは自動で保存されます。写真（全385枚・約75MB）は下のボタンでまとめて保存できます。地図は通信が必要です。iPhoneはSafariの共有ボタン→「ホーム画面に追加」で、アプリのように開けます。</span><progress data-offline-progress max="100" value="0" hidden></progress></div><button type="button" class="btn main" data-save-all>全日の写真をまとめて保存</button></div>', "", open_=True)}
{section("ふたりの地図", "My Maps", map_html("sky", 520, "新婚旅行の地図"), "作成済みのMy Mapsをそのまま表示。拡大すると各都市のピン")}
{section("出発前に知っておくこと", "Before you go", basics)}
{section("ひとことフレーズ", "Phrases", phr)}
<footer class="foot"><h4>ABOUT THIS BOOK</h4>
<p>未予約の仮の旅程（2026-11-24時点の表）をもとに作った旅行誌。料金・営業時間・予約の目安は、このリポジトリの確認記録（各スポットに確認日）を差し込んでいる。2027年の訪問日に公式サイトで再確認を。写真はWikimedia Commonsの画像を、作者・ライセンスを明記して表示。生成：<code>python3 scripts/build-magazine.py</code>　作成：{BUILT}</p>
<h4>PHOTO CREDITS</h4><ol>{creds}</ol></footer>
</div>
<script src="{ED['root']}assets/magazine.js?v={JS_V}" defer></script>
</body></html>"""
    return head("ふたりの欧州手帖｜2027 新婚旅行 13日間", "ヴェネツィア・ローマ・バルセロナ・パリ・モンサンミッシェル。13日間の新婚旅行を1日1ページにまとめた旅行誌。", "sky") + body


# ------------------------------------------------------------------ 出力
def write_manifest():
    m = {"name": "ふたりの欧州手帖", "short_name": "欧州手帖", "lang": "ja", "start_url": "./index.html", "scope": "./",
         "display": "standalone", "background_color": "#fffdf9", "theme_color": "#ec6870",
         "description": "2027年 新婚旅行13日間の旅行誌（ヴェネツィア・ローマ・バルセロナ・パリ）",
         "icons": [{"src": "assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
                   {"src": "assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
                   {"src": "assets/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
                   {"src": "assets/favicon.svg", "sizes": "any", "type": "image/svg+xml"}]}
    (OUT / "manifest.webmanifest").write_text(json.dumps(m, ensure_ascii=False, indent=1))


def write_sw():
    """オフライン用のService Worker。ページとデザインは先に保存、写真・フォントは見たものから保存。"""
    import hashlib
    one = ["index.html", "flights.html"] + [f"day{d['n']:02d}.html" for d in DAYS]
    pages = ["./"] + one + ["feb01/"] + ["feb01/" + q for q in one]
    core = pages + [f"assets/magazine.css?v={CSS_V}", f"assets/magazine.js?v={JS_V}", "manifest.webmanifest",
                    "assets/favicon.svg", "assets/favicon-32.png", "assets/icon-180.png", "assets/icon-192.png", "assets/icon-512.png"]
    h = hashlib.sha1("".join((OUT / q).read_text() for q in pages if not q.endswith("/")).encode()).hexdigest()[:10]
    js = f"""'use strict';
// ふたりの欧州手帖：オフライン用（scripts/build-magazine.py が生成）
const CORE = 'techo-core-{h}';
const MEDIA = 'techo-media';
const CORE_URLS = {json.dumps(core)};
const MEDIA_HOSTS = ['upload.wikimedia.org', 'fonts.googleapis.com', 'fonts.gstatic.com'];
self.addEventListener('install', e => {{
  e.waitUntil(caches.open(CORE).then(c => c.addAll(CORE_URLS)).then(() => self.skipWaiting()));
}});
self.addEventListener('activate', e => {{
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith('techo-core-') && k !== CORE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener('fetch', e => {{
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (MEDIA_HOSTS.includes(url.hostname)) {{
    e.respondWith((async () => {{
      const cache = await caches.open(MEDIA);
      const hit = await cache.match(req.url);
      if (hit) return hit;
      try {{
        const res = await fetch(req.url, {{ mode: 'cors', credentials: 'omit' }});
        if (res.ok) cache.put(req.url, res.clone());
        return res;
      }} catch (err) {{ return fetch(req); }}
    }})());
    return;
  }}
  if (url.origin !== self.location.origin || !url.pathname.startsWith(new URL(self.registration.scope).pathname)) return;
  e.respondWith((async () => {{
    const cache = await caches.open(CORE);
    try {{
      const res = await Promise.race([fetch(req), new Promise((_, rej) => setTimeout(() => rej(new Error('slow')), 4000))]);
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    }} catch (err) {{
      const hit = await cache.match(req, {{ ignoreSearch: req.mode === 'navigate' }}) || await cache.match(req.url.split('#')[0]);
      if (hit) return hit;
      if (req.mode === 'navigate') return cache.match('index.html');
      throw err;
    }}
  }})());
}});
"""
    (OUT / "sw.js").write_text(js)


def main():
    missing = [(d["n"], f["id"]) for d in DAYS for f in d["features"] if f["id"] not in SPOTS]
    missing += [(d["n"], s) for d in DAYS for *_, s in d["timeline"] if s and s not in SPOTS]
    if missing:
        sys.exit(f"スポットIDが見つかりません: {missing}")
    for key in ("0131", "0201"):
        use_edition(key)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "index.html").write_text(index_page())
        for d in DAYS:
            (OUT_DIR / f"day{d['n']:02d}.html").write_text(day_page(d))
        (OUT_DIR / "flights.html").write_text(flights_page())
    write_manifest()
    write_sw()
    nophoto = [(d["n"], t) for d in DAYS for t, _, _, _, s in d["timeline"] if not pinfo(tl_photo_key(d["n"], t, s))]
    print(f"magazine/: index + {len(DAYS)} days + flights  / 写真なしのタイムライン項目: {nophoto}")


if __name__ == "__main__":
    main()
