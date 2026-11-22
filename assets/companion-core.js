(function(root){'use strict';
const Core={
 dateKey(d=new Date(),tz='Europe/Paris'){return new Intl.DateTimeFormat('en-CA',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit'}).format(d);},
 days(start){if(!/^\d{4}-\d{2}-\d{2}$/.test(start||''))return [];const d=new Date(start+'T12:00:00Z');if(Number.isNaN(+d)||d.toISOString().slice(0,10)!==start)return [];return Array.from({length:14},(_,i)=>new Date(+d+i*86400000).toISOString().slice(0,10));},
 scheduleWarnings(start,routes={},db={}){
  const dates=this.days(start),rules=db.scheduleRules?.rules||[],items=[];
  // 到着日の見学開始は保証された時刻ではなく、本人の移動案から置く目安。
  const cities=[null,'ヴェネツィア','ヴェネツィア','ローマ','ローマ','バルセロナ','バルセロナ','バルセロナ','パリ','パリ','パリ','ノルマンディー','パリ',null];
  const arrivals={2:870,4:900,6:960,9:1170},names=new Map([...(db.spots||[]),...(db.places||[])].map(p=>[p.id,p]));
  dates.forEach((date,i)=>{
   const day=i+1,weekday=new Date(date+'T12:00:00Z').getUTCDay(),assigned=routes['day'+day]||[];
   const add=(id,name,level,text,source='',planned=false)=>items.push({day,date,id,name,level,text,source,planned});
   for(const r of rules){
    const planned=assigned.includes(r.id);if(!planned&&r.city!==cities[i])continue;
    if(planned&&names.get(r.id)?.city!==cities[i])add(r.id,r.name,'check','この日の標準の滞在都市と違います。移動を含めて日程を確認してください。',r.source,true);
    const lastSunday=weekday===0&&new Date(Date.UTC(Number(date.slice(0,4)),Number(date.slice(5,7))-1,Number(date.slice(8))+7)).getUTCMonth()!==Number(date.slice(5,7))-1;
    const closed=(r.closedWeekdays||[]).includes(weekday)&&!(r.exceptLastSunday&&lastSunday)||(r.closedMonthDays||[]).includes(date.slice(5))||(r.closedDates||[]).includes(date);
    if(closed){add(r.id,r.name,planned?'closed':'caution','通常の定休日・休館日に当たります。'+r.advice,r.source,planned);continue;}
    if(r.exceptLastSunday&&lastSunday)add(r.id,r.name,'check','最終日曜の公開は通常と時間・入場条件が異なります。公式カレンダーを確認してください。',r.source,planned);
    if(r.notice)add(r.id,r.name,'check',r.notice,r.source,planned);
    const inSeason=!r.months||r.months.includes(Number(date.slice(5,7)));
    if(!inSeason&&(r.cutoff!=null||r.cutoffByWeekday))add(r.id,r.name,'check','この季節の営業時間は自動判定に未登録です。訪問日の公式時間を確認してください。',r.source,planned);
    const cutoff=inSeason?(r.cutoffByWeekday?.[weekday]??r.cutoff):null;
    if(cutoff!=null){const time=String(Math.floor(cutoff/60)).padStart(2,'0')+':'+String(cutoff%60).padStart(2,'0');
     if(arrivals[day]!=null&&arrivals[day]>=cutoff)add(r.id,r.name,'caution','移動日の見学開始目安より早い'+time+'に閉場・最終入場。到着後に間に合う前提にしないでください。',r.source,planned);
     else if(r.early||planned)add(r.id,r.name,'caution',time+'閉場・最終入場が目安。'+r.advice,r.source,planned);
    }
   }
   for(const id of assigned){const p=names.get(id);if(!p){add(id,'保存した場所','check','現在のガイドに見つかりません。場所を選び直してください。','',true);continue;}
    if(!rules.some(r=>r.id===id)){add(id,p.name,'check','この場所の曜日・臨時休業の自動判定は未登録です。公式情報を確認してください。',p.official||p.source?.split('\n')[0]||'',true);if(p.city!==cities[i])add(id,p.name,'check','この日の標準の滞在都市と違います。移動を確認してください。','',true);}
   }
   if(cities[i]==='バルセロナ'&&weekday===0)add('sunday-shopping','市場・商店街・スーパー','caution','日曜は市場と一般店舗の休業に注意。通りの散策と店舗の営業は別です。食事は営業確認済みの店へ。','https://bid.barcelonaturisme.com/wv3/en/page/4669/shops-opening-hours-and-tax-free-.html');
   if(day===12&&weekday>0&&weekday<6&&[1,2,3,4,10,11,12].includes(Number(date.slice(5,7))))add('mont-transport','モンサンミッシェルの往復交通','check','冬のパリ直通NOMAD列車は原則週末。平日の往復交通・季節ダイヤを先に確認してください。','https://www.montsaintmichel.gouv.fr/acceder-au-mont-saint-michel/venir-au-mont-saint-michel');
  });
  return {dates,items,checked:db.scheduleRules?.checked||'',outsideYear:dates.length>0&&dates.some(d=>d.slice(0,4)!==String(db.scheduleRules?.year)),basis:'都市順・ホテル11泊の標準案で再計算。追加した場所はその日を優先して判定します。到着日の目安は便・列車の変更に自動追従しません。'};
 },
 distance(a,b){const valid=x=>Array.isArray(x)&&x.length===2&&x.every(Number.isFinite)&&Math.abs(x[0])<=90&&Math.abs(x[1])<=180;if(!valid(a)||!valid(b))return null;const rad=v=>v*Math.PI/180,dlat=rad(b[0]-a[0]),dlon=rad(b[1]-a[1]);const h=Math.sin(dlat/2)**2+Math.cos(rad(a[0]))*Math.cos(rad(b[0]))*Math.sin(dlon/2)**2;return 6371000*2*Math.asin(Math.sqrt(Math.min(1,h)));},
 nearest(place,candidates,limit=3,maxMeters=2000){return candidates.filter(p=>p.id!==place.id&&p.city===place.city).map(p=>({place:p,meters:this.distance(place.coords,p.coords)})).filter(x=>x.meters!==null&&x.meters<=maxMeters).sort((a,b)=>a.meters-b.meters).slice(0,limit);},
 myMap(coords,zoom=15){const u=new URL('https://www.google.com/maps/d/viewer');u.searchParams.set('mid','1gKS7F8p3_YdS952P8K2jDE28-1epSAM');if(this.distance(coords,coords)===0){u.searchParams.set('ll',coords.join(','));u.searchParams.set('z',String(zoom));}return u.href;},
 search(query){return 'https://www.google.com/maps/search/?'+new URLSearchParams({api:'1',query});},
 directions(points,mode='walking',origin=''){const p=points.filter(Boolean);if(!p.length)return '';const q={api:'1',travelmode:mode,destination:p.at(-1)};if(origin)q.origin=origin;else if(p.length>1)q.origin=p[0];const middle=origin?p.slice(0,-1):p.slice(1,-1);if(mode==='walking'&&middle.length)q.waypoints=middle.slice(0,3).join('|');return 'https://www.google.com/maps/dir/?'+new URLSearchParams(q);},
 yen(eur,rate){const a=Number(eur),b=Number(rate);return Number.isFinite(a)&&Number.isFinite(b)&&a>=0&&b>0?Math.round(a*b):null;},
 escape(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));},
 normalize(raw){if(!raw||raw.version!==1)throw new Error('この旅手帖のバックアップではありません');const s=raw.state;if(!s||!Array.isArray(s.saved)||!Array.isArray(s.expenses)||!s.hotels||typeof s.hotels!=='object')throw new Error('保存データの形式を確認できません');if(s.expenses.length>10000||JSON.stringify(s).length>3000000)throw new Error('データが大きすぎます');const allowed=['venice','rome','barcelona','paris'];const hotels=Object.fromEntries(allowed.map(k=>[k,String(s.hotels[k]||'').slice(0,500)]));return {city:allowed.includes(s.city)?s.city:'venice',mode:s.mode==='during'?'during':'before',start:this.days(s.start).length?s.start:'',saved:[...new Set(s.saved.filter(v=>typeof v==='string'))].slice(0,300),routes:Object.fromEntries(Object.entries(s.routes||{}).filter(([k,v])=>/^day\d+$/.test(k)&&Array.isArray(v)).map(([k,v])=>[k,v.filter(x=>typeof x==='string').slice(0,5)])),hotels,rate:Number(s.rate)>0&&Number(s.rate)<100000?Number(s.rate):'',rateDate:String(s.rateDate||'').slice(0,30),expenses:s.expenses.filter(x=>x&&Number.isFinite(x.amount)&&x.amount>0&&x.amount<1000000).map(x=>({id:String(x.id).slice(0,80),amount:x.amount,label:String(x.label||'').slice(0,100),payer:x.payer==='partner'?'partner':'me',date:String(x.date||'').slice(0,30)})),checks:Array.isArray(s.checks)?s.checks.filter(x=>typeof x==='string').slice(0,40):[],day:Math.max(1,Math.min(14,Number(s.day)||1))};}
};if(typeof module!=='undefined')module.exports=Core;root.TripCore=Core;
})(typeof window!=='undefined'?window:globalThis);
