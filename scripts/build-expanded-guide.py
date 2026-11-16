"""追加候補と作品情報を、既存ID・列スキーマを保って統合する。"""
import csv,json,html,xml.etree.ElementTree as E,copy
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'data';a=json.loads((p/'expansion-places.json').read_text());films=json.loads((p/'film-location-notes.json').read_text());scenes=json.loads((p/'film-scene-images.json').read_text());byfilm={};byscene={}
for f in films:byfilm.setdefault(f['no'],[]).append(f)
for s in scenes:
 for no in s['spots']:byscene.setdefault(no,[]).append(s)
def movie_text(no):
 fs=byfilm.get(no,[])
 if not fs:return ''
 lines=['🎬 作品・場面（ネタバレあり）']
 for f in fs:lines += [f"作品：{f['work']}",f"関係：{f['relation']}",f"場面：{f['scene']}",f"確認：{f['status']}",f"出典：{f['source']}"]
 for s in byscene.get(no,[]):lines += [f"場面画像：{s['caption']}",f"{s['credit']}／{s['source']}",f"保存した場面画像：{s['drive_url']}"]
 return '\n'.join(lines)
def write(name,headers,rows):
 with (p/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=headers,lineterminator='\n');w.writeheader();w.writerows(rows)
f=p/'honeymoon-61-photo-index.csv';r=csv.DictReader(f.open(encoding='utf-8-sig'));headers=r.fieldnames;rows=list(r);assert len(rows)==62,'この統合は62件の正本へ一度だけ適用する'
for x in a:
 no=x['no'];food={'パリ':'周辺でクロワッサン・クレープ・カフェ','バルセロナ':'周辺でタパス・ボカディージョ','ローマ':'周辺でジェラート・ローマ風パスタ','ヴェネツィア':'周辺でチケッティ・バカラ・マンテカート'}[x['city']];souvenir={'パリ':'施設ショップの絵はがき・美術作品や建築の雑貨','バルセロナ':'モデルニスモ建築の絵はがき・地元雑貨','ローマ':'ローマの街並み・映画の絵はがき','ヴェネツィア':'ヴェネツィアの絵はがき・ガラス小物（産地を確認）'}[x['city']]
 if no=='083':food='映画にちなむクレームブリュレ・カフェ（提供・価格は店頭確認）'
 x['food']=food;x['souvenirs']=souvenir
 memo=f"🎟 予約：{x['reservation']}\n公式・案内：{x['official']}\n{x['weather']}\n\n候補区分：{x['group']}／判断：{x['visit_status']}\n{x['highlight']}\n選ぶ・見送る判断：{x['decision']}"
 row=dict(zip(headers,[no,x['filename'],'写真_映え版_85スポット/'+x['filename'],x['city'],x['name'],x['category'],x['priority'],x['query'],x['fee'],x['hours'],x['closed'],x['official'],x['nearby'],food,souvenir,x['duration'],memo,x['official'],x['confirmed'],x['checked'],x['image_url'],x['source_url'],x['maps_url'],x['visit_status'],'Drive保存済み／地図の写真表示は検証待ち']))
 rows.append(row)
for r in rows:
 r['Drive相対パス']='写真_映え版_85スポット/'+r['画像ファイル名'];m=movie_text(r['連番'])
 if m:r['メモ']+='\n\n'+m
write('honeymoon-61-photo-index.csv',headers,rows)
# 新規行のシートA:Yを明示し、既存行の書換えに利用しない。
sheet_headers=['都市','スポット名','色分け','優先度','場所検索','入場料金（大人）','営業時間（現地）','定休日・注意','予約サイト（公式）','近くで回るスポット','おすすめの食べ物','おすすめのお土産','滞在目安','メモ','情報源（公式優先）','確認状況','確認日','写真URL','写真出典URL','Googleマップ検索','訪問状態','写真No.','写真ファイル名','写真（Google Drive）','写真選定']
new={x['no']:x for x in a}
for r in rows[62:]:
 x=new[r['連番']];s=dict(r,**{'写真No.':r['連番'],'写真ファイル名':r['画像ファイル名'],'写真（Google Drive）':x['drive_url']});x['sheet_values']=[s[h] for h in sheet_headers]
(p/'expansion-places.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
# 出典索引・クレジット表は同じ正本の件数に同期。
h=['連番','スポット名','画像ファイル名','写真出典URL','写真選定'];write('photo-source-index-61.csv',h,[{k:r[k] for k in h} for r in rows])
f=p/'photo-credits-001-061.csv';rr=csv.DictReader(f.open(encoding='utf-8-sig'));h=rr.fieldnames;cr=list(rr)
for x in a:cr.append({k:({'no':x['no'],'name':x['name'],'author':x['author'],'license':x['license'],'license_url':x['license_url'],'source_url':x['source_url'],'image_url':x['image_url'],'drive_url':x['drive_url'],'rights_status':'Commons利用条件確認済み／代表写真'}).get(k,'') for k in h})
write('photo-credits-001-061.csv',h,cr)
h=['Name','Description','Address or Query','City','Category','Photo URL','Google Maps URL'];write('mymaps-61-import.csv',h,[dict(zip(h,[r['スポット名'],r['メモ'],r['場所検索'],r['都市'],r['色分け'],r['写真URL'],r['Googleマップ検索']])) for r in rows])
f=p/'reservation-weather-guide.json';guide=json.loads(f.read_text())
for x in a:guide.append({'no':x['no'],'name':x['name'],'city':x['city'],'reservation':x['reservation'],'weather':x['weather'],'official_url':x['official'],'prefix':f"🎟 予約：{x['reservation']}\n公式・案内：{x['official']}\n{x['weather']}\n\n",'updated':'2026-11-16'})
f.write_text(json.dumps(guide,ensure_ascii=False,indent=2)+'\n')
# 既存のカタログID062・064を維持し、新IDのみ候補として登録。既存旅程は変更しない。
f=p/'spot-catalog.csv';rr=csv.DictReader(f.open());h=rr.fieldnames;catalog=list(rr);ids={r['id'] for r in catalog}
for x in a:
 if x['no'] not in ids:catalog.append(dict(zip(h,[x['no'],x['city'],x['name'],'映画・アニメ' if x['group']!='定番候補' else '観光','candidate_review_2026-11-16','未決定',x['decision']])))
with f.open('w',newline='') as o:w=csv.DictWriter(o,fieldnames=h,quoting=csv.QUOTE_ALL,lineterminator='\n');w.writeheader();w.writerows(catalog)
print('正本85件、代表写真85件、候補23件。既存62行の順序・IDを維持。')
