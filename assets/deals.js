'use strict';
(() => {
const {dataset:data,brief,briefCurrent} = JSON.parse(document.getElementById('gear-data').textContent);
const $=id=>document.getElementById(id), clone=x=>JSON.parse(JSON.stringify(x));
const escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeURL=value=>{try{const u=new URL(value);return ['https:','http:'].includes(u.protocol)?u.href:'#';}catch{return '#';}};
const dollars=x=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(x);
const date=x=>{const d=new Date(x);return Number.isFinite(d.getTime())?new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZone:'America/Denver',timeZoneName:'short'}).format(d):'Not verified';};
const age=x=>x&&Number.isFinite(Date.parse(x))?Math.max(0,(Date.now()-Date.parse(x))/3600000):Infinity;
const preferenceKey='gearDeals.preferences.v2',viewKey='gearDeals.view.v2';
function validate(p){
 if(!p||typeof p!=='object'||Array.isArray(p))throw Error('Expected a preferences object.');
 for(const k of ['my_ski_sizes','family_ski_sizes'])if(!Array.isArray(p[k])||p[k].some(n=>!Number.isInteger(n)||n<100||n>220))throw Error('Ski sizes must be whole numbers between 100 and 220.');
 for(const k of ['clothing_sizes','watch_terms','muted_terms','owned_terms','watch_urls','muted_urls','owned_urls'])if(p[k]!==undefined&&(!Array.isArray(p[k])||p[k].length>1000||p[k].some(v=>typeof v!=='string'||v.length>2000)))throw Error('Invalid '+k);
 for(const k of ['ski','clothing'])if(!Number.isFinite(p.max_prices?.[k])||p.max_prices[k]<=0||p.max_prices[k]>100000)throw Error('Enter valid positive budgets.');
 const normalized={...clone(data.preferences),...p};
 for(const k of ['act_now_hours','hide_cached_after_hours'])if(!Number.isFinite(normalized.freshness?.[k])||normalized.freshness[k]<1||normalized.freshness[k]>720)throw Error('Invalid freshness window.');
 for(const k of ['ski','clothing'])for(const key of ['amount','percent'])if(!Number.isFinite(normalized.price_drop_thresholds?.[k]?.[key])||normalized.price_drop_thresholds[k][key]<=0)throw Error('Invalid price drop threshold.');
 return normalized;
}
let preferences=clone(data.preferences),state={view:'today',search:'',sort:'relevance',store:'',drops:false,budget:true,hidden:false};
try{const p=JSON.parse(localStorage.getItem(preferenceKey)||'null');if(p)preferences=validate(p);const v=JSON.parse(localStorage.getItem(viewKey)||'null');if(v)state={...state,...v};}catch{}
// Start every ordinary visit with skis, regardless of the previously browsed category.
state.category='ski';
if(state.view==='clothing')state.view='today';
const params=new URLSearchParams(location.search);
for(const key of ['category','view','search','sort','store'])if(params.has(key))state[key]=params.get(key);
for(const key of ['drops','budget','hidden'])if(params.has(key))state[key]=params.get(key)==='1';
if(state.view==='clothing'){state.category='clothing';state.view='all';}
if(!['ski','clothing'].includes(state.category))state.category='ski';
if(state.category==='clothing'&&state.view==='family')state.view='today';
if(!['today','me','family','all'].includes(state.view))state.view='today';
function persist(){try{localStorage.setItem(preferenceKey,JSON.stringify(preferences));localStorage.setItem(viewKey,JSON.stringify(state));}catch{}}
function matches(d,sizes){return(d.sizes||[]).some(s=>(String(s).match(/\b\d{3}\b/g)||[]).some(n=>sizes.includes(Number(n))));}
function enrich(d){
 const hay=[d.title,d.source,d.url].join(' ').toLowerCase(),cat=d.category;
 const terms=key=>(preferences[key]||[]).some(t=>hay.includes(t.toLowerCase()));
 const muted=terms('muted_terms')||(preferences.muted_urls||[]).includes(d.url),owned=terms('owned_terms')||(preferences.owned_urls||[]).includes(d.url);
 const aliases={small:'s',medium:'m',large:'l','x-large':'xl'};
 const me=cat==='ski'?matches(d,preferences.my_ski_sizes):(d.sizes||[]).some(s=>preferences.clothing_sizes.includes(aliases[String(s).toLowerCase()]||String(s).toLowerCase()));
 const family=cat==='ski'&&matches(d,preferences.family_ski_sizes),fit=me||family,budget=d.current_price<=preferences.max_prices[cat];
 const fresh=!d.is_cached&&age(d.last_verified_at)<=preferences.freshness.act_now_hours;
 const verified=fit&&fresh&&d.stock_status==='in_stock'&&d.price_scope==='exact';
 const limits=preferences.price_drop_thresholds[cat],drop=fresh&&d.price_change<0&&(Math.abs(d.price_change)>=limits.amount||Math.abs(d.price_change_percent||0)>=limits.percent);
 const watched=terms('watch_terms')||(preferences.watch_urls||[]).includes(d.url);
 const lowest=d.observation_count>=3&&d.highest_price>d.lowest_price&&d.current_price<=d.lowest_price;
 const act=verified&&budget&&!muted&&!owned&&(drop||lowest);
 const active=preferences.shopping_intent?.[cat]==='active';
 const score=40*fit+20*verified+15*budget+12*watched+20*drop+10*lowest+5*active-100*(muted||owned)-30*!fresh;
 return {...d,me,family,fit,budget,fresh,verified,drop,watched,act,muted,owned,score};
}
function controls(){for(const k of ['search','sort','store'])$(k).value=state[k];for(const k of ['drops','budget','hidden'])$(k).checked=state[k];}
function storeOptions(){
 const stores=[...new Set(data.deals.filter(d=>d.category===state.category).map(d=>d.source))].sort();
 $('store').replaceChildren(new Option('All stores',''));
 for(const s of stores)$('store').append(new Option(s,s));
 if(!stores.includes(state.store))state.store='';
 controls();
}
storeOptions();
const recommendations=new Map((brief?.decisions||[]).map(r=>[r.id,r]));
function graph(d){const values=d.price_series||[];if(values.length<2)return '';const low=Math.min(...values),high=Math.max(...values),points=values.map((v,i)=>`${(i/(values.length-1)*84+2).toFixed(1)},${(24-(v-low)/(high-low||1)*22).toFixed(1)}`).join(' ');return `<svg class="sparkline" viewBox="0 0 88 26" role="img" aria-label="Observed price trend"><polyline fill="none" stroke="#246747" stroke-width="2" points="${points}"/></svg>`;}
function card(d){
 let verdict=d.act?'Act now':d.verified&&d.budget?'Worth watching':'Check details';
 const record=briefCurrent?recommendations.get(d.id):null;
 const caveats=[];if(d.price_scope!=='exact')caveats.push('Size-specific price unverified');if(!d.fresh)caveats.push('Not freshly verified');if(d.stock_status!=='in_stock')caveats.push(d.stock_status==='sold_out'?'Sold out':'Stock unknown');
 const evidence=d.observation_count?`${d.observation_count} verified checks since ${d.history_start}. Range ${dollars(d.lowest_price)}–${dollars(d.highest_price)}.`:'Verified offer history starts with the next successful refresh.';
 const offers=d.comparison?.offers||[];
 return `<article class="deal" data-id="${escape(d.id)}">${d.image_url?`<img class="thumb" src="${escape(safeURL(d.image_url))}" alt="${escape(d.title)}" loading="lazy">`:'<div class="thumb no-photo">No photo</div>'}<div><p class="eyebrow">${escape(d.source)}</p><h3>${escape(d.title)}</h3><p class="muted">${escape((d.sizes||[]).join(' · ')||'Size not listed')}${d.condition?' · '+escape(d.condition):''}</p><div class="badges"><span class="badge ${d.act?'good':''}">${verdict}</span>${d.me?'<span class="badge">Your size</span>':''}${d.family?'<span class="badge">Family size</span>':''}${d.drop?`<span class="badge good">Down ${dollars(Math.abs(d.price_change))}</span>`:''}${caveats.map(x=>`<span class="badge caution">${x}</span>`).join('')}</div>${record?`<p class="reason">${escape(record.reason)}</p>`:''}<div class="evidence">${graph(d)}<span>${escape(evidence)}</span></div><p class="muted">Last checked: ${escape(date(d.last_verified_at))}</p>${offers.length>1?`<details class="offer-list"><summary>Compare verified offers</summary>${offers.map(o=>`<p><a href="${escape(safeURL(o.url))}" target="_blank" rel="noopener">${escape(o.source)}</a> · ${dollars(o.price)}</p>`).join('')}</details>`:''}<div class="actions"><button data-action="watch" data-id="${escape(d.id)}" aria-pressed="${d.watched}">${d.watched?'Watching':'Watch'}</button><button data-action="mute" data-id="${escape(d.id)}">${d.muted?'Undo dismissal':'Not interested'}</button><button data-action="own" data-id="${escape(d.id)}">${d.owned?'Undo owned':'Already bought'}</button></div></div><div class="purchase"><p class="price">${d.price_scope!=='exact'?'<small>From</small>':''}${dollars(d.current_price)}</p><a class="button" href="${escape(safeURL(d.url))}" target="_blank" rel="noopener">View deal ↗</a></div></article>`;
}
function render(){
 const all=data.deals.filter(d=>d.category===state.category).map(enrich).filter(d=>!d.is_cached||age(d.last_verified_at)<=preferences.freshness.hide_cached_after_hours);
 const relevant=all.filter(d=>d.fit&&d.budget&&!d.muted&&!d.owned);
 const health=(data.source_health||[]).filter(s=>s.category===state.category);
 const healthy=health.filter(s=>s.status==='ok'&&age(s.last_verified_at)<=preferences.freshness.act_now_hours).length;
 $('freshness').textContent='Data refreshed '+date(data.generated_at);
 const incomplete=health.filter(s=>s.status==='degraded').length;
 const old=age(data.generated_at)>preferences.freshness.act_now_hours;
 $('status').className='status'+(old||incomplete?' warning':'');
 $('status').textContent=old?'This snapshot is older than your freshness window. Check retailer availability before acting.':incomplete?`${incomplete} stores have incomplete coverage. Unverified listings cannot qualify for Act now.`:'';
 $('metrics').innerHTML=[[relevant.length,'Matching offers'],[relevant.filter(d=>d.drop).length,'Meaningful drops'],[relevant.filter(d=>d.price_trend==='new').length,'New matches'],[`${healthy}/${health.length}`,'Stores checked successfully']].map(([n,t])=>`<div class="metric"><b>${n}</b><span>${t}</span></div>`).join('');
 for(const b of document.querySelectorAll('[data-category]'))b.setAttribute('aria-pressed',String(b.dataset.category===state.category));
 document.querySelector('[data-view=family]').hidden=state.category==='clothing';
 for(const b of document.querySelectorAll('[data-view]'))b.setAttribute('aria-pressed',String(b.dataset.view===state.view));
 const local=JSON.stringify(preferences)!==JSON.stringify(data.preferences);
 $('brief').hidden=state.view!=='today';
 $('brief').innerHTML=`<h2>${relevant.some(d=>d.act)?'Worth your attention':'No verified must-buy deals right now'}</h2><p class="muted">${brief?'Last successful brief: '+escape(date(brief.generated_at)): 'A validated buying brief will appear after the next successful scheduled run.'}${brief&&!briefCurrent?' The brief is from an earlier snapshot.':''}</p>${local?'<p class="muted">Your browser preferences differ from the saved brief settings. Export them to update future briefs.</p>':''}<a href="../deal-brief/">Read full brief →</a>`;
 const query=state.search.toLowerCase();let rows=all.filter(d=>(state.hidden||(!d.muted&&!d.owned))&&(!state.budget||d.budget)&&(!state.drops||d.drop)&&(!state.store||d.source===state.store)&&(!query||[d.title,d.source].join(' ').toLowerCase().includes(query)));
 if(state.view==='me')rows=rows.filter(d=>d.me);if(state.view==='family')rows=rows.filter(d=>d.family);if(state.view==='today')rows=rows.filter(d=>d.fit&&d.budget);
 rows.sort((a,b)=>state.sort==='price'?a.current_price-b.current_price:state.sort==='drop'?(b.drop?Math.abs(b.price_change):0)-(a.drop?Math.abs(a.price_change):0):state.sort==='new'?(Date.parse(b.first_seen_at)||0)-(Date.parse(a.first_seen_at)||0):b.score-a.score||a.current_price-b.current_price);
 const total=rows.length;if(state.view==='today')rows=rows.slice(0,8);
 $('listTitle').textContent={today:"Today's shortlist",me:'For you',family:'For the family',all:'All offers'}[state.view]+' · '+(state.category==='ski'?'Skis':'Clothing');
 $('count').textContent=state.view==='today'?`${rows.length} of ${total} matches`:`${total} offers`;
 $('list').innerHTML=rows.length?rows.map(card).join(''):'<div class="empty"><h3>No offers match these filters.</h3><p>Try All deals, clear your search, or adjust your preferences.</p><button class="secondary" id="emptyReset">Clear filters</button></div>';
 $('emptyReset')?.addEventListener('click',reset);
 $('healthTitle').textContent=`Store coverage · ${healthy} of ${health.length} freshly checked`;
 $('health').innerHTML=(data.run_status?`<p class="muted">Last run: ${escape(date(data.run_status.recorded_at))}. Ski collection: ${escape(data.run_status.ski)}. Clothing: ${escape(data.run_status.clothing)}. Brief: ${escape(data.run_status.brief||'not generated')}.</p>`:'')+health.map(s=>`<div class="health-row"><strong>${escape(s.source)}</strong><span>${s.status==='ok'?'Last checked '+escape(date(s.last_verified_at)):'Incomplete coverage'} · ${s.count} offers</span></div>`).join('');
 persist();
}
function reset(){state={category:state.category,view:'all',search:'',sort:'relevance',store:'',drops:false,budget:true,hidden:false};controls();render();}
$('categories').addEventListener('click',e=>{const b=e.target.closest('[data-category]');if(!b)return;state.category=b.dataset.category;state.store='';state.search='';if(state.category==='clothing'&&state.view==='family')state.view='today';storeOptions();render();});
$('views').addEventListener('click',e=>{const b=e.target.closest('[data-view]');if(b){state.view=b.dataset.view;render();}});
for(const k of ['search','sort','store','drops','budget','hidden'])$(k).addEventListener(k==='search'?'input':'change',()=>{state[k]=['drops','budget','hidden'].includes(k)?$(k).checked:$(k).value;render();});
$('reset').addEventListener('click',reset);
$('share').addEventListener('click',async()=>{const url=new URL(location.href);url.search='';for(const [k,v]of Object.entries(state))url.searchParams.set(k,typeof v==='boolean'?(v?'1':'0'):v);try{await navigator.clipboard.writeText(url.href);$('share').textContent='Copied';}catch{$('share').textContent='View link is in the address bar';}history.replaceState(null,'',url);});
$('list').addEventListener('click',e=>{const b=e.target.closest('[data-action]');if(!b)return;const d=data.deals.find(d=>d.id===b.dataset.id);if(!d)return;const key={watch:'watch_urls',mute:'muted_urls',own:'owned_urls'}[b.dataset.action];const list=new Set(preferences[key]||[]);list.has(d.url)?list.delete(d.url):list.add(d.url);preferences[key]=[...list];render();});
const form=$('preferencesForm');
function fill(){for(const key of ['my_ski_sizes','family_ski_sizes','clothing_sizes','watch_terms','muted_terms','owned_terms'])form.elements[key].value=(preferences[key]||[]).join(', ');form.elements.ski_budget.value=preferences.max_prices.ski;form.elements.clothing_budget.value=preferences.max_prices.clothing;form.elements.ski_intent.value=preferences.shopping_intent?.ski||'exceptional_only';form.elements.clothing_intent.value=preferences.shopping_intent?.clothing||'exceptional_only';$('preferenceError').textContent='';}
function readForm(){const p=clone(preferences),split=k=>form.elements[k].value.split(',').map(x=>x.trim()).filter(Boolean);for(const k of ['my_ski_sizes','family_ski_sizes'])p[k]=[...new Set(split(k).map(Number))].sort((a,b)=>a-b);for(const k of ['clothing_sizes','watch_terms','muted_terms','owned_terms'])p[k]=split(k).map(s=>s.toLowerCase());p.max_prices={ski:Number(form.elements.ski_budget.value),clothing:Number(form.elements.clothing_budget.value)};p.shopping_intent={ski:form.elements.ski_intent.value,clothing:form.elements.clothing_intent.value};return validate(p);}
$('openPreferences').addEventListener('click',()=>{fill();$('preferences').showModal();});$('closePreferences').addEventListener('click',()=>$('preferences').close());
form.addEventListener('submit',e=>{e.preventDefault();try{preferences=readForm();render();$('preferences').close();}catch(err){$('preferenceError').textContent=err.message;}});
$('export').addEventListener('click',()=>{try{const p=readForm(),url=URL.createObjectURL(new Blob([JSON.stringify(p,null,2)+'\n'],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='deal_preferences.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(err){$('preferenceError').textContent=err.message;}});
$('import').addEventListener('change',async e=>{try{const file=e.target.files[0];if(!file)return;if(file.size>1000000)throw Error('Preferences file is too large.');preferences=validate(JSON.parse(await file.text()));fill();render();}catch(err){$('preferenceError').textContent=err.message;}finally{e.target.value='';}});
$('restore').addEventListener('click',()=>{preferences=clone(data.preferences);fill();render();});
render();
})();
