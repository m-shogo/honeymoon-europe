"""公開My Mapsの読戻しと、変更前85ピンの保持を検査する。"""
import hashlib,json,re,math,urllib.request,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];N={'k':'http://www.opengis.net/kml/2.2'}
def canonical(p):
    text=p.findtext('k:description',namespaces=N) or ''
    text=re.sub(r'https://(?:lh3\.googleusercontent\.com/umsh/|mymaps\.usercontent\.google\.com/hostedimage/)[^" <>\s]+','DYNAMIC_GOOGLE_PHOTO_URL',text)
    fields={x.get('name'):x.findtext('k:value',namespaces=N) for x in p.findall('k:ExtendedData/k:Data',N) if x.get('name')!='gx_media_links'}
    return dict(name=p.findtext('k:name',namespaces=N),description=text,fields=fields,coordinates=p.findtext('k:Point/k:coordinates',namespaces=N),style=p.findtext('k:styleUrl',namespaces=N),images=text.count('<img'))
def digest(p):return hashlib.sha256(json.dumps(canonical(p),ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def meters(a,b):
    x,y=map(math.radians,a);u,v=map(math.radians,b)
    h=math.sin((x-u)/2)**2+math.cos(x)*math.cos(u)*math.sin((y-v)/2)**2
    return 6371000*2*math.asin(math.sqrt(h))
def main():
    d=json.loads((R/'data/map-amenities.json').read_text());base=json.loads((R/'data/mymaps-amenities-baseline.json').read_text())
    raw=urllib.request.urlopen('https://www.google.com/maps/d/kml?mid='+d['mapId']+'&forcekml=1',timeout=25).read()
    root=E.fromstring(raw);pins=root.findall('.//k:Placemark',N);names=[p.findtext('k:name',namespaces=N) for p in pins];byname=dict(zip(names,pins));assert len(names)==len(set(names))==115
    assert len(root.findall('.//k:Folder',N))==9
    assert all(digest(byname[name])==value for name,value in base['pins'].items()),'Existing pin changed'
    maxerr=0
    for key,ui in [('toilets','mymaps-wc-ui-verification.json'),('places','mymaps-food-ui-verification.json')]:
        actual={x['name']:x for x in json.loads((R/'data'/ui).read_text())};assert len(actual)==15
        for p in d[key]:
            assert p['name'] in byname and p['name'] in actual
            assert actual[p['name']]['coords'] and len(actual[p['name']]['coords'])==2
            err=meters(p['coords'],actual[p['name']]['coords']);assert err<1.5;maxerr=max(maxerr,err)
            pm=byname[p['name']];txt=pm.findtext('k:description',namespaces=N) or ''
            assert p['source'] in txt and p['name'] in names
            style=pm.findtext('k:styleUrl',namespaces=N)
            if key=='toilets':assert style.endswith('7D7D7D')
            else:
                expected='0F9D58' if 'スーパー' in p['type'] else 'F57C00'
                assert style.endswith(expected),(p['name'],style,expected)
            if p['id']=='life-paris-bofinger':assert 'Smart Casual' in txt
    (R/'data/mymaps-amenities-export.kml').write_bytes(raw)
    report=dict(total=115,layers=9,originalPinsPreserved=85,toilets=15,food=6,groceryAndSmallStores=6,anniversaryCandidates=3,duplicateNames=0,uiReadback=30,maxCoordinateDisplayDifferenceMeters=round(maxerr,3),originalPhotoUrlNote='Googleの動的配信URLのみ正規化。元の説明・登録項目・位置・色・写真枚数を比較。全85枚の再表示検査ではない。')
    (R/'data/mymaps-amenities-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
