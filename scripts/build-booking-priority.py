"""2/1出発案の予約一覧を、同じデータからWebと記録へ出力。"""
import html, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/booking-priority-feb01.json').read_text())
e=html.escape
links=lambda x:f'<a href="{e(x["url"],quote=True)}" target="_blank" rel="noopener noreferrer">公式・予約 ↗</a> · <a href="{e(x["rule"],quote=True)}" target="_blank" rel="noopener noreferrer">条件の出典 ↗</a>'
cards=''.join(f'<article class="card"><p class="overline">{e(x["when"])}</p><h2>{e(x["name"])}</h2><p class="tag">{e(x["visit"])}</p><p><strong>{e(x["status"])}</strong></p><p>{e(x["action"])}</p><p class="subtle">{links(x)}</p></article>' for x in d['actions'])
concerns=''.join(f'<li><strong>{e(x["title"])}</strong><p>{e(x["text"])}</p><a href="{e(x["source"],quote=True)}">公式の案内 ↗</a></li>' for x in d['concerns'])
page=f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(d['title'])}｜ふたりの旅手帖</title><link rel="stylesheet" href="assets/companion.css"><style>main{{max-width:1100px;margin:auto;padding-bottom:60px}}.booking-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,310px),1fr));gap:16px}}.booking-grid .card{{margin:0}}.concerns{{padding-left:22px}}.concerns li{{margin-bottom:26px}}.concerns p{{margin:6px 0}}.top{{height:auto;padding:24px}}@media(max-width:600px){{main{{padding:24px 20px}}}}</style><header class="top"><a class="brand" href="./">✦ ふたりの旅手帖</a><a href="./">ホームへ</a></header><main><p class="overline">BEFORE YOU BOOK · {e(d['checked'])}確認</p><h1>{e(d['title'])}</h1><p>{e(d['basis'])}</p><p class="subtle">{' → '.join(map(e,d['route']))}</p><article class="card"><h2>先に決めるのは、移動と一日の配分</h2><p>航空・宿泊と日帰りの往復交通を確認し、時間指定の観光と記念日ディナーを合わせます。発売前のものは開始目安を残し、売切れと混同しません。</p></article><h2>気になる日程と、調整すること</h2><ol class="concerns">{concerns}</ol><h2>予約の優先順</h2><div class="booking-grid">{cards}</div><p class="subtle" style="margin-top:25px">{e(d['limits'])}</p><a class="button" href="./">旅手帖へ戻る</a></main></html>'''
(R/'booking.html').write_text(page+'\n')
md=f"# {d['title']}\n\n{d['checked']}確認。{d['basis']}\n\n"+' → '.join(d['route'])+'\n\n## 日程の懸念\n\n'
for x in d['concerns']:md+=f"### {x['title']}\n\n{x['text']} [公式案内]({x['source']})\n\n"
md+='## 予約の優先順\n\n'
for x in d['actions']:md+=f"### {x['name']}｜{x['visit']}\n\n- いつ：{x['when']}\n- 確認状態：{x['status']}\n- 対応：{x['action']}\n- [公式・予約]({x['url']}) / [条件の出典]({x['rule']})\n\n"
md+='## 限界\n\n'+d['limits']+'\n'
(R/'docs/booking-priority-feb01.md').write_text(md)
print('booking guide:',len(d['actions']),'actions,',len(d['concerns']),'concerns')
