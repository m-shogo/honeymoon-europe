"""出典ページで確認した場面画像を旅行用参考資料として取得する。"""
from pathlib import Path
import concurrent.futures,json,urllib.request,hashlib
p=Path(__file__).resolve().parents[1]/'data';out=p/'scene-images';out.mkdir(exist_ok=True)
bfi='https://www.bfi.org.uk/features/roman-holiday-rome-locations-audrey-hepburn-gregory-peck';root='https://core-cms.bfi.org.uk/sites/default/files/styles/responsive/public/2025-04/'
a=[{'id':'lupin-louvre','spots':['052'],'work':'LUPIN／ルパン','url':'https://parisjetaime.com/data/layout_image/25062_Lupin-le-Louvre--630x405--%40-Emmanuel-Guimier-Netflix_landscape_3-2_xs.jpg?ver=1700735208','source':'https://parisjetaime.com/article/balade-dans-le-paris-de-lupin-netflix-a1100','credit':'© Emmanuel Guimier / Netflix','caption':'清掃員に扮したアサンとルーブル。S1冒頭の強盗に関係する場面。'}, {'id':'spiderman-venice','spots':['033','036'],'work':'スパイダーマン：ファー・フロム・ホーム','url':'https://www.italyformovies.it/app/img/film/6913/spider_man_far_from_home_1_1587118143.webp','source':'https://www.italyformovies.it/film-serie-tv-games/detail/6913/spiderman-far-from-home','credit':'© Sony','caption':'ヴェネツィアでのピーター。観光中の場面参考（ピン位置と同じ撮影角度を保証しない）。'}, {'id':'amelie-cafe','spots':['083'],'work':'アメリ','url':'https://cdn.paris.fr/paris/2026/04/08/huge-9cdb5f45af53cbf8fc57ac5abe211531.jpg','source':'https://www.paris.fr/en/pages/what-if-we-rediscovered-paris-through-the-eyes-of-amelie-poulain-34990','credit':'© Studiocanal GmbH','caption':'アメリの場面写真。勤務先カフェの作品参考。'}]
for id,spots,file,caption in [('roman-steps',['018'],'roman-holiday-1953-ann-with-gelato.jpg','アン王女がスペイン階段でジェラートを食べる場面。'),('roman-truth',['062'],'roman-holiday-1953-ann-joe-and-irving-looking-at-statue.jpg','真実の口を訪れたアン、ジョー、アーヴィング。'),('roman-forum',['021'],'roman-holiday-1953-peck-against-carved-stone-monument.jpg','ジョーがアンと出会うフォロ・ロマーノ周辺の場面。'),('roman-margutta',['084'],'roman-holiday-1953-big-open-doors.jpg','ジョーの住居へ入る場面の入口。実在する私有建物は外観のみ。'),('roman-castel',['030'],'roman-holiday-1953-dance-floor.jpg','サンタンジェロ城近く、テヴェレ川沿いのダンスの場面。')]:a.append({'id':id,'spots':spots,'work':'ローマの休日','url':root+file+'/1440x0/'+file,'source':bfi,'credit':'Roman Holiday (1953) / rights holders; BFI掲載場面写真','caption':caption})
# 保存済みのDrive対応と追加選定を保持する。
old={x['id']:x for x in json.loads((p/'film-scene-images.json').read_text())} if (p/'film-scene-images.json').exists() else {}
a=[{**old.get(x['id'],{}),**x} for x in a]+[x for key,x in old.items() if key not in {y['id'] for y in a}]
def fetch(x):
 b=urllib.request.urlopen(urllib.request.Request(x['url'],headers={'User-Agent':'Mozilla/5.0','Referer':x['source']}),timeout=30).read();suffix='.webp' if '.webp' in x['url'] else '.jpg';x['filename']=x['id']+suffix;(out/x['filename']).write_bytes(b);x['sha256']=hashlib.sha256(b).hexdigest();x['rights']='作品画像。フリーライセンスとは扱わず、作品・権利者・掲載元を記録。';return x
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:a=list(pool.map(fetch,a))
(p/'film-scene-images.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
from PIL import Image,ImageDraw
im=Image.new('RGB',(1000,((len(a)+3)//4)*220),'white');dr=ImageDraw.Draw(im)
for i,x in enumerate(a):
 z=Image.open(out/x['filename']).convert('RGB');z.thumbnail((245,190));x0=i%4*250;y=i//4*220;im.paste(z,(x0,y));dr.text((x0,y+195),x['id'],fill='black')
im.save(out/'contact.jpg');print('場面画像取得',len(a))
