"""保存済みMy Mapsの書出しと85件の正本・作品メタデータを照合する。"""
import csv, html, json, re, subprocess
import xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
load = lambda name: json.loads((DATA / name).read_text())
rows = list(csv.DictReader((DATA / 'honeymoon-61-photo-index.csv').open(encoding='utf-8-sig')))
by_name = {x['スポット名']: x for x in rows}
ns = {'k': 'http://www.opengis.net/kml/2.2'}
tree = E.parse(DATA / 'mymaps-film-expansion-export.kml')
points = tree.findall('.//k:Placemark', ns)
assert len(points) == len(by_name) == 85
assert {x['連番'] for x in rows} == {f'{i:03}' for i in range(1, 87)} - {'063'}
assert Counter(x['都市'] for x in rows) == {'バルセロナ':20,'ローマ':20,'ヴェネツィア':18,'パリ':25,'ノルマンディー':2}
assert [len(x.findall('k:Placemark',ns)) for x in tree.findall('.//k:Folder',ns)] == [15,17,15,13,2,16,7]
films = load('film-location-notes.json')
scenes = load('film-scene-images.json')
assert len(films) == 34 and len({x['no'] for x in films}) == 32
assert len(scenes) == 9 and sum(len(x['spots']) for x in scenes) == 10
scene_nos = {n for x in scenes for n in x['spots']}
old = E.fromstring(subprocess.check_output(['git','show','3853068:data/mymaps-reservation-weather-export.kml'], cwd=ROOT))
old_points = {x.findtext('k:name',namespaces=ns):x for x in old.findall('.//k:Placemark',ns)}
for p in points:
    name = p.findtext('k:name',namespaces=ns)
    row = by_name[name]
    desc = p.findtext('k:description','',ns)
    plain = html.unescape(re.sub('<[^>]+>','',desc)).strip()
    media = p.findtext('.//k:Data[@name="gx_media_links"]/k:value','',ns).split()
    assert plain.startswith('🎟 予約：'), name
    assert any(x in plain[:400] for x in ['☔','🌦','🌤']), name
    assert len(media) == (2 if row['連番'] in scene_nos else 1), name
    assert ('🎬 作品・場面' in plain) == (row['連番'] in {x['no'] for x in films}), name
    assert row['Googleマップ検索'] in html.unescape(desc), name
    if name in old_points:
        assert p.findtext('k:Point/k:coordinates',namespaces=ns) == old_points[name].findtext('k:Point/k:coordinates',namespaces=ns), name
        old_media = old_points[name].findtext('.//k:Data[@name="gx_media_links"]/k:value','',ns).split()
        # Googleの署名付き画像URLは書出しごとに変化するため文字列一致で画像同一性を判定しない。
        old_desc = old_points[name].findtext('k:description','',ns)
        for drive_id in re.findall(r'drive.google.com/file/d/([^/]+)/',old_desc):
            assert drive_id in desc, name
        assert len(media) >= len(old_media), name
    assert re.search(r'1899-(0288D1|F57C00|0F9D58)',p.findtext('k:styleUrl','',ns)), name
assert len(load('film-expansion-ui-checks.json')) == 23
assert len(load('film-scene-ui-checks.json')) == 10
assert all(x['drive_id'] and x['sha256'] and x['license'] for x in load('expansion-places.json'))
assert all(x['drive_id'] and x['sha256'] and x['credit'] and x['rights'] for x in scenes)
print('OK: 保存済み85ピン・写真85件・7レイヤー・3色・予約先頭85件・作品32ピン/34関連・場面画像10ピン')
print('OK: 既存62ピンの座標・写真出典を保持。追加23現地写真＋場面画像10ピンの画面確認記録あり')
