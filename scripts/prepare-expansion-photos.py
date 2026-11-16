"""公式ページと照合するための追加候補写真をCommonsから取得する。"""
import concurrent.futures,hashlib,html,json,re,urllib.request
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data';a=json.loads((p/'expansion-places.json').read_text());pages=list(json.loads((p/'expansion-commons-metadata.json').read_text())['query']['pages'].values());by={x['title']:x for x in pages};options={'069':'Piazza del Campidoglio, Rome - 2498.jpg','070':'Basilica di San Giorgio Maggiore a Venezia Facciata d ingresso.jpg','074':"Musee d'Orsay and Pont Royal, North-West view 140402 1.jpg",'081':'La salle ovale du site Richelieu, Bibliothèque nationale de France, Paris 2022.jpg'}
for no,file in options.items():
 q=json.loads((p/f'expansion-photo-options-{no}.json').read_text())['query']['pages'];by.update({x['title']:x for x in q.values()});next(x for x in a if x['no']==no)['image_file']=file
out=p/'expansion-photos';out.mkdir(exist_ok=True)
clean=lambda s:html.unescape(re.sub('<[^>]+>','',s)).strip()
def fetch(x):
 info=by['File:'+x['image_file']]['imageinfo'][0];m=info['extmetadata'];url=info.get('thumburl',info['url']).split('?')[0];license=m.get('LicenseShortName',{}).get('value','要確認');assert license!='要確認',x['name']
 req=urllib.request.Request(url,headers={'User-Agent':'HoneymoonGuide/1.0 personal travel research'});b=urllib.request.urlopen(req,timeout=35).read();file=x['no']+'_'+x['name']+'.jpg';(out/file).write_bytes(b);x.update(filename=file,image_url=url,source_url=info['descriptionurl'],author=clean(m.get('Artist',{}).get('value','')),license=license,license_url=m.get('LicenseUrl',{}).get('value',''),bytes=len(b),sha256=hashlib.sha256(b).hexdigest());return x
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:a=list(pool.map(fetch,a))
(p/'expansion-places.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
from PIL import Image,ImageOps,ImageDraw
sheet=Image.new('RGB',(1000,((len(a)+3)//4)*180),'white');draw=ImageDraw.Draw(sheet)
for i,x in enumerate(a):
 im=Image.open(out/x['filename']).convert('RGB');im.thumbnail((245,150));x0=(i%4)*250;y0=(i//4)*180;sheet.paste(im,(x0,y0));draw.text((x0,y0+152),x['no']+' '+x['wiki_title'][:31],fill='black')
sheet.save(out/'contact.jpg');print('Downloaded',len(a),'photos')
