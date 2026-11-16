"""Drive同期用の確定データを検査する（ネットワーク書き込みなし）。"""
import csv
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
def read_csv(name):
    with (ROOT / 'data' / name).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)

headers, rows = read_csv('honeymoon-61-photo-index.csv')
assert len(headers) == 25 and len(rows) == 62
assert [r['連番'] for r in rows] == [f'{i:03}' for i in range(1, 62)]+['064']
assert len({(r['都市'], r['スポット名']) for r in rows}) == 62
assert Counter(r['都市'] for r in rows) == {'バルセロナ':15,'ローマ':17,'ヴェネツィア':15,'パリ':13,'ノルマンディー':2}
photos = json.loads((ROOT / 'data/paris-added-spots-048-061.json').read_text())
assert len(photos) == 14
for r in rows:
    assert None not in r
    assert r['画像ファイル名'] == f"{r['連番']}_{r['スポット名']}.jpg"
    assert r['Drive相対パス'] == '写真_映え版_62スポット/' + r['画像ファイル名']
    u = urlparse(r['Googleマップ検索'])
    assert u.netloc == 'www.google.com' and u.path == '/maps/search/'
    assert parse_qs(u.query)['query'] == [r['場所検索']]
for r, photo in zip(rows[47:61], photos):
    assert r['連番'] == photo['no']
    assert r['画像ファイル名'] == photo['filename']
    assert r['写真URL'] == photo['image_url'] and r['写真出典URL'] == photo['source_url']
    assert photo['drive_id'] in photo['drive_url']
    assert photo['author'] and photo['license'] and photo['sha256']
_, map_rows = read_csv('mymaps-61-import.csv')
assert len(map_rows) == 62
for r, m in zip(rows, map_rows):
    assert m['Name'] == r['スポット名'] and m['City'] == r['都市']
    assert m['Address or Query'] == r['場所検索']
    assert m['Photo URL'] == r['写真URL'] and m['Google Maps URL'] == r['Googleマップ検索']
_, source_rows = read_csv('photo-source-index-61.csv')
assert len(source_rows) == 62
for r, s in zip(rows, source_rows):
    assert all(r[k] == s[k] for k in s)
verification = json.loads((ROOT / 'data/mymaps-photo-verification-048-061.json').read_text())
assert [p['no'] for p in verification] == [f'{i:03}' for i in range(48, 62)]
assert all(p['photo'] and p['coords'] for p in verification)
print('OK: 62件・25列・001〜061＋064・都市別件数・地図リンク62件・CSV間の行対応')

# 完成版My Mapsの読み戻しとKML・写真確認記録を照合する。
import xml.etree.ElementTree as ET
ns = {'k':'http://www.opengis.net/kml/2.2'}
kml = ET.parse(ROOT / 'data/mymaps-61-photos-city-layers.kml')
placemarks = kml.findall('.//k:Placemark', ns)
assert len(placemarks) == 62
assert {p.find('k:name', ns).text for p in placemarks} == {r['スポット名'] for r in rows}
assert len(kml.findall('.//k:Folder', ns)) == 5
assert all('<img src=' in p.find('k:description', ns).text for p in placemarks)
verified = json.loads((ROOT/'data/mymaps-61-verification.json').read_text())
assert len(verified) == 61 and all(v['photo'] and v['maps_link'] and v['official_link'] for v in verified)
expected_icons = {'観光スポット':'1899-0288D1','食事・市場':'1899-F57C00','お土産・商店街':'1899-0F9D58'}
assert all(v['name'] == r['スポット名'] and v['icon'] == expected_icons[r['色分け']] for v,r in zip(verified,rows))
photo_checks = json.loads((ROOT/'data/mymaps-viewer-photo-checks.json').read_text())
assert len(photo_checks) == 61 and all(v['googleHostedPhoto'] and v['visible_photo_stddev'] > 5 for v in photo_checks)
assert [v['no'] for v in photo_checks] == [r['連番'] for r in rows[:61]]
rounding = json.loads((ROOT/'data/mymaps-coordinate-rounding-audit.json').read_text())
assert all(v['distance_m'] < 1.2 for v in rounding)
print('OK: KML62件・5フォルダ・既存写真61件の実表示記録・登録リンク・3色・座標表示差1.2m未満')

# 保存済みMy Mapsの読み戻し。064は2026-11-16に追加・再読み込み実表示確認。
current=json.loads((ROOT/'data/reservation-weather-map-checks.json').read_text())
assert len(current)==62 and all(v['reservation_first'] and v['weather'] for v in current)
assert {v['no'] for v in current}=={r['連番'] for r in rows}
assert all(v['photo'] for v in current)
assert all(v['coords'] for v in current)
guide=json.loads((ROOT/'data/reservation-weather-guide.json').read_text())
assert len(guide)==62 and len({v['no'] for v in guide})==62
assert all(r['メモ'].startswith('🎟 予約：') for r in rows)
print('OK: 保存済み62ピンの予約先頭・天気表示、重複なし。写真62/62件登録済み。064は2026-11-16に実表示確認。')
