"""旅行用ホームに公開してよい観光情報だけを出力。個人の旅程・宿泊先は取り込まない。"""
import csv,json,re,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];N={'k':'http://www.opengis.net/kml/2.2'}
coords={p.findtext('k:name',namespaces=N):[float(v) for v in p.findtext('k:Point/k:coordinates',namespaces=N).strip().split(',')[:2]][::-1] for p in E.parse(R/'data/mymaps-booking-2027-export.kml').findall('.//k:Placemark',N)}
rows=list(csv.DictReader((R/'data/honeymoon-61-photo-index.csv').open(encoding='utf-8-sig')))
spots=[]
for r in rows:
 memo=r['メモ'];body=memo.split('\n\n',1)[-1];body='\n'.join(line for line in body.splitlines() if not line.startswith(('候補区分：','選ぶ・見送る判断：')));film=body.partition('\n\n🎬 作品・場面（ネタバレあり）')[2]
 booking=memo.split('\n\n',1)[0]
 booking='\n'.join(line for line in booking.splitlines() if not line.startswith('訪問想定：'))
 spots.append(dict(id=r['連番'],city=r['都市'],name=r['スポット名'],category=r['色分け'],priority=r['優先度'],query=r['場所検索'],fee=r['入場料金（大人）'],hours=r['営業時間（現地）'],caution=r['定休日・注意'],official=r['予約サイト（公式）'],duration=r['滞在目安'],nearby=r['近くで回るスポット'],food=r['おすすめの食べ物'],souvenir=r['おすすめのお土産'],summary=body.split('\n\n🎬')[0],film=film,booking=booking,checked=r['確認日'],source=r['情報源（公式優先）'],coords=coords[r['スポット名']],indoor='☔' in memo.split('\n\n',1)[0]))
extra=json.loads((R/'data/daily-essentials.json').read_text())
out=dict(version=1,updated='2026-11-18',spots=spots,**extra)
(R/'assets/companion-data.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
print('public guide:',len(spots),'spots,',len(extra['places']),'daily-use candidates; personal trip dates/hotels excluded')
