"""公式確認の差分をCSV・予約先頭文・候補データへ適用（クラウド書込なし）。"""
import csv,json
from pathlib import Path
D=Path(__file__).resolve().parents[1]/'data'
def load(n):return json.loads((D/n).read_text())
def save(n,v):(D/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
a=load('booking-verification-2027.json')['spots']; changes={x['no']:x for x in a}
g=load('reservation-weather-guide.json'); guide={x['no']:x for x in g}
with (D/'honeymoon-61-photo-index.csv').open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);header=r.fieldnames;rows=list(r)
for r in rows:
 x=changes.get(r['連番'])
 if not x:continue
 q=guide[x['no']];old=q['prefix'];q['reservation']=x['release_rule']+'｜'+x['release'];q['updated']=x['checked']
 q['prefix']=f"🎟 予約：{q['reservation']}\n訪問想定：{x['visit']}（2/1出発主案・未予約）\n公式・予約：{q['official_url'] or x['booking_url'] or x['source'].splitlines()[0]}\n{q['weather']}\n確認区分：{x['scope']}\n\n"
 memo=r['メモ'];assert memo.startswith(old),(x['no'],'prefix mismatch');r['メモ']=q['prefix']+memo[len(old):]
 for key,field in [('入場料金（大人）','fee'),('営業時間（現地）','hours'),('定休日・注意','caution'),('情報源（公式優先）','source'),('確認状況','scope'),('確認日','checked')]:r[key]=x[field]
with (D/'honeymoon-61-photo-index.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=header,lineterminator='\n');w.writeheader();w.writerows(rows)
save('reservation-weather-guide.json',g)
e=load('expansion-places.json')
for x in e:
 if x['no'] not in changes:continue
 b=changes[x['no']]
 x.update(fee=b['fee'],hours=b['hours'],closed=b['caution'],reservation=guide[x['no']]['reservation'],confirmed=b['scope'],checked=b['checked'],booking_verification_source=b['source'])
save('expansion-places.json',e)
with (D/'mymaps-61-import.csv').open(encoding='utf-8-sig',newline='') as f:r=csv.DictReader(f);mh=r.fieldnames;m=list(r)
by={r['スポット名']:r for r in rows}
for r in m:
 s=by[r['Name']]
 if s['連番'] in changes:r['Description']=s['メモ']+f"\n\n料金：{s['入場料金（大人）']}\n営業時間：{s['営業時間（現地）']}\n休み・注意：{s['定休日・注意']}\n確認：{s['確認日']}\n出典：{s['情報源（公式優先）']}"
with (D/'mymaps-61-import.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=mh,lineterminator='\n');w.writeheader();w.writerows(m)
print('更新対象',len(a),'件／CSV',len(rows),'件／列',len(header))
