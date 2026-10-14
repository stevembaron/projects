'use strict';
(() => {
const G = window.GEAR;
const D = G.dataset;
const F = window.GearFit;
const $ = id => document.getElementById(id);
const esc = v => String(v == null ? '' : v).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const safeURL = v => { try { const u = new URL(v, location.href); return ['https:', 'http:'].includes(u.protocol) ? u.href : '#'; } catch (e) { return '#'; } };
const usd = (n, cents) => n == null || !isFinite(n) ? '—' : new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD', maximumFractionDigits: cents || n < 100 && n % 1 ? 2 : 0}).format(n);
const hoursSince = iso => { const t = Date.parse(iso); return isFinite(t) ? Math.max(0, (Date.now() - t) / 36e5) : Infinity; };
const ago = iso => { const h = hoursSince(iso); if (!isFinite(h)) return 'not verified'; if (h < 1) return `${Math.max(1, Math.round(h * 60))} min ago`; if (h < 36) return `${Math.round(h)} h ago`; return `${Math.round(h / 24)} days ago`; };
const when = iso => { const d = new Date(iso); return isFinite(d) ? new Intl.DateTimeFormat('en-US', {weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZone: 'America/Denver'}).format(d) : ''; };
const clone = x => JSON.parse(JSON.stringify(x));
const thumb = v => { const url = safeURL(v); try { const u = new URL(url); if (u.hostname === 'cdn.shopify.com' || u.pathname.includes('/cdn/shop/')) u.searchParams.set('width', '360'); return u.href; } catch (e) { return url; } };
const VERDICT = {buy_now: 'Buy now', strong: 'Strong deal', watch: 'Worth watching', pass: 'Pass'};
const RANK = {buy_now: 0, strong: 1, watch: 2, pass: 3};
const CATEGORY = {carving: 'Carver', frontside: 'Frontside', all_mountain: 'All-mountain', all_mountain_wide: 'Wide all-mountain', freeride: 'Freeride', powder: 'Powder', park: 'Park', touring: 'Touring'};
const CONDITION_GROUP = {new: 'New', blem: 'Blem', new_with_tags: 'Resale new', demo: 'Demo', excellent: 'Used', good: 'Used', fair: 'Used', used: 'Used'};

const store = {
  get(key, fallback) { try { const v = localStorage.getItem('ph.' + key); return v ? JSON.parse(v) : fallback; } catch (e) { return fallback; } },
  set(key, value) { try { localStorage.setItem('ph.' + key, JSON.stringify(value)); } catch (e) { /* private mode */ } },
};

const published = clone(D.preferences);
let prefs = store.get('prefs', null);
if (!prefs || prefs.schema_version !== 3 || !Array.isArray(prefs.profiles)) prefs = clone(published);
let mine = Object.assign({saved: [], dismissed: [], owned: [], targets: {}, savedPrice: {}}, store.get('mine', {}));
let compare = [];
const defaults = {category: 'ski', profile: 'me', view: 'foryou', search: '', sort: 'verdict', kinds: ['ski'], conditions: [], categories: [], stores: [], inSize: true, budget: true};
let state = Object.assign({}, defaults, store.get('view', {}));
state.category = 'ski';
const params = new URLSearchParams(location.search);
for (const key of ['category', 'profile', 'view', 'search', 'sort']) if (params.get(key)) state[key] = params.get(key);
if (!['ski', 'clothing'].includes(state.category)) state.category = 'ski';
if (!prefs.profiles.some(p => p.id === state.profile)) state.profile = prefs.profiles[0].id;
let limit = 40;

function globalPrefs() {
  const union = (a, b) => [...new Set([...(a || []), ...(b || [])])];
  return Object.assign({}, prefs, {
    saved: union(prefs.saved, mine.saved), dismissed: union(prefs.dismissed, mine.dismissed),
    owned_listings: union(prefs.owned_listings, mine.owned), targets: Object.assign({}, prefs.targets, mine.targets),
  });
}
function profile() { return prefs.profiles.find(p => p.id === state.profile) || prefs.profiles[0]; }

function evaluateAll() {
  const g = globalPrefs(), p = profile(), freshHours = (prefs.freshness || {}).act_now_hours || 30;
  g.learned = F.learn(D.items, g);
  for (const item of D.items) {
    item.fresh = !item.stale && hoursSince(item.verified_at) <= freshHours;
    item._fit = F.evaluate(item, p, g);
    item._v = F.verdict(item, item._fit, g.targets[item.id]);
    item._saved = g.saved.includes(item.id) || g.saved.includes(item.url);
  }
}

/* ---------- small renderers ---------- */
function pill(verdict) { return `<span class="verdict v-${verdict}">${VERDICT[verdict]}</span>`; }
function scoreRing(item) {
  const s = item.score, r = 15, c = 2 * Math.PI * r;
  return `<span class="ring band-${item.band}" title="Deal score ${s}/100 · ${item.confidence} confidence"><svg viewBox="0 0 36 36" aria-hidden="true"><circle cx="18" cy="18" r="${r}" class="track"/><circle cx="18" cy="18" r="${r}" class="fill" stroke-dasharray="${(s / 100 * c).toFixed(1)} ${c.toFixed(1)}"/></svg><b>${s}</b><i class="conf conf-${item.confidence}" aria-label="${item.confidence} confidence"></i></span>`;
}
function dots(value, label) {
  if (value == null) return '';
  return `<span class="dots" title="${label} ${value}/5" aria-label="${label} ${value} of 5">${label}<i>${'●'.repeat(value)}${'○'.repeat(5 - value)}</i></span>`;
}
function valueBar(item, price) {
  const fmv = item.fmv, list = item.list_price;
  if (!fmv && !list) return '';
  const top = Math.max(price, fmv || 0, list || 0) * 1.06;
  const pos = n => (n / top * 100).toFixed(1);
  const good = fmv && price < fmv;
  const seg = fmv ? `<span class="seg ${good ? 'good' : 'bad'}" style="left:${pos(Math.min(price, fmv))}%;width:${(Math.abs(fmv - price) / top * 100).toFixed(1)}%"></span>` : '';
  return `<div class="vbar" role="img" aria-label="Price ${usd(price)}${fmv ? ', estimated fair price ' + usd(fmv) : ''}${list ? ', list ' + usd(list) : ''}">
    <span class="track"></span>${seg}
    ${fmv ? `<span class="tick fmv" style="left:${pos(fmv)}%"><em>Fair ${usd(fmv)}</em></span>` : ''}
    ${list ? `<span class="tick list" style="left:${pos(list)}%"><em>List ${usd(list)}</em></span>` : ''}
    <span class="dot" style="left:${pos(price)}%"></span></div>`;
}
function sizeChips(item) {
  const p = profile();
  if (item.kind === 'ski') {
    const L = ((p.ski || {}).lengths) || {}, ideal = L.ideal || [0, 0], ok = L.ok || [0, 0], never = L.never_at_or_above;
    return item.variants.map(v => {
      const n = v.length_cm;
      let cls = 'out';
      if (n && n >= ok[0] && n <= ok[1] && (never == null || n < never)) cls = n >= ideal[0] && n <= ideal[1] ? 'ideal' : 'ok';
      if (v.available === false) cls += ' soldout';
      const priceNote = v.price !== item.price ? ` · ${usd(v.price)}` : '';
      return `<span class="chip size ${cls}" title="${esc(v.label)}${priceNote}">${esc(v.label.replace(' cm', ''))}${priceNote ? `<small>${esc(usd(v.price))}</small>` : ''}</span>`;
    }).join('');
  }
  const sizes = ((p.clothing || {}).sizes || []).map(s => String(s).toUpperCase());
  return item.variants.map(v => `<span class="chip size ${sizes.includes(String(v.size || '').toUpperCase()) ? 'ideal' : 'out'}">${esc(v.size || v.label)}</span>`).join('');
}
function spark(series, w, h) {
  if (!series || series.length < 2) return '';
  const vals = series.map(x => x[1]), lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
  const pts = vals.map((v, i) => `${(i / (vals.length - 1) * (w - 4) + 2).toFixed(1)},${(h - 3 - (v - lo) / span * (h - 6)).toFixed(1)}`).join(' ');
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true"><polyline points="${pts}"/></svg>`;
}
function historyChart(item) {
  const s = (item.history || {}).series || [];
  if (s.length < 2) return '<p class="muted">Price history starts when we first saw this listing' + (item.first_seen ? ` (${esc(when(item.first_seen))})` : '') + '. No changes yet.</p>';
  const w = 520, h = 120, pad = 28;
  const times = s.map(x => Date.parse(x[0])), vals = s.map(x => x[1]);
  const t0 = Math.min(...times), t1 = Math.max(Date.now(), ...times), lo = Math.min(...vals), hi = Math.max(...vals), span = hi - lo || 1;
  const X = t => pad + (t - t0) / ((t1 - t0) || 1) * (w - pad - 8), Y = v => 10 + (1 - (v - lo) / span) * (h - 34);
  let path = '';
  s.forEach((p, i) => { const x = X(times[i]), y = Y(p[1]); path += i ? ` H${x.toFixed(1)} V${y.toFixed(1)}` : `M${x.toFixed(1)},${y.toFixed(1)}`; });
  path += ` H${X(t1).toFixed(1)}`;
  return `<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Price history from ${usd(hi)} to ${usd(lo)}">
    <line x1="${pad}" x2="${w - 8}" y1="${Y(lo)}" y2="${Y(lo)}" class="grid"/><line x1="${pad}" x2="${w - 8}" y1="${Y(hi)}" y2="${Y(hi)}" class="grid"/>
    <text x="2" y="${Y(hi) + 4}">${esc(usd(hi))}</text><text x="2" y="${Y(lo) + 4}">${esc(usd(lo))}</text>
    <path d="${path}" class="line"/>${s.map((p, i) => `<circle cx="${X(times[i]).toFixed(1)}" cy="${Y(p[1]).toFixed(1)}" r="3"><title>${esc(when(p[0]))}: ${esc(usd(p[1]))}</title></circle>`).join('')}
    <text x="${pad}" y="${h - 4}">${esc(when(s[0][0]).split(',').slice(0, 2).join(','))}</text><text x="${w - 8}" y="${h - 4}" text-anchor="end">now</text></svg>`;
}

function card(item) {
  const f = item._fit, [verdict, reason] = item._v, price = f.price || item.price;
  const h = item.history || {};
  const badges = [];
  if (item.is_new) badges.push('<span class="badge new">New</span>');
  if (h.change < 0) badges.push(`<span class="badge drop">▼ ${esc(usd(-h.change))}</span>`);
  if (item.cheapest_in_group) badges.push('<span class="badge">Lowest of ' + (1 + (item.also_at || []).length) + ' stores</span>');
  if (item.stale) badges.push('<span class="badge warn">Store unreachable; last seen ' + esc(ago(item.verified_at)) + '</span>');
  const specs = [];
  if (item.year) specs.push(item.year);
  if (item.category) specs.push(CATEGORY[item.category] || item.category);
  if (item.waist_mm) specs.push(item.waist_mm + ' mm');
  const b = item.bindings || {};
  if (item.kind === 'ski') specs.push(b.included ? (b.demo ? 'Demo bindings' : 'With bindings') : b.included === false ? 'Flat' : 'Bindings ?');
  const why = (item.evidence || []).slice(0, 2);
  const fitLines = [...f.pros.slice(0, 2).map(t => `<li class="pro">${esc(t)}</li>`), ...f.hard.slice(0, 1).map(t => `<li class="con hard">${esc(t)}</li>`), ...f.cons.slice(0, 2).map(t => `<li class="con">${esc(t)}</li>`)];
  const target = globalPrefs().targets[item.id];
  return `<article class="deal v-${verdict}" id="d-${esc(item.id)}" data-id="${esc(item.id)}">
  <a class="photo" href="${esc(safeURL(item.url))}" target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">${item.image ? `<img src="${esc(thumb(item.image))}" alt="" loading="lazy" decoding="async">` : '<span>No photo</span>'}</a>
  <div class="main">
    <div class="topline">${pill(verdict)}${scoreRing(item)}<span class="seller">${esc(item.source)}${item.seller_type && item.seller_type !== 'retailer' ? ` · ${esc(item.seller_type.replace('_', ' '))}` : ''}</span>${badges.join('')}</div>
    <h3><a href="${esc(safeURL(item.url))}" target="_blank" rel="noopener">${esc(item.title)}</a></h3>
    <p class="specs">${specs.map(esc).join(' · ')}${item.kind === 'ski' ? dots(item.playful, 'Playful') + dots(item.demanding, 'Demanding') : ''}<span class="cond cond-${esc(item.condition || 'unknown')}">${esc(item.condition_text)}</span></p>
    <div class="sizes">${sizeChips(item)}</div>
    <div class="why">
      ${why.length ? `<p class="interest"><b>Why it's interesting</b> ${esc(why.join('. '))}.</p>` : ''}
      <p class="reason"><b>${esc(VERDICT[verdict])}:</b> ${esc(reason)}</p>
      ${fitLines.length ? `<ul class="fit">${fitLines.join('')}</ul>` : ''}
    </div>
    <details class="more-info"><summary>Details, history and evidence</summary>
      <div class="detail-grid">
        <div>${historyChart(item)}
          <p class="muted">${h.observations ? `${h.observations} checks` : 'First check'}${h.low_90 ? ` · 90-day low ${esc(usd(h.low_90))}` : ''}${item.first_seen ? ` · first seen ${esc(when(item.first_seen))}` : ''}${item.listed_at ? ` · listed ${esc(when(item.listed_at))}` : ''}</p></div>
        <div>
          ${item.fmv_basis ? `<p><b>Fair price basis.</b> ${esc(item.fmv_basis)}.</p>` : '<p><b>Fair price.</b> Not enough evidence to estimate one.</p>'}
          ${(item.evidence || []).length > 2 ? `<ul class="evidence">${item.evidence.slice(2).map(e => `<li>${esc(e)}</li>`).join('')}</ul>` : ''}
          ${(item.flags || []).length ? `<ul class="flags">${item.flags.map(e => `<li>${esc(e)}</li>`).join('')}</ul>` : ''}
          ${item.summary ? `<p><b>How it skis.</b> ${esc(item.summary)}</p>` : item.kind === 'ski' && item.character_source === 'inferred' ? '<p class="muted">Character inferred from width and construction; this model is not in the ski catalog yet.</p>' : ''}
          ${(item.also_at || []).length ? `<p><b>Same product elsewhere.</b> ${item.also_at.map(o => `<a href="${esc(safeURL(o.url))}" target="_blank" rel="noopener">${esc(o.source)} ${esc(usd(o.price))}</a>`).join(' · ')}</p>` : ''}
          <p class="muted">Score parts: ${Object.entries(item.points || {}).map(([k, v]) => `${esc(k)} ${v}`).join(' · ')}${item.penalty ? ` · penalty −${item.penalty}` : ''}</p>
        </div>
      </div>
    </details>
  </div>
  <div class="buy">
    <p class="price">${item.price_scope !== 'exact' ? '<small>from</small>' : ''}${esc(usd(price))}</p>
    ${f.variant ? `<p class="for-size">${esc(f.variant)}</p>` : ''}
    ${item.fmv ? `<p class="fmv ${item.vs_fmv > 0 ? 'good' : ''}">${item.vs_fmv > 0 ? `${esc(usd(item.vs_fmv))} under fair` : 'At or above fair'}</p>` : ''}
    ${item.claimed_pct ? `<p class="claimed">${esc(Math.round(item.claimed_pct))}% off ${esc(usd(item.list_price))} list</p>` : ''}
    ${valueBar(item, price)}
    ${item.shipping && item.shipping.cost ? `<p class="muted">+ ${esc(usd(item.shipping.cost))} shipping</p>` : ''}
    <a class="cta" href="${esc(safeURL(item.url))}" target="_blank" rel="noopener">View at ${esc(item.source)} ↗</a>
    <p class="checked" title="${esc(when(item.verified_at))}">Checked ${esc(ago(item.verified_at))}</p>
    <div class="acts">
      <button type="button" data-act="save" aria-pressed="${item._saved}" title="Save">${item._saved ? '★ Saved' : '☆ Save'}</button>
      <button type="button" data-act="target" title="Set a target price">${target ? 'Target ' + esc(usd(target)) : 'Target'}</button>
      <button type="button" data-act="compare" aria-pressed="${compare.includes(item.id)}">Compare</button>
      <button type="button" data-act="dismiss">${f.hidden === 'dismissed' ? 'Undo' : 'Not for me'}</button>
      <button type="button" data-act="own">${f.hidden === 'owned' ? 'Undo owned' : 'I own it'}</button>
    </div>
  </div>
</article>`;
}

/* ---------- brief ---------- */
function renderBrief() {
  const el = $('brief');
  const kind = state.category;
  const key = kind === 'clothing' ? 'clothing' : (state.profile === 'family' && G.briefs.house.family ? 'family' : 'ski');
  const b = G.briefs.house[key];
  if (!b) { el.innerHTML = ''; return; }
  const line = l => {
    if (typeof l === 'string') return `<li>${esc(l)}</li>`;
    if (!l.ref) return `<li>${esc(l.text)}</li>`;
    const item = D.items.find(i => i.id === l.ref);
    const v = item && item._v ? item._v[0] : 'pass';
    return `<li class="bl v-${v}"><a href="#d-${esc(l.ref)}" data-ref="${esc(l.ref)}">${esc(l.text)}</a></li>`;
  };
  const section = s => `<div class="b-sec"><h3>${esc(s.title)}</h3><ul>${(s.lines || []).map(line).join('')}</ul></div>`;
  const all = b.sections || [], rest = all.slice(2);
  const sections = all.slice(0, 2).map(section).join('') + (rest.length ? `</div><details class="b-more"><summary>More in the brief: ${rest.map(s => esc(s.title)).join(' · ')}</summary><div class="b-body">${rest.map(section).join('')}</div></details><div>` : '');
  el.innerHTML = `<div class="b-head"><p class="kicker">The brief · ${esc(when(G.briefs.generated_at))}</p></div><h2 id="briefHeadline">${esc(b.headline)}</h2>${b.dek ? `<p class="dek">${esc(b.dek)}</p>` : ''}<div class="b-body">${sections}</div><p class="b-note">Written automatically from today's listings.</p>`;
}

/* ---------- list ---------- */
function filtered() {
  const q = state.search.trim().toLowerCase();
  const kinds = state.category === 'clothing' ? ['clothing'] : (state.kinds.length ? state.kinds : ['ski']);
  let rows = D.items.filter(i => kinds.includes(i.kind));
  const hidden = i => !!i._fit.hidden;
  if (state.view === 'hidden') rows = rows.filter(hidden);
  else rows = rows.filter(i => !hidden(i));
  if (state.view === 'foryou') rows = rows.filter(i => i._v[0] !== 'pass');
  if (state.view === 'saved') rows = rows.filter(i => i._saved);
  if (state.view === 'new') rows = rows.filter(i => i.is_new);
  if (state.view === 'drops') rows = rows.filter(i => (i.history || {}).change < 0);
  if (state.view !== 'foryou' && state.view !== 'saved') {
    if (state.inSize) rows = rows.filter(i => !i._fit.hard.some(h => /^No length|^Not in your size|^Women's-specific|^Not cut/.test(h)));
    if (state.budget) rows = rows.filter(i => !i._fit.hard.some(h => /budget/.test(h)));
  }
  if (state.conditions.length) rows = rows.filter(i => state.conditions.includes(CONDITION_GROUP[i.condition] || 'Unknown'));
  if (state.categories.length && state.category === 'ski') rows = rows.filter(i => state.categories.includes(i.category || 'unknown'));
  if (state.stores.length) rows = rows.filter(i => state.stores.includes(i.source));
  if (q) rows = rows.filter(i => `${i.title} ${i.source} ${i.brand || ''} ${i.category || ''}`.toLowerCase().includes(q));
  const by = {
    verdict: (a, b) => RANK[a._v[0]] - RANK[b._v[0]] || b.score - a.score || b._fit.score - a._fit.score,
    score: (a, b) => b.score - a.score,
    value: (a, b) => (b.vs_fmv_pct == null ? -999 : b.vs_fmv_pct) - (a.vs_fmv_pct == null ? -999 : a.vs_fmv_pct),
    price: (a, b) => (a._fit.price || a.price) - (b._fit.price || b.price),
    drop: (a, b) => ((a.history || {}).change_pct || 0) - ((b.history || {}).change_pct || 0),
    new: (a, b) => Date.parse(b.first_seen || 0) - Date.parse(a.first_seen || 0),
  };
  return rows.sort(by[state.sort] || by.verdict);
}

function renderViews() {
  const views = [['foryou', 'For you'], ['all', 'All deals'], ['new', 'New'], ['drops', 'Price drops'], ['saved', 'Saved'], ['hidden', 'Hidden']];
  $('views').innerHTML = views.map(([k, t]) => `<button type="button" role="tab" data-view="${k}" aria-selected="${state.view === k}">${t}</button>`).join('');
}

function renderFilters() {
  const items = D.items.filter(i => state.category === 'clothing' ? i.kind === 'clothing' : i.kind !== 'clothing');
  const chip = (group, value, label) => `<button type="button" class="fchip" data-group="${group}" data-value="${esc(value)}" aria-pressed="${state[group].includes(value)}">${esc(label)}</button>`;
  const conds = [...new Set(items.map(i => CONDITION_GROUP[i.condition] || 'Unknown'))];
  const cats = [...new Set(items.filter(i => i.kind === 'ski').map(i => i.category || 'unknown'))].sort();
  const stores = [...new Set(items.map(i => i.source))].sort();
  const saved = store.get('savedViews', []);
  $('filters').innerHTML = `
    ${state.category === 'ski' ? `<div class="fgroup"><span>Gear</span>${chip('kinds', 'ski', 'Skis')}${chip('kinds', 'binding', 'Bindings')}</div>` : ''}
    <div class="fgroup"><span>Condition</span>${conds.map(c => chip('conditions', c, c)).join('')}</div>
    ${state.category === 'ski' ? `<div class="fgroup"><span>Ski type</span>${cats.map(c => chip('categories', c, CATEGORY[c] || 'Unknown')).join('')}</div>` : ''}
    <div class="fgroup"><span>Store</span>${stores.map(s => chip('stores', s, s)).join('')}</div>
    <div class="fgroup toggles"><label><input type="checkbox" id="fInSize" ${state.inSize ? 'checked' : ''}> In my size</label><label><input type="checkbox" id="fBudget" ${state.budget ? 'checked' : ''}> Within budget</label>
      <span class="muted">(For you and Saved always apply your sizes and budget.)</span></div>
    <div class="fgroup saved-views"><span>Saved views</span>${saved.map((v, i) => `<button type="button" class="fchip" data-saved-view="${i}">${esc(v.name)}</button><button type="button" class="x" data-delete-view="${i}" aria-label="Delete saved view ${esc(v.name)}">×</button>`).join('')}
      <button type="button" class="ghost small" id="saveView">Save this view</button><button type="button" class="ghost small" id="resetView">Reset</button><button type="button" class="ghost small" id="shareView">Copy link</button></div>`;
}

function renderScoreboard(rows) {
  const items = D.items.filter(i => state.category === 'clothing' ? i.kind === 'clothing' : i.kind === 'ski');
  const visible = items.filter(i => !i._fit.hidden);
  const count = v => visible.filter(i => i._v[0] === v).length;
  const health = D.sources;
  const ok = health.filter(s => s.status === 'ok').length;
  const cells = [
    ['buy_now', count('buy_now'), 'Buy now'], ['strong', count('strong'), 'Strong deals'], ['watch', count('watch'), 'Worth watching'],
    ['new', visible.filter(i => i.is_new && !i._fit.hard.length).length, 'New, your size'], ['drops', visible.filter(i => (i.history || {}).change < 0 && !i._fit.hard.length).length, 'Price drops, your size'],
    ['stores', `${ok}/${health.length}`, 'Stores read fully'],
  ];
  $('scoreboard').innerHTML = cells.map(([k, n, t]) => `<button type="button" class="stat s-${k}" data-jump="${k}"><b>${n}</b><span>${t}</span></button>`).join('');
  for (const [cat, id] of [['ski', 'countSki'], ['clothing', 'countClothing']]) {
    $(id).textContent = D.items.filter(i => i.kind === cat && !i._fit.hidden && i._v[0] !== 'pass').length || '';
  }
}

function renderList() {
  const rows = filtered();
  const titles = {foryou: 'For you', all: 'All deals', new: 'New listings', drops: 'Price drops', saved: 'Saved', hidden: 'Hidden'};
  $('listTitle').textContent = `${titles[state.view] || 'Deals'} · ${state.category === 'ski' ? (state.kinds.includes('binding') && !state.kinds.includes('ski') ? 'Bindings' : 'Skis') : 'Clothing'}`;
  $('listCount').textContent = `${rows.length} listing${rows.length === 1 ? '' : 's'}`;
  const shown = rows.slice(0, limit);
  if (!rows.length) {
    const hint = state.view === 'foryou' ? "Nothing clears your size, style and budget right now. Try All deals, or widen your length range in Preferences." : 'No listings match these filters.';
    $('list').innerHTML = `<div class="empty"><p>${hint}</p><button type="button" class="ghost" id="emptyAll">Show all deals</button></div>`;
  } else {
    $('list').innerHTML = shown.map(card).join('');
  }
  $('more').hidden = rows.length <= limit;
  $('more').textContent = `Show ${Math.min(40, rows.length - limit)} more of ${rows.length - limit}`;
  renderScoreboard(rows);
  renderCompareBar();
}

function renderGone() {
  const kind = state.category === 'clothing' ? 'clothing' : 'ski';
  const g = globalPrefs();
  const rows = (D.gone || []).filter(r => r.kind === kind).map(r => Object.assign({}, r, {saved: g.saved.includes(r.id) || g.saved.includes(r.url)}));
  rows.sort((a, b) => (b.saved - a.saved));
  if (!rows.length) { $('gone').innerHTML = ''; return; }
  $('gone').innerHTML = `<h2 id="goneTitle">Recently sold or removed</h2><p class="muted">Seen in a complete check of the store, then gone in a later one. ${rows.length} in the last week.</p>
    <ul class="gone-list">${rows.slice(0, 12).map(r => `<li class="${r.saved ? 'saved' : ''}">${r.saved ? '★ ' : ''}${esc(r.title)} <span class="muted">· ${esc(r.source)} · gone ${esc(ago(r.gone_at))}</span></li>`).join('')}</ul>`;
}

function renderHealth() {
  const s = D.sources;
  const bad = s.filter(x => x.status !== 'ok');
  $('healthTitle').textContent = `Store coverage · ${s.length - bad.length} of ${s.length} read fully${bad.length ? ` · ${bad.length} need attention` : ''}`;
  $('healthBody').innerHTML = `<table class="htable"><thead><tr><th>Store</th><th>Status</th><th>Listings</th><th>Pages</th><th>Last full read</th><th>Recent success</th><th>Notes</th></tr></thead><tbody>
    ${s.map(x => `<tr class="h-${esc(x.status)}"><td>${esc(x.name)}</td><td><span class="hstat">${esc(x.status)}</span></td><td>${x.offers}</td><td>${x.pages}</td><td>${x.last_ok ? esc(ago(x.last_ok)) : '—'}</td><td>${x.success_rate == null ? '—' : Math.round(x.success_rate * 100) + '% of ' + x.runs}</td><td>${esc(x.error || (x.notes || []).join('; ') || '')}</td></tr>`).join('')}
  </tbody></table><p class="muted">Data built ${esc(when(D.generated_at))}. ${D.counts.collected.toLocaleString()} listings collected; ${D.counts.published.toLocaleString()} discounted or secondhand listings published.</p>`;
}

function renderAlerts() {
  const seen = new Set(store.get('seen', []));
  const first = !store.get('visited', false);
  const g = globalPrefs();
  const out = [];
  for (const i of D.items) {
    if (i._fit.hidden) continue;
    const v = i._v[0];
    const price = i._fit.price || i.price;
    const target = g.targets[i.id];
    if (target && price <= target) out.push({id: i.id, text: `Target hit: ${i.title} is ${usd(price)} (target ${usd(target)})`, cls: 'v-buy_now'});
    else if ((v === 'buy_now' || v === 'strong') && !seen.has(i.id)) out.push({id: i.id, text: `${VERDICT[v]}: ${i.title}, ${usd(price)} at ${i.source}`, cls: 'v-' + v});
    else if (i._saved && mine.savedPrice[i.id] && price < mine.savedPrice[i.id]) out.push({id: i.id, text: `Saved item cheaper: ${i.title} now ${usd(price)} (was ${usd(mine.savedPrice[i.id])} when saved)`, cls: 'v-strong'});
  }
  for (const r of D.gone || []) if (g.saved.includes(r.id) || g.saved.includes(r.url)) out.push({id: null, text: `Saved item gone: ${r.title} (${r.source})`, cls: 'v-pass'});
  if (first || !out.length) { $('alerts').hidden = true; if (first) markSeen(); return; }
  $('alerts').hidden = false;
  $('alerts').innerHTML = `<div class="alerts-head"><b>Since your last visit</b><button type="button" class="ghost small" id="markSeen">Mark all seen</button></div><ul>${out.slice(0, 6).map(a => `<li class="${a.cls}">${a.id ? `<a href="#d-${esc(a.id)}" data-ref="${esc(a.id)}">${esc(a.text)}</a>` : esc(a.text)}</li>`).join('')}</ul>${out.length > 6 ? `<p class="muted">and ${out.length - 6} more</p>` : ''}`;
}
function markSeen() {
  store.set('seen', D.items.filter(i => i._v[0] === 'buy_now' || i._v[0] === 'strong').map(i => i.id));
  store.set('visited', true);
}

function renderCompareBar() {
  const bar = $('compareBar');
  if (!compare.length) { bar.hidden = true; return; }
  bar.hidden = false;
  bar.innerHTML = `<span>${compare.length} selected</span><button type="button" id="openCompare" ${compare.length < 2 ? 'disabled' : ''}>Compare</button><button type="button" class="ghost small" id="clearCompare">Clear</button>`;
}

function render() {
  evaluateAll();
  for (const b of document.querySelectorAll('[data-category]')) b.setAttribute('aria-pressed', String(b.dataset.category === state.category));
  const p = $('profile');
  p.innerHTML = prefs.profiles.map(x => `<option value="${esc(x.id)}" ${x.id === state.profile ? 'selected' : ''}>${esc(x.name)}</option>`).join('');
  const age = hoursSince(D.generated_at);
  $('freshness').innerHTML = `Checked ${esc(when(D.generated_at))}${age > ((prefs.freshness || {}).act_now_hours || 30) ? ' · <b class="stale">older than your freshness window; Buy now is paused</b>' : ''}`;
  $('search').value = state.search;
  $('sort').value = state.sort;
  renderBrief();
  renderViews();
  renderFilters();
  renderList();
  renderGone();
  renderHealth();
  renderAlerts();
  store.set('view', Object.assign({}, state, {search: ''}));
}

/* ---------- preferences dialog ---------- */
function prefsForm() {
  const p = profile(), s = p.ski, c = p.clothing;
  const list = v => (v || []).join(', ');
  const cats = Object.keys(CATEGORY);
  const conds = ['new', 'blem', 'new_with_tags', 'demo', 'excellent', 'good', 'fair', 'used'];
  $('prefsDialog').innerHTML = `<form method="dialog" id="prefsForm" novalidate>
  <div class="sheet-head"><h2 id="prefsTitle">Preferences · ${esc(p.name)}</h2><button type="button" class="x" data-close aria-label="Close">×</button></div>
  <p class="muted">Changes apply in this browser right away. To make the twice-daily build use them, export and replace <code>config/deal_preferences.json</code> (<a href="${esc(G.repo)}/edit/main/config/deal_preferences.json" target="_blank" rel="noopener">edit on GitHub</a>).</p>
  ${s ? `<fieldset><legend>Skis</legend><div class="grid">
    <label>Ideal length from (cm)<input name="ideal0" type="number" min="100" max="210" value="${s.lengths.ideal[0]}"></label>
    <label>to<input name="ideal1" type="number" min="100" max="210" value="${s.lengths.ideal[1]}"></label>
    <label>Acceptable from<input name="ok0" type="number" min="100" max="210" value="${s.lengths.ok[0]}"></label>
    <label>to<input name="ok1" type="number" min="100" max="210" value="${s.lengths.ok[1]}"></label>
    <label>Never at or above<input name="never" type="number" min="100" max="220" value="${s.lengths.never_at_or_above || ''}"></label>
    <label>Budget ($)<input name="budget" type="number" min="1" max="20000" value="${s.budget}"></label>
    <label>Style<select name="style"><option value="playful" ${s.style === 'playful' ? 'selected' : ''}>Playful; I slarve more than carve</option><option value="" ${!s.style ? 'selected' : ''}>No preference</option></select></label>
    <label>Ability<select name="ability">${['', 'intermediate', 'advanced', 'expert'].map(a => `<option value="${a}" ${s.ability === a || (!s.ability && !a) ? 'selected' : ''}>${a || 'Not set'}</option>`).join('')}</select></label>
    <label class="check"><input type="checkbox" name="resort" ${s.resort_only ? 'checked' : ''}> Resort skiing (downrank touring skis)</label>
  </div>
  <div class="checks"><span>Avoid</span>${cats.map(k => `<label><input type="checkbox" name="avoid" value="${k}" ${(s.categories_avoid || []).includes(k) ? 'checked' : ''}> ${CATEGORY[k]}</label>`).join('')}</div>
  <div class="checks"><span>Already own a</span>${cats.map(k => `<label><input type="checkbox" name="owned" value="${k}" ${(s.categories_owned || []).includes(k) ? 'checked' : ''}> ${CATEGORY[k]}</label>`).join('')}</div>
  <div class="checks"><span>Conditions</span>${conds.map(k => `<label><input type="checkbox" name="cond" value="${k}" ${(s.conditions || []).includes(k) ? 'checked' : ''}> ${k.replace(/_/g, ' ')}</label>`).join('')}</div>
  <div class="checks"><span>Cut</span>${['mens', 'womens', 'unisex'].map(k => `<label><input type="checkbox" name="gender" value="${k}" ${(s.genders || []).includes(k) ? 'checked' : ''}> ${k === 'mens' ? "Men's" : k === 'womens' ? "Women's" : 'Unisex'}</label>`).join('')}</div>
  <label class="wide">Skis you own (one per line: Brand Model, waist mm, type)<textarea name="quiver" rows="3">${esc((s.quiver || []).map(q => `${q.name}, ${q.waist_mm || ''}, ${q.category || ''}`).join('\n'))}</textarea></label>
  </fieldset>` : ''}
  ${c ? `<fieldset><legend>Clothing</legend><div class="grid"><label>Sizes<input name="csizes" value="${esc(list(c.sizes))}"></label><label>Budget ($)<input name="cbudget" type="number" min="1" max="5000" value="${c.budget}"></label></div></fieldset>` : ''}
  <fieldset><legend>Everyone</legend><div class="grid"><label class="wide">Watch terms<input name="watch" value="${esc(list(prefs.watch_terms))}"></label><label class="wide">Muted terms<input name="muted" value="${esc(list(prefs.muted_terms))}"></label></div></fieldset>
  <p class="error" id="prefsError" role="alert"></p>
  <div class="sheet-actions"><button type="submit" id="prefsSave">Save in this browser</button><button type="button" class="ghost" id="prefsExport">Export JSON</button>
  <label class="ghost file">Import JSON<input type="file" id="prefsImport" accept="application/json,.json"></label><button type="button" class="ghost" id="prefsReset">Use published settings</button></div>
  </form>`;
}
function readPrefsForm() {
  const form = $('prefsForm'), next = clone(prefs), p = next.profiles.find(x => x.id === state.profile);
  const num = name => { const v = form.elements[name] && form.elements[name].value; return v === '' || v == null ? null : Number(v); };
  const checked = name => [...form.querySelectorAll(`input[name="${name}"]:checked`)].map(x => x.value);
  const words = v => String(v || '').split(',').map(x => x.trim()).filter(Boolean);
  if (p.ski) {
    const ideal = [num('ideal0'), num('ideal1')], ok = [num('ok0'), num('ok1')];
    if (ideal.concat(ok).some(n => !Number.isFinite(n))) throw Error('Enter all four lengths.');
    if (!(ok[0] <= ideal[0] && ideal[0] <= ideal[1] && ideal[1] <= ok[1])) throw Error('The ideal range must sit inside the acceptable range.');
    const budget = num('budget');
    if (!(budget > 0)) throw Error('Enter a ski budget above zero.');
    p.ski.lengths = {ideal, ok, never_at_or_above: num('never')};
    p.ski.budget = budget;
    p.ski.style = form.elements.style.value || null;
    p.ski.ability = form.elements.ability.value || null;
    p.ski.resort_only = form.elements.resort.checked;
    p.ski.categories_avoid = checked('avoid');
    p.ski.categories_owned = checked('owned');
    p.ski.conditions = checked('cond');
    const genders = checked('gender');
    p.ski.genders = genders.length ? genders.concat([null]) : null;
    p.ski.quiver = form.elements.quiver.value.split('\n').map(l => l.trim()).filter(Boolean).map(line => {
      const [name, waist, category] = line.split(',').map(x => x.trim());
      const words2 = name.split(/\s+/);
      const known = (p.ski.quiver || []).find(q => q.name === name);
      return Object.assign({}, known || {}, {name, waist_mm: Number(waist) || null, category: category || null, brand: known ? known.brand : words2[0], model_key: known ? known.model_key : words2.slice(1).join(' ').toLowerCase()});
    });
  }
  if (p.clothing) {
    p.clothing.sizes = words(form.elements.csizes.value).map(s => s.toUpperCase());
    p.clothing.budget = num('cbudget');
    if (!(p.clothing.budget > 0)) throw Error('Enter a clothing budget above zero.');
  }
  next.watch_terms = words(form.elements.watch.value).map(s => s.toLowerCase());
  next.muted_terms = words(form.elements.muted.value).map(s => s.toLowerCase());
  return next;
}
function exportPrefs() {
  const out = clone(prefs);
  const g = globalPrefs();
  Object.assign(out, {saved: g.saved, dismissed: g.dismissed, owned_listings: g.owned_listings, targets: g.targets});
  const url = URL.createObjectURL(new Blob([JSON.stringify(out, null, 2) + '\n'], {type: 'application/json'}));
  const a = document.createElement('a'); a.href = url; a.download = 'deal_preferences.json'; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}

async function copy(text, button) {
  try { await navigator.clipboard.writeText(text); button.textContent = 'Copied'; }
  catch (e) { const t = document.createElement('textarea'); t.value = text; document.body.appendChild(t); t.select(); try { document.execCommand('copy'); button.textContent = 'Copied'; } catch (e2) { button.textContent = 'Copy failed'; } t.remove(); }
}

/* ---------- compare ---------- */
function compareDialog() {
  const items = compare.map(id => D.items.find(i => i.id === id)).filter(Boolean);
  const rows = [
    ['Verdict', i => VERDICT[i._v[0]]], ['Price', i => usd(i._fit.price || i.price)], ['Fair price', i => i.fmv ? usd(i.fmv) : '—'],
    ['Under fair', i => i.vs_fmv > 0 ? usd(i.vs_fmv) : '—'], ['Deal score', i => `${i.score} (${i.confidence})`], ['Fit score', i => i._fit.score],
    ['Your size', i => i._fit.variant || '—'], ['Type', i => CATEGORY[i.category] || '—'], ['Waist', i => i.waist_mm ? i.waist_mm + ' mm' : '—'],
    ['Playful', i => i.playful == null ? '—' : i.playful + '/5'], ['Demanding', i => i.demanding == null ? '—' : i.demanding + '/5'],
    ['Condition', i => i.condition_text], ['Year', i => i.year || '—'], ['Bindings', i => (i.bindings || {}).included ? ((i.bindings || {}).demo ? 'Demo' : 'Included') : (i.bindings || {}).included === false ? 'None' : '?'],
    ['Store', i => i.source], ['Checked', i => ago(i.verified_at)],
  ];
  $('compareDialog').innerHTML = `<div class="sheet-head"><h2 id="compareTitle">Compare</h2><button type="button" class="x" data-close aria-label="Close">×</button></div>
  <div class="ctable-wrap"><table class="ctable"><thead><tr><th></th>${items.map(i => `<th><a href="${esc(safeURL(i.url))}" target="_blank" rel="noopener">${esc(i.title)}</a></th>`).join('')}</tr></thead>
  <tbody>${rows.map(([label, fn]) => `<tr><th>${label}</th>${items.map(i => `<td>${esc(fn(i))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
  $('compareDialog').showModal();
}

/* ---------- events ---------- */
function saveMine() { store.set('mine', mine); }
function toggle(list, value) { const i = list.indexOf(value); if (i >= 0) list.splice(i, 1); else list.push(value); }

document.addEventListener('click', e => {
  const t = e.target.closest('button, a');
  if (!t) return;
  if (t.dataset.category) { state.category = t.dataset.category; state.stores = []; state.categories = []; limit = 40; render(); return; }
  if (t.dataset.view) { state.view = t.dataset.view; limit = 40; render(); return; }
  if (t.dataset.group) { toggle(state[t.dataset.group], t.dataset.value); if (t.dataset.group === 'kinds' && !state.kinds.length) state.kinds = ['ski']; limit = 40; render(); $('filters').hidden = false; return; }
  if (t.dataset.jump) {
    const map = {buy_now: 'foryou', strong: 'foryou', watch: 'foryou', new: 'new', drops: 'drops'};
    if (t.dataset.jump === 'stores') { $('health').open = true; $('health').scrollIntoView({behavior: 'smooth'}); return; }
    state.view = map[t.dataset.jump]; render(); $('deals').scrollIntoView({behavior: 'smooth'}); return;
  }
  if (t.dataset.ref) {
    const el = $('d-' + t.dataset.ref);
    if (!el) { e.preventDefault(); state.view = 'all'; state.inSize = false; state.budget = false; state.search = ''; render(); }
    setTimeout(() => { const x = $('d-' + t.dataset.ref); if (x) { x.scrollIntoView({behavior: 'smooth', block: 'center'}); x.classList.add('flash'); setTimeout(() => x.classList.remove('flash'), 1600); } }, 30);
    return;
  }
  if (t.dataset.close !== undefined) { t.closest('dialog').close(); return; }
  if (t.dataset.savedView) { const v = store.get('savedViews', [])[Number(t.dataset.savedView)]; if (v) { state = Object.assign({}, defaults, v.state); render(); } return; }
  if (t.dataset.deleteView) { const v = store.get('savedViews', []); v.splice(Number(t.dataset.deleteView), 1); store.set('savedViews', v); renderFilters(); return; }
  const act = t.dataset.act;
  if (act) {
    const id = t.closest('[data-id]').dataset.id, item = D.items.find(i => i.id === id);
    if (act === 'save') { toggle(mine.saved, id); if (mine.saved.includes(id)) mine.savedPrice[id] = item._fit.price || item.price; saveMine(); }
    if (act === 'dismiss') { toggle(mine.dismissed, id); saveMine(); }
    if (act === 'own') { toggle(mine.owned, id); saveMine(); }
    if (act === 'compare') { toggle(compare, id); if (compare.length > 3) compare.shift(); }
    if (act === 'target') {
      const current = globalPrefs().targets[id];
      const answer = window.prompt(`Alert me when ${item.title} is at or below (USD). Leave empty to clear.`, current || Math.round((item._fit.price || item.price) * 0.85));
      if (answer === null) return;
      const n = Number(String(answer).replace(/[$,]/g, ''));
      if (answer.trim() === '') delete mine.targets[id]; else if (n > 0) mine.targets[id] = n; else return;
      saveMine();
    }
    const y = window.scrollY; render(); window.scrollTo(0, y);
    return;
  }
  switch (t.id) {
    case 'toggleFilters': { const f = $('filters'); f.hidden = !f.hidden; t.setAttribute('aria-expanded', String(!f.hidden)); break; }
    case 'more': limit += 40; renderList(); break;
    case 'emptyAll': state.view = 'all'; state.inSize = false; state.budget = false; state.conditions = []; state.categories = []; state.stores = []; state.search = ''; render(); break;
    case 'openPrefs': prefsForm(); $('prefsDialog').showModal(); break;
    case 'prefsExport': try { prefs = readPrefsForm(); } catch (err) { $('prefsError').textContent = err.message; break; } store.set('prefs', prefs); exportPrefs(); break;
    case 'prefsReset': prefs = clone(published); store.set('prefs', null); $('prefsDialog').close(); render(); break;
    case 'markSeen': markSeen(); $('alerts').hidden = true; break;
    case 'openCompare': compareDialog(); break;
    case 'clearCompare': compare = []; render(); break;
    case 'saveView': { const name = window.prompt('Name this view'); if (name) { const v = store.get('savedViews', []); v.push({name: name.slice(0, 30), state: Object.assign({}, state)}); store.set('savedViews', v); renderFilters(); } break; }
    case 'resetView': state = Object.assign({}, defaults, {category: state.category, profile: state.profile}); render(); break;
    case 'shareView': { const u = new URL(location.href); u.search = ''; u.hash = ''; for (const k of ['category', 'profile', 'view', 'sort']) u.searchParams.set(k, state[k]); if (state.search) u.searchParams.set('search', state.search); copy(u.href, t); break; }
    default: break;
  }
});
document.addEventListener('submit', e => {
  if (e.target.id !== 'prefsForm') return;
  e.preventDefault();
  try { prefs = readPrefsForm(); store.set('prefs', prefs); $('prefsDialog').close(); render(); }
  catch (err) { $('prefsError').textContent = err.message; }
});
document.addEventListener('change', e => {
  const t = e.target;
  if (t.id === 'profile') { state.profile = t.value; render(); }
  if (t.id === 'sort') { state.sort = t.value; renderList(); store.set('view', state); }
  if (t.id === 'fInSize') { state.inSize = t.checked; renderList(); }
  if (t.id === 'fBudget') { state.budget = t.checked; renderList(); }
  if (t.id === 'prefsImport' && t.files[0]) {
    t.files[0].text().then(text => {
      const next = JSON.parse(text);
      if (next.schema_version !== 3 || !Array.isArray(next.profiles) || !next.profiles.length) throw Error('Expected a schema 3 preferences file.');
      prefs = next; store.set('prefs', prefs); $('prefsDialog').close(); render();
    }).catch(err => { $('prefsError').textContent = err.message; });
  }
});
let searchTimer;
$('search').addEventListener('input', e => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { state.search = e.target.value; limit = 40; renderList(); }, 120); });

render();
if (location.hash.startsWith('#d-')) setTimeout(() => { const x = document.querySelector(location.hash); if (x) x.scrollIntoView({block: 'center'}); }, 50);
window.GearApp = {state: () => state, evaluateAll};
})();
