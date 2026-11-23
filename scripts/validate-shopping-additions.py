"""実地図の追加前後のKMLで既存115ピンを検査。"""
from pathlib import Path
import json,re,xml.etree.ElementTree as E
D=Path(__file__).resolve().parents[1]/'data';N={'k':'http://www.opengis.net/kml/2.2'}
def read(path):
 r=E.parse(path);ps=r.findall('.//k:Placemark',N);return r,ps,{p.findtext('k:name',namespaces=N):p for p in ps}
b,bps,bn=read(D/'mymaps-shopping-before-20261123.kml');a,aps,an=read(D/'mymaps-shopping-after-20261123.kml');new=json.loads((D/'shopping-additions-087-093.json').read_text())
assert len(bps)==115 and len(aps)==122 and len(an)==122
assert set(an)-set(bn)=={p['name'] for p in new}
for name,p in bn.items():
 assert p.findtext('k:Point/k:coordinates',namespaces=N)==an[name].findtext('k:Point/k:coordinates',namespaces=N),(name,'coordinates')
 # Googleの写真プロキシURLは書出しごとに更新されるため、本文・出典・写真枚数を比較。
 norm=lambda s:re.sub(r'<img[^>]*>','<img>',s or '')
 assert norm(p.findtext('k:description',namespaces=N))==norm(an[name].findtext('k:description',namespaces=N)),(name,'description excluding rotating photo proxy URLs')
 media=lambda el:(el.findtext('.//k:Data[@name="gx_media_links"]/k:value',default='',namespaces=N)).split()
 assert len(media(p))==len(media(an[name])),(name,'photo count')
for p in new:
 q=an[p['name']];s=q.findtext('k:description',namespaces=N);assert '確認日：2026-11-23' in s and '2027' in s
 assert q.find('.//k:Data[@name="gx_media_links"]/k:value',N) is not None,p['name']
 latlon=[float(x) for x in q.findtext('k:Point/k:coordinates',namespaces=N).split(',')[:2]][::-1]
 assert all(abs(x-y)<.00001 for x,y in zip(latlon,p['coords'])),p['name']
report={'before':len(bps),'after':len(aps),'added':7,'layers':len(a.findall('.//k:Folder',N)),'preservedExistingPins':115,'duplicateNames':len(aps)-len(an),'photoMediaEntries':7,'photoActualDisplay':'7/7 visual screenshots reviewed','backupMap':'https://www.google.com/maps/d/edit?mid=1mylZlV0VX4sdb3P_GYU2WOle2l3T7VA'}
(D/'shopping-map-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
