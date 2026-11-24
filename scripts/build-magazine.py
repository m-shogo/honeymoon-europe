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
from magazine_content import TL_PHOTOS, HIGHLIGHT  # noqa: E402

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
<link rel="stylesheet" href="assets/magazine.css?v={CSS_V}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle cx='16' cy='16' r='16' fill='%23ef4f3b'/%3E%3Ctext x='16' y='22' font-family='Arial' font-weight='900' font-size='17' fill='%23fff' text-anchor='middle'%3E%E2%99%A1%3C/text%3E%3C/svg%3E">
</head>
"""


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
    col = f'<div class="{cls}">{figs}</div>' if figs else ""
    return f'{col}<div class="feat__grid"><div>{"".join(left)}</div><div>{right}</div></div>'


def plain_detail(k, title, note):
    return (f'<div class="collage n1 small">{img(k, 1280, title)}</div>' if k and pinfo(k) else "") + \
           (f'<p class="feat__summary" style="margin-top:14px">{e(note)}</p>' if note else "")


def panel(pid, icon_, title, en, inner, count="", open_=False):
    c = f'<small>{e(count)}</small>' if count else ""
    return (f'<details class="panel" id="{pid}"{" open" if open_ else ""}><summary class="panel__head">'
            f'<span class="panel__ic">{icon_}</span><span class="panel__t"><b>{title}</b><em>{e(en)}</em></span>{c}<span class="chev" aria-hidden="true"></span></summary>'
            f'<div class="panel__body">{inner}</div></details>')


def scard_html(sid):
    s = SPOTS[sid]
    mini = " ・ ".join(x for x in [s.get("hours"), s.get("duration")] if x)
    buy = f'<div class="buy"><b>買う</b> {e(s.get("souvenir"))}</div>' if s.get("souvenir") else ""
    return (f'<a class="scard" href="{e(maps_link(s))}" target="_blank" rel="noopener">{img(sid, 960, s["name"])}'
            f'<div class="scard__body"><h4>{e(s["name"])}</h4><p>{e(s.get("summary"))}</p>{buy}<div class="mini">📍 {e(mini)}</div></div></a>')


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
<div class="chip"><small>🛏 宿泊</small><b>{e(day['stay'])}</b></div>
<div class="chip"><small>👟 歩く量</small><b><span class="shoes">{shoes}</span>{load_word}</b></div>
<div class="chip wide"><small>☀ {e(cname)}の日の出・日の入</small><b>{hm(rise)} → {hm(sset)}</b></div>
</div></div>"""

    # ---- 日程（アコーディオン）
    rows = []
    for i, (t, kind, title, note, sid) in enumerate(day["timeline"], 1):
        k = use(tl_photo_key(n, t, sid))
        thumb = f'<span class="th"><img src="{e(purl(k, 500))}" alt="" loading="lazy"></span>' if k and pinfo(k) else '<span class="th none"></span>'
        chips = []
        if sid and sid in SPOTS:
            s = SPOTS[sid]
            if s.get("duration"):
                chips.append(f'<span class="badge">⏱ {e(s["duration"])}</span>')
            chips += spot_badges(s)
        move = " move" if kind in MOVE_KINDS else ""
        summ = (f'<time>{e(t)}</time>{thumb}<span class="tx"><span class="kind">{icon(kind)}{KIND_LABEL.get(kind, "")}</span>'
                f'<b class="ttl">{e(title)}</b>{f"<span class=nt>{e(note)}</span>" if note else ""}'
                f'{f"<span class=chips>{chr(10).join(chips)}</span>" if chips else ""}</span>')
        if sid and sid in SPOTS:
            for kk in [sid, f"x:{sid}:1", f"x:{sid}:2"]:
                use(kk)
            body = spot_detail(sid, feats.get(sid, {}))
            star = " star" if sid in feats else ""
            rows.append(f'<li class="it{move}{star}" id="t{i}"><details class="acc"><summary>{summ}<span class="chev" aria-hidden="true"></span></summary>'
                        f'<div class="acc__body">{body}<button type="button" class="acc__close" data-close>閉じる ▲</button></div></details></li>')
        elif k and pinfo(k):
            rows.append(f'<li class="it{move}" id="t{i}"><details class="acc"><summary>{summ}<span class="chev" aria-hidden="true"></span></summary>'
                        f'<div class="acc__body">{plain_detail(k, title, "")}<button type="button" class="acc__close" data-close>閉じる ▲</button></div></details></li>')
        else:
            rows.append(f'<li class="it{move}" id="t{i}"><div class="acc"><div class="sum">{summ}</div></div></li>')
    rp, sp = max(0, min(100, rise / 14.4)), max(0, min(100, sset / 14.4))
    sunbar = "" if theme == "sky" else f'<div class="sunbar"><span>☀ {hm(rise)}</span><span class="sunbar__bar" style="--rise:{rp:.1f}%;--set:{sp:.1f}%"></span><span>☾ {hm(sset)}</span></div>'
    tools = '<div class="tl-tools"><span>★ は今日の見どころ。タップで写真・歴史・映画・料金がひらく</span><button type="button" class="btn" data-toggle-all>すべて開く</button></div>'
    timeline = (f'<section class="sec" id="sec-plan"><div class="sec__head"><span class="sec__en">Schedule</span><h2 class="sec__title">今日の日程</h2>'
                f'<span class="sec__sub">時刻は予約前の目安。予約した時刻・列車・便に合わせて組み直す。</span></div>{sunbar}{tools}<ol class="tl2">{"".join(rows)}</ol></section>')

    panels = []
    nav = [("sec-plan", "🗓", "日程")]
    # ---- 地図
    if theme != "sky":
        panels.append(panel("sec-map", "🗺", "地図", "Map", map_html(theme, 460, f"{cname}の地図"), cname, open_=True))
        nav.append(("sec-map", "🗺", "地図"))
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
        tix.append(f'<a class="tk" href="{e(s["official"])}" target="_blank" rel="noopener">{img(sid, 500, s["name"], cap=False)}'
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
    # ---- メモ
    panels.append(panel("sec-memo", "✏️", "ふたりのメモ", "Notes", '<div class="memo"><textarea data-memo="day" placeholder="ホテル名、予約時刻、行きたいお店…"></textarea>'
                        '<small>この端末のブラウザだけに保存されます。予約番号やパスポート番号は書かないでください。</small></div>'))
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

    creds = "".join(f"<li>{credit(k)}</li>" for k in used)
    foot = f"""<footer class="foot">
<details><summary>写真クレジット（{len(used)}枚・Wikimedia Commons）と、この手帖について</summary>
<ol>{creds or '<li>写真なし</li>'}</ol>
<p>行程は2026-11-24に受け取った13日間の表（未予約の仮案）。料金・営業時間・予約の目安はリポジトリの確認記録（確認日は各スポットに記載）。日の出・日の入りは計算値（NOAA近似式）。歴史・豆知識は一般的な解説で、現地の案内を優先。写真は場所のイメージで、撮影時期・天候は訪問時と異なる。地図は作成済みのMy Mapsを埋め込み表示。作成：{BUILT}</p></details>
</footer>"""

    body = (f'<body data-theme="{theme}" data-page="day{n:02d}">{mast(n)}<main>{hero}{strip}'
            f'<div class="wrap">{intro}</div>{subnav}<div class="wrap">{timeline}<div class="panels">{"".join(panels)}</div>{pager}{foot}</div></main>'
            f'<a class="totop" href="#" aria-label="ページの先頭へ">↑</a>'
            f'<script src="assets/magazine.js?v={JS_V}" defer></script></body></html>')
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
    body = (f'<body data-theme="sky" data-page="flights">{mast("flights")}<main>{hero}<div class="wrap">'
            + section("搭乗ガイド", "Boarding guide", "".join(cards), "所要時間は表の発着時刻と時差から計算。機材・ターミナルは予約画面と当日の案内を優先。")
            + section("航空会社と機内", "Airlines", airline)
            + section("空港と手荷物のルール", "Airport rules", rules)
            + '<nav class="next"><a href="day13.html" style="--nc:#18306b"><small>← Back</small><b>DAY 13 Tokyo</b><span>帰国</span></a><a class="r" href="index.html" style="--nc:#ef4f3b"><small>Cover →</small><b>Contents</b><span>表紙と目次</span></a></nav>'
            + f'<footer class="foot"><h4>PHOTO CREDITS（Wikimedia Commons）</h4><ol>{creds}</ol><h4>SOURCES</h4><p>便名・時刻：2026-11-24にユーザーから受け取った表、およびリポジトリの <code>data/itinerary-2027-af-jan31.json</code>・<code>docs/2027-af-jan31-feasibility-day-by-day.md</code>。777-300ER・ラ・プルミエールはCAPA（2026-03）と便追跡サイトの記録。写真は機材・空港のイメージで、実際の便の機体とは限らない。作成：{BUILT}</p></footer>'
            + f'</div></main><script src="assets/magazine.js?v={JS_V}" defer></script></body></html>')
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
<div class="basic"><div class="ic">📅</div><h4>曜日について</h4><p>貼り付けた表の曜日（1/31が金曜など）は2025年の暦。2027年は1/31が日曜。表の注意書き（2/7日曜はボケリア休み、火曜はルーブル休館）は2027年の曜日と一致するので、2027年の曜日で組んでいる。</p></div>
<div class="basic"><div class="ic">🕗</div><h4>時差は−8時間</h4><p>イタリア・スペイン・フランスは日本の−8時間。現地の朝9時＝日本の夕方5時。</p></div>
<div class="basic"><div class="ic">💶</div><h4>お金はユーロ</h4><p>3か国ともユーロ。タッチ決済のクレジットカードが主役。小銭はトイレやチップ用に少し。</p></div>
<div class="basic"><div class="ic">🔌</div><h4>電源</h4><p>Cタイプ（丸ピン2本）でほぼ対応、230V。</p></div>
<div class="basic"><div class="ic">🆘</div><h4>緊急は112</h4><p>EU共通の緊急番号。パスポートの写真は別の場所にも保存。</p></div>
<div class="basic"><div class="ic">🧥</div><h4>2月は真冬</h4><p>運河・海・丘の上は風が冷たい。教会は肩と膝を隠す。石畳なので底の厚い靴。</p></div>
<div class="basic"><div class="ic">👜</div><h4>スリ対策</h4><p>駅・地下鉄・有名広場が多発地帯。リュックは前、スマホはテーブルに置かない、署名・ミサンガは無視。</p></div>
<div class="basic"><div class="ic">🎭</div><h4>カーニバルの季節</h4><p>ヴェネツィアは1/23〜2/9（公式）、バルセロナは2/4〜2/10（地元メディア）。2都市ともお祭りの季節に滞在する。</p></div>
</div>"""
    phr = """<div class="phr">
<div style="background:#0d7480"><h4>ITALIANO</h4><dl><dt>Buongiorno</dt><dd>こんにちは</dd><dt>Grazie</dt><dd>ありがとう</dd><dt>Il conto, per favore</dt><dd>お会計お願いします</dd><dt>Dov’è il bagno?</dt><dd>トイレはどこ？</dd></dl></div>
<div style="background:#1f56c6"><h4>ESPAÑOL · CATALÀ</h4><dl><dt>Hola</dt><dd>こんにちは</dd><dt>Gracias / Gràcies</dt><dd>ありがとう</dd><dt>La cuenta, por favor</dt><dd>お会計お願いします</dd><dt>On és el lavabo?</dt><dd>トイレはどこ？（カタルーニャ語）</dd></dl></div>
<div style="background:#283a6b"><h4>FRANÇAIS</h4><dl><dt>Bonjour</dt><dd>こんにちは（入店時に必ず）</dd><dt>Merci</dt><dd>ありがとう</dd><dt>L’addition, s’il vous plaît</dt><dd>お会計お願いします</dd><dt>Où sont les toilettes ?</dt><dd>トイレはどこ？</dd></dl></div>
</div>"""
    creds = "".join(f"<li>{credit(k)}</li>" for k in dict.fromkeys(used + (["p:af-777"] if pinfo("p:af-777") else [])))
    body = f"""<body data-theme="sky" data-page="index">
<header class="cover">{''.join(panels)}
<div class="cover__t"><div><span class="hand">Our honeymoon in Europe</span><h1>Buon viaggio!</h1><p>ふたりの欧州手帖</p></div></div>
<div class="cover__stk"><div><b>13</b>DAYS<br>4 CITIES</div></div>
</header>
<div class="wrap">
{section("13日間のもくじ", "Contents", f'<div class="dgrid">{"".join(cards)}</div>', "1/31 羽田発 → 2/12 羽田着　カードをタップして各日のページへ")}
{section("旅のルート", "Route", route_map(), "位置関係のイメージ図（緯度経度から描いた概略。海岸線は省略）")}
{section("ふたりの地図", "My Maps", map_html("sky", 520, "新婚旅行の地図"), "作成済みのMy Mapsをそのまま表示。拡大すると各都市のピン")}
{section("出発前に知っておくこと", "Before you go", basics)}
{section("ひとことフレーズ", "Phrases", phr)}
<footer class="foot"><h4>ABOUT THIS BOOK</h4>
<p>未予約の仮の旅程（2026-11-24時点の表）をもとに作った旅行誌。料金・営業時間・予約の目安は、このリポジトリの確認記録（各スポットに確認日）を差し込んでいる。2027年の訪問日に公式サイトで再確認を。写真はWikimedia Commonsの画像を、作者・ライセンスを明記して表示。生成：<code>python3 scripts/build-magazine.py</code>　作成：{BUILT}</p>
<h4>PHOTO CREDITS</h4><ol>{creds}</ol></footer>
</div>
<script src="assets/magazine.js?v={JS_V}" defer></script>
</body></html>"""
    return head("ふたりの欧州手帖｜2027 新婚旅行 13日間", "ヴェネツィア・ローマ・バルセロナ・パリ・モンサンミッシェル。13日間の新婚旅行を1日1ページにまとめた旅行誌。", "sky") + body


# ------------------------------------------------------------------ 出力
def main():
    missing = [(d["n"], f["id"]) for d in DAYS for f in d["features"] if f["id"] not in SPOTS]
    missing += [(d["n"], s) for d in DAYS for *_, s in d["timeline"] if s and s not in SPOTS]
    if missing:
        sys.exit(f"スポットIDが見つかりません: {missing}")
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(index_page())
    for d in DAYS:
        (OUT / f"day{d['n']:02d}.html").write_text(day_page(d))
    (OUT / "flights.html").write_text(flights_page())
    nophoto = [(d["n"], t) for d in DAYS for t, _, _, _, s in d["timeline"] if not pinfo(tl_photo_key(d["n"], t, s))]
    print(f"magazine/: index + {len(DAYS)} days + flights  / 写真なしのタイムライン項目: {nophoto}")


if __name__ == "__main__":
    main()
