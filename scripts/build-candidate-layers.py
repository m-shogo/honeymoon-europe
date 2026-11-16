"""都市別再構築KMLから、候補だけの追加レイヤーを切り出す。"""
import copy, json, xml.etree.ElementTree as E
from pathlib import Path
DATA = Path(__file__).resolve().parents[1] / 'data'
ns = {'k':'http://www.opengis.net/kml/2.2'}
E.register_namespace('', ns['k'])  # My Mapsはns0接頭辞付きの出力を拒否する。
source = E.parse(DATA/'mymaps-61-photos-city-layers.kml')
places = json.loads((DATA/'expansion-places.json').read_text())
points = {p.attrib['id'].removeprefix('spot-'):p for p in source.findall('.//k:Placemark',ns)}
styles = source.findall('k:Document/k:Style',ns)+source.findall('k:Document/k:StyleMap',ns)
for group, name, filename in [('定番候補','追加の定番候補（未決定）','standard-candidates.kml'),('映画・アニメ寄り道','🎬映画・アニメ寄り道（未決定）','film-detours.kml')]:
    root=E.Element('{'+ns['k']+'}kml')
    doc=E.SubElement(root,'{'+ns['k']+'}Document')
    E.SubElement(doc,'{'+ns['k']+'}name').text=name
    for style in styles:doc.append(copy.deepcopy(style))
    for p in places:
        if p['group']==group:doc.append(copy.deepcopy(points[p['no']]))
    # 補助項目は説明に含める。別列にするとピンの説明が横に広がるため作らない。
    E.ElementTree(root).write(DATA/'mymaps-additions'/filename,encoding='utf-8',xml_declaration=True)
print('OK: 定番候補16件・映画アニメ寄り道7件のKMLを生成')
