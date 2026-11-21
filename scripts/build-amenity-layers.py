"""生活スポットの別レイヤーを生成。観光85件のCSV・KMLは変更しない。"""
import csv, json, html, xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/map-amenities.json'
K='http://www.opengis.net/kml/2.2'
ET.register_namespace('',K)
def el(parent,name,value=None):
    e=ET.SubElement(parent,'{'+K+'}'+name)
    if value is not None:e.text=str(value)
    return e
def description(p):
    fields=[('予約',p.get('booking')),('服装・ドレスコード',p.get('dress')),('分類',p['type']),('都市',p['city']),('場所',p['address']),('近くの観光',p['nearby']),('料金',p['fee']),('営業時間',p['hours']),('利用条件・注意',p['note']),('日本語での紹介',p.get('japaneseNote')),('確認日',p['checked'])]
    text='\n'.join(f'{k}：{v}' for k,v in fields if v)
    text+='\n公式・出典：'+p['source']
    for source in p.get('extraSources',[]):text+='\n補足出典：'+source
    if p.get('japaneseSource'):text+='\n日本語紹介の出典：'+p['japaneseSource']
    if p.get('photo'):
        ph=p['photo']
        text+='\n写真：'+ph['author']+' / Wikimedia Commons / '+ph['license']+'\n写真出典：'+ph['source']+'\n写真ライセンス：'+ph['licenseUrl']+'\n写真（Drive）：'+ph['driveUrl']
    text+='\nGoogleマップ：'+p['mapUrl']
    return text
def main():
    d=json.loads(DATA.read_text()); wc=d['toilets']; places=d['places']
    assert len({p['id'] for p in wc+places})==len(wc+places)
    doc=ET.Element('{'+K+'}kml'); body=el(doc,'Document');el(body,'name','🚻観光地近くのトイレ')
    style=el(body,'Style');style.set('id','wc');icon=el(style,'IconStyle');el(icon,'color','ff7d7d7d');el(icon,'scale',0.85);el(el(icon,'Icon'),'href','https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png')
    for p in wc:
        assert len(p['coords'])==2
        m=el(body,'Placemark');el(m,'name',p['name']);el(m,'description',description(p));el(m,'styleUrl','#wc');el(el(m,'Point'),'coordinates',f"{p['coords'][1]},{p['coords'][0]},0")
    ET.indent(doc);ET.ElementTree(doc).write(ROOT/'data/mymaps-amenities-wc.kml',encoding='utf-8',xml_declaration=True)
    with (ROOT/'data/mymaps-amenities-food.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['Name','Description','Address','City','Category','Google Maps URL','ID'])
        for p in places:w.writerow([p['name'],description(p),p['query'],p['city'],p['type'],p['mapUrl'],p['id']])
    essentials=json.loads((ROOT/'data/daily-essentials.json').read_text())
    essentials['places']=[dict(id=p['id'],city=p['city'],name=p['name'],type=p['type'],query=p.get('query') or ','.join(map(str,p['coords'])),note=description(p),source=p['source'],checked=p['checked'],**({'photo':p['photo']} if p.get('photo') else {})) for p in places+wc]
    for c in essentials['cities']:
        if c['id']=='rome':c['toiletNote']='P.Stopの総合案内は€1、個別施設案内は€1.50と不一致。現地料金を確認。チッタ・レオニーナは工事休止の公式案内があるため利用候補から除外。'
    (ROOT/'data/daily-essentials.json').write_text(json.dumps(essentials,ensure_ascii=False,indent=2)+'\n')
    print(f'WC {len(wc)}, food/shop/occasion {len(places)}, total {len(wc)+len(places)}; main 85 spots untouched')
if __name__=='__main__':main()
