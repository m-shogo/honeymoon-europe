import fs from 'node:fs';
import assert from 'node:assert/strict';

const data = JSON.parse(fs.readFileSync(new URL('../data/itinerary-12days.json', import.meta.url)));
const rules = JSON.parse(fs.readFileSync(new URL('../data/venue-rules.json', import.meta.url)));
const csv = fs.readFileSync(new URL('../data/spot-catalog.csv', import.meta.url), 'utf8');
const fail = msg => { throw new Error(msg); };
assert.equal(data.important.source_spot_count, 47);
assert.equal(data.days.length, 12, '12日間の必須行が欠落');
assert.deepEqual(data.days.map(d => d.day), Array.from({length:12},(_,i)=>i+1));
const originals = data.spots.filter(s => s.origin === 'uploaded_47_spots_xlsx');
assert.equal(originals.length, 47, '元の47スポットが消えている');
assert.deepEqual(originals.map(s=>s.id), Array.from({length:47},(_,i)=>String(i+1).padStart(3,'0')),'元IDが破損');
assert.equal(new Set(data.spots.map(s=>s.id)).size,data.spots.length,'スポットID重複');
assert.equal(new Set(data.spots.map(s=>s.city+'|'+s.name)).size,data.spots.length,'名前重複');
const valid = new Set(data.spots.map(s=>s.id));
const visited = new Set();
for (const day of data.days) {
 assert.ok(day.dinner?.name, '夕食未指定: DAY'+day.day);
 assert.ok(day.events.length>0, '予定未指定: DAY'+day.day);
 for (const e of day.events) {
  for (const id of e.spot_ids||[]) {assert.ok(valid.has(id),'未登録の訪問地点 '+id);visited.add(id);}
  if(e.start && e.end) assert.ok(e.start<e.end, '時刻の前後関係: DAY'+day.day);
 }
}
for(const spot of data.spots) assert.equal(spot.visit_status, visited.has(spot.id)?'予定':'今回は見送り','予定フラグが一致しない '+spot.id);
assert.ok(data.days[9].events.some(e=>(e.spot_ids||[]).includes('061')),'モンサンミッシェル修道院が抜けた');
assert.ok(data.days[10].events.some(e=>(e.spot_ids||[]).includes('052')),'ルーブルが抜けた');
assert.deepEqual(data.days.slice(1,4).map(d=>d.city), ['バルセロナ','バルセロナ','バルセロナ']);
assert.deepEqual(data.days.slice(4,6).map(d=>d.city), ['ローマ','ローマ']);
assert.deepEqual(data.days.slice(6,8).map(d=>d.city), ['ベネチア','ベネチア']);
assert.equal(data.days[8].city,'パリ');assert.equal(data.days[9].city,'ノルマンディー');assert.equal(data.days[10].city,'パリ');
assert.ok(data.important.hard_truth.includes('DAY13'),'日本到着翌日の注意が抜けた');
assert.ok(data.important.time_model.includes('仮'),'未確定時刻を確定値として扱っている');
assert.ok(['009','052','034','006'].every(id=>rules.some(r=>r.spot_id===id)),'重要な休館ルールがない');
const originalNames=originals.map(s=>s.name);
const headers=['id','city','name','category','origin','visit_status','not_scheduled_reason'];
assert.ok(csv.startsWith(headers.map(x=>'"'+x+'"').join(',')),'CSVの列変更');
for(const name of originalNames) assert.ok(csv.includes('"'+name+'"'),'CSVで元スポットが消失: '+name);
for(const day of data.days.slice(1,11)) assert.ok(day.dinner,'観光日の夕食がない');
console.log('OK: 12日、元47件＋追加'+(data.spots.length-47)+'件、夕食12枠、休館ルール、Mont Saint-Michel、ID/CSV整合');
