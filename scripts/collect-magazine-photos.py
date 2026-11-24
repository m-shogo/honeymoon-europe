#!/usr/bin/env python3
"""Wikimedia Commons から写真の候補を集める（画像は保存せず、URLとクレジットだけ記録）。

  python3 scripts/collect-magazine-photos.py            # 未取得のキーだけ検索
  python3 scripts/collect-magazine-photos.py --refresh  # 全キーを検索し直す

出力: data/magazine-photo-candidates.json（キーごとの候補）
選定: data/magazine-photos.json の "picks"（キー→候補の番号）。未指定なら0番（品質認定写真を優先）。
"""
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from magazine_photo_queries import all_queries  # noqa: E402

API = "https://commons.wikimedia.org/w/api.php"
UA = "honeymoon-magazine-builder/1.0 (personal travel notebook; python-urllib)"
OK_LICENSE = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)? \d(\.\d)?)", re.I)
BAD_TITLE = re.compile(r"(map|plan|logo|diagram|\.svg|\.gif|coat of arms|flag|ticket|schema)", re.I)
OUT = ROOT / "data/magazine-photo-candidates.json"


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def thumb(url, width=960):
    """原寸URLから標準幅のサムネイルURLを作る（APIにサムネイル生成を頼むと制限にかかるため）。"""
    m = re.match(r"(https://upload\.wikimedia\.org/wikipedia/commons)/(\w/\w\w)/(.+)$", url.split("?")[0])
    return f"{m.group(1)}/thumb/{m.group(2)}/{m.group(3)}/{width}px-{m.group(3)}" if m else url


def search(term, quality):
    q = f"{term} filetype:bitmap" + (" incategory:Quality_images" if quality else "")
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
              "gsrsearch": q, "gsrlimit": 10, "prop": "imageinfo",
              "iiprop": "url|size|mime|extmetadata"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    err = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            break
        except Exception as ex:  # 429など
            err = ex
            time.sleep(5 + attempt * 10)
    else:
        print("  failed:", term, err, flush=True)
        return None
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        lic = plain(meta.get("LicenseShortName", {}).get("value"))
        if not OK_LICENSE.match(lic) or BAD_TITLE.search(p["title"]):
            continue
        if ii.get("mime") != "image/jpeg" or ii.get("width", 0) < 1000:
            continue
        out.append({
            "title": p["title"],
            "thumb": thumb(ii.get("url", "")),
            "w": ii.get("width"), "h": ii.get("height"),
            "source_url": ii.get("descriptionurl"),
            "author": plain(meta.get("Artist", {}).get("value"))[:80] or "不明",
            "license": lic,
            "license_url": meta.get("LicenseUrl", {}).get("value", ""),
            "quality": quality,
        })
    return out


def main():
    refresh = "--refresh" in sys.argv
    cand = json.loads(OUT.read_text()) if OUT.exists() and not refresh else {}
    queries = all_queries()
    todo = [k for k in queries if k not in cand or cand[k].get("query") != queries[k]]
    print(f"{len(todo)} / {len(queries)} keys to search")
    for i, k in enumerate(todo, 1):
        term = queries[k]
        seen, items = set(), []
        failed = False
        # 品質認定写真の検索は名所の追加写真（x:）だけ。料理・移動は一致度を優先
        for quality in ((True, False) if k.startswith("x:") else (False,)):
            res = search(term, quality)
            if res is None:
                failed = True
                continue
            for c in res:
                if c["title"] not in seen:
                    seen.add(c["title"])
                    items.append(c)
            time.sleep(0.5)
        if failed and not items:
            continue
        cand[k] = {"query": term, "items": items[:8]}
        print(f"[{i}/{len(todo)}] {k}: {len(items)}", flush=True)
        if i % 10 == 0:
            OUT.write_text(json.dumps(cand, ensure_ascii=False, indent=1))
    OUT.write_text(json.dumps(cand, ensure_ascii=False, indent=1))
    empty = [k for k, v in cand.items() if not v["items"]]
    print("no candidates:", empty)


if __name__ == "__main__":
    main()
