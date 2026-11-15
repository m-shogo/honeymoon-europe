"""既存の座標・写真出典を保持して都市別のMy Maps用KMLを作る。"""
import copy,csv,html,json,xml.etree.ElementTree as E
from pathlib import Path
root=Path(__file__).resolve().parents[1];data=root/'data';ns='http://www.opengis.net/kml/2.2';N={'k':ns};E.register_namespace('',ns)
rows=list(csv.DictReader((data/'honeymoon-61-photo-index.csv').open(encoding='utf-8-sig')))
photos=json.loads((data/'original-photo-registration-001-047.json').read_text())+json.loads((data/'paris-added-spots-048-061.json').read_text());by_no={p['no']:p for p in photos}
coords={p['name']:p['coords'].split(', ') for p in json.loads((data/'mymaps-original-coordinates-61.json').read_text())}
old=E.parse(data/'mymaps-category-styles.kml').getroot().find('k:Document',N)
styles=[copy.deepcopy(x) for x in old if x.tag.split('}')[-1] in ('Style','StyleMap')]
colors={'観光スポット':'0288D1','お土産・商店街':'0F9D58','食事・市場':'F57C00'};emojis={'観光スポット':'🔵','お土産・商店街':'🟢','食事・市場':'🟠'}
def make_doc(name):
 kml=E.Element('{'+ns+'}kml');doc=E.SubElement(kml,'{'+ns+'}Document');E.SubElement(doc,'{'+ns+'}name').text=name
 for style in styles:doc.append(copy.deepcopy(style))
 return kml,doc
all_root,all_doc=make_doc('新婚旅行｜61スポット 写真付き・都市別ガイド');folder=data/'mymaps-city-layers';folder.mkdir(exist_ok=True)
for index,city in enumerate(dict.fromkeys(r['都市'] for r in rows),1):
 kml,doc=make_doc(city);all_folder=E.SubElement(all_doc,'{'+ns+'}Folder');E.SubElement(all_folder,'{'+ns+'}name').text=city
 for r in [x for x in rows if x['都市']==city]:
  p=by_no[r['連番']];image=p['image_url']; esc=html.escape
  lines=[f"{emojis[r['色分け']]} {r['色分け']} {r['優先度']}",f"見どころ：{r['メモ']}",f"料金：{r['入場料金（大人）']}",f"営業時間：{r['営業時間（現地）']}",f"休み・注意：{r['定休日・注意']}",f"滞在目安：{r['滞在目安']}",f"近くで回る：{r['近くで回るスポット']}",f"食べ物：{r['おすすめの食べ物']}",f"お土産：{r['おすすめのお土産']}"]
  desc=f'<img src="{esc(image,quote=True)}" height="220" width="auto"><br><br>'+'<br>'.join(esc(x) for x in lines)+'<br><br>'
  if r['予約サイト（公式）']:desc+=f'<a href="{esc(r["予約サイト（公式）"],quote=True)}">公式・予約ページ</a><br>'
  elif r['情報源（公式優先）']:desc+=f'<a href="{esc(r["情報源（公式優先）"].split(" | ")[0],quote=True)}">公式案内</a><br>'
  desc+=f'<a href="{esc(r["Googleマップ検索"],quote=True)}">Googleマップで開く</a><br>'
  desc+=f'<a href="{esc(p["drive_url"],quote=True)}">保存した写真</a><br>'
  desc+=f"確認：{esc(r['確認日'])}／訪問日の料金・営業は再確認<br>"
  desc+=f"写真：{esc(p.get('author','要確認'))}／{esc(p.get('license','要確認'))}<br>"
  desc+=f'<a href="{esc(p["source_url"],quote=True)}">写真の出典</a>'
  if p.get('license_url'):desc+=f'・<a href="{esc(p["license_url"],quote=True)}">利用条件</a>'
  else:desc+='<br>写真の再利用条件は要確認（既存資料の写真）'
  placemark=E.Element('{'+ns+'}Placemark',id='spot-'+r['連番']);E.SubElement(placemark,'{'+ns+'}name').text=r['スポット名'];E.SubElement(placemark,'{'+ns+'}description').text=desc
  E.SubElement(placemark,'{'+ns+'}styleUrl').text='#icon-1899-'+colors[r['色分け']]
  ext=E.SubElement(placemark,'{'+ns+'}ExtendedData');el=E.SubElement(ext,'{'+ns+'}Data',name='gx_media_links');E.SubElement(el,'{'+ns+'}value').text=image
  point=E.SubElement(placemark,'{'+ns+'}Point');lat,lon=coords[r['スポット名']];E.SubElement(point,'{'+ns+'}coordinates').text=f'{lon},{lat},0'
  doc.append(placemark);all_folder.append(copy.deepcopy(placemark))
 E.ElementTree(kml).write(folder/f'{index:02}_{city}.kml',encoding='utf-8',xml_declaration=True)
E.ElementTree(all_root).write(data/'mymaps-61-photos-city-layers.kml',encoding='utf-8',xml_declaration=True)
for generated in [data/'mymaps-61-photos-city-layers.kml',*folder.glob('*.kml')]:
 generated.write_bytes(b'\n'.join(line.rstrip(b' \t') for line in generated.read_bytes().split(b'\n')))
assert len(all_doc.findall('.//k:Placemark',N))==61
print('KML: 61件・写真61件・元の座標61件・4都市＋ノルマンディーのレイヤー用ファイル')
