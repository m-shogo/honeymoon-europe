"""2027予約再確認のCSV・実地図出力・保持項目を照合する。"""
import csv,html,json,re,xml.etree.ElementTree as E
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'data';N={'k':'http://www.opengis.net/kml/2.2'}
def points(file):return {p.findtext('k:name',namespaces=N):p for p in E.parse(D/file).findall('.//k:Placemark',N)}
old=points('mymaps-film-expansion-export.kml');new=points('mymaps-booking-2027-export.kml')
b=json.loads((D/'booking-verification-2027.json').read_text()); target={x['name']:x for x in b['spots']}
rows=list(csv.DictReader((D/'honeymoon-61-photo-index.csv').open(encoding='utf-8-sig')))
assert len(old)==len(new)==len(rows)==85 and set(old)==set(new)
assert len(target)==32
for name,p in new.items():
 o=old[name];desc=p.findtext('k:description','',N);od=o.findtext('k:description','',N)
 assert p.findtext('k:Point/k:coordinates',namespaces=N)==o.findtext('k:Point/k:coordinates',namespaces=N),name
 assert p.findtext('k:styleUrl',namespaces=N)==o.findtext('k:styleUrl',namespaces=N),name
 media=p.findtext('.//k:Data[@name="gx_media_links"]/k:value','',N).split();om=o.findtext('.//k:Data[@name="gx_media_links"]/k:value','',N).split()
 assert len(media)==len(om) and len(media)>=1,name
 for driveid in re.findall(r'drive.google.com/file/d/([^/]+)/',od):assert driveid in desc,name
 if '🎬 作品・場面（ネタバレあり）' in od:
  film=od.split('🎬 作品・場面（ネタバレあり）',1)[1].split('公式・予約ページ',1)[0]
  film=re.sub(r'<img[^>]*>','',film).strip()
  assert film in re.sub(r'<img[^>]*>','',desc),name
 if name in target:
  x=target[name];plain=html.unescape(re.sub('<[^>]*>','',desc))
  for field in ['fee','hours','caution','release','visit']:assert x[field] in plain,(name,field)
  assert plain.strip().startswith('🎟 予約：'),name
 else:assert re.sub(r'<img[^>]*>','',desc)==re.sub(r'<img[^>]*>','',od),name
for x in b['spots']:
 r=next(r for r in rows if r['連番']==x['no'])
 for field,key in [('fee','入場料金（大人）'),('hours','営業時間（現地）'),('caution','定休日・注意')]:assert r[key]==x[field]
assert [len(x.findall('k:Placemark',N)) for x in E.parse(D/'mymaps-booking-2027-export.kml').findall('.//k:Folder',N)]==[15,17,15,13,2,16,7]
audit=dict(checked=b['checked'],map_spots=85,booking_updated=32,photos_preserved=85,scene_gallery_pins_preserved=10,coordinate_changes=0,untouched_descriptions=53,backup_map_id='1k7bZ5FdajxnjSAoFMoeApgw4Wz_pwLY',availability_not_guaranteed=True)
(D/'booking-verification-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps(audit,ensure_ascii=False))
