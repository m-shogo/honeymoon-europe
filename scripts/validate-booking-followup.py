"""11/17追補を直前Git版と比較し、3件以外の情報や採否・写真の保持を確認。"""
import csv,html,io,json,re,subprocess,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data';N={'k':'http://www.opengis.net/kml/2.2'};BASE='7fba88d';TARGET={'032','064','070'}
def previous(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=R)
def points(root):return {p.findtext('k:name',namespaces=N):p for p in root.findall('.//k:Placemark',N)}
def normalized(p):return re.sub(r'<img[^>]*>','',p.findtext('k:description','',N))
old=points(E.fromstring(previous('data/mymaps-booking-2027-export.kml')));new=points(E.parse(D/'mymaps-booking-2027-export.kml').getroot())
changed=[name for name in new if normalized(new[name])!=normalized(old[name])]
book=json.loads((D/'booking-verification-2027.json').read_text());targets={x['name'] for x in book['spots'] if x['no'] in TARGET}
assert set(changed)==targets,(changed,targets)
a=list(csv.DictReader(io.StringIO(previous('data/honeymoon-61-photo-index.csv').decode('utf-8-sig'))));b=list(csv.DictReader((D/'honeymoon-61-photo-index.csv').open(encoding='utf-8-sig')))
assert len(a)==len(b)==85
allow={'メモ','入場料金（大人）','営業時間（現地）','定休日・注意','情報源（公式優先）','確認状況','確認日'}
for before,after in zip(a,b):
 for key in before:
  if before['連番'] not in TARGET or key not in allow:assert before[key]==after[key],(before['連番'],key)
# 決済前の選択画面。これは購入済み・予約済みの記録ではない。
quote=(D/'disneyland-2027-02-10-price-ui.txt').read_text()
for text in ['Valid on 10 February 2027','Dated 1 Day/1 Park ticket','€75.00','€150.00','3 days before']:assert text in quote,text
vatican=(D/'vatican-2027-02-05-availability-ui.txt').read_text()
for text in ['05 febbraio 2027','Biglietti Musei Vaticani','Nessun tipo di visita è disponibile']:assert text in vatican,text
result={'checked':'2026-11-17','baseline_commit':BASE,'updated_spots':3,'untouched_map_descriptions':82,'spots':85,'csv_columns':len(b[0]),'unchanged_adoption_status':True,'disney_quote_adult_eur':75,'disney_quote_adults':2,'disney_quote_total_eur':150,'purchased':False,'vatican_no_matching_visit':True,'reason_of_vatican_unavailability':'unknown'}
(D/'booking-followup-2026-11-17-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
