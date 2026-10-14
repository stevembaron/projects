/* Personal fit and verdict rules. Mirrors scripts/gear/fit.py exactly so
   in-browser preference edits re-rank listings the same way the daily build
   does. tests/test_fit_parity.py runs both against shared vectors. */
(function (root) {
  'use strict';
  const NOUN = {carving: 'carver', frontside: 'frontside ski', all_mountain: 'all-mountain ski', all_mountain_wide: 'wide all-mountain ski',
    freeride: 'freeride ski', powder: 'powder ski', park: 'park ski', touring: 'touring ski'};
  const usd = n => '$' + Math.round(n).toLocaleString('en-US');
  const fmtLen = n => Number.isInteger(n) ? String(n) : String(n);
  const text = item => ['title', 'source', 'url'].map(k => String(item[k] == null ? '' : item[k])).join(' ').toLowerCase();
  const has = (list, value) => Array.isArray(list) && list.some(x => x === value || (x === null && value == null));
  const minBy = (list, key) => list.reduce((best, x) => (best === null || key(x) < key(best) ? x : best), null);
  const lowerFirst = s => s.charAt(0).toLowerCase() + s.slice(1);

  function skiFit(item, prefs, global) {
    const pros = [], cons = [], hard = [];
    let score = 50;
    const genders = prefs.genders;
    if (genders && genders.length && !has(genders, item.gender)) hard.push(item.gender === 'womens' ? "Women's-specific model" : 'Not cut for this profile');
    const lengths = prefs.lengths || {};
    const ideal = lengths.ideal || [0, 999], ok = lengths.ok || [0, 999], never = lengths.never_at_or_above;
    const variants = (item.variants || []).filter(v => v.available !== false);
    const sized = variants.filter(v => v.length_cm);
    const inOk = sized.filter(v => v.length_cm >= ok[0] && v.length_cm <= ok[1] && (never == null || v.length_cm < never));
    const inIdeal = inOk.filter(v => v.length_cm >= ideal[0] && v.length_cm <= ideal[1]);
    let chosen = null;
    if (inIdeal.length) {
      chosen = minBy(inIdeal, v => v.price);
      score += 25;
      pros.push(`${fmtLen(chosen.length_cm)} cm is in your ${ideal[0]}–${ideal[1]} cm range`);
    } else if (inOk.length) {
      const middle = (ideal[0] + ideal[1]) / 2;
      chosen = inOk.slice().sort((a, b) => Math.abs(a.length_cm - middle) - Math.abs(b.length_cm - middle) || a.price - b.price)[0];
      score += 12;
      cons.push(`${fmtLen(chosen.length_cm)} cm is a touch ${chosen.length_cm < ideal[0] ? 'short' : 'long'} of your ${ideal[0]}–${ideal[1]} cm range`);
    } else if (sized.length) {
      const available = sized.slice().sort((a, b) => a.length_cm - b.length_cm).slice(0, 6).map(v => fmtLen(v.length_cm)).join(', ');
      hard.push(`No length between ${ok[0]} and ${ok[1]} cm (has ${available})`);
    } else if (variants.length) {
      chosen = minBy(variants, v => v.price);
      cons.push('Lengths not listed; check your size before buying');
    } else {
      hard.push('Sold out');
    }
    const price = chosen ? chosen.price : item.price;
    if (prefs.budget && price && price > prefs.budget) hard.push(`Over your ${usd(prefs.budget)} budget`);
    const playful = item.playful, demanding = item.demanding;
    if (prefs.style === 'playful') {
      if (playful == null) { score -= 5; cons.push('How it skis is unknown for this model'); }
      else if (playful >= 4) { score += 15; pros.push('Playful and easy to pivot or slarve'); }
      else if (playful === 3) score += 5;
      else { score -= 22; cons.push('Prefers to be carved; less forgiving of slarved turns'); }
      if (demanding != null && demanding >= 4) { score -= 12; cons.push('Demanding: wants speed and precise technique'); }
      else if (demanding != null && demanding <= 2) { score += 4; pros.push('Forgiving'); }
    }
    const category = item.category;
    if (category && has(prefs.categories_avoid, category)) { score -= 15; cons.push(`A ${NOUN[category] || category}, which you avoid`); }
    if (category === 'touring' && prefs.resort_only) { score -= 12; cons.push('Built light for touring; less damp on resort snow'); }
    const level = item.level || [];
    if ((prefs.ability === 'advanced' || prefs.ability === 'expert') && level.length === 2 && (level[1] === 'beginner' || level[1] === 'intermediate')) {
      hard.push('Entry-level ski, below your ability');
    }
    let duplicate = null;
    for (const owned of prefs.quiver || []) {
      const sameFamily = owned.model_key && owned.brand === item.brand && String(item.model_key || '').startsWith(owned.model_key);
      const similar = owned.category === category && owned.waist_mm && item.waist_mm && Math.abs(owned.waist_mm - item.waist_mm) <= 5;
      if (sameFamily || similar) { duplicate = owned.name; score -= 20; cons.push(`Close to your ${owned.name}`); break; }
    }
    if (!duplicate && category && has(prefs.categories_owned, category)) { score -= 6; cons.push(`You already own a ${NOUN[category] || category}`); }
    if (prefs.conditions && prefs.conditions.length && item.condition && !has(prefs.conditions, item.condition)) hard.push('Condition is outside your preferences');
    const binding = item.bindings || {};
    if (prefs.bindings === 'flat' && binding.included) cons.push('Comes with bindings you may not want');
    else if (prefs.bindings === 'included' && binding.included === false) { score -= 6; cons.push('Bindings not included'); }
    if (binding.included && binding.demo) pros.push('Includes adjustable demo bindings');
    const learned = global.learned || {};
    const brandPasses = (learned.brands || {})[item.brand || ''] || 0;
    const categoryPasses = (learned.categories || {})[category || ''] || 0;
    if (brandPasses >= 2) { score -= 6; cons.push(`You've passed on ${brandPasses} ${item.brand} skis`); }
    if (categoryPasses >= 3) { score -= 6; cons.push(`You've passed on ${categoryPasses} ${NOUN[category] || category}s`); }
    const t = text(item);
    if ((global.watch_terms || []).some(term => t.includes(String(term).toLowerCase()))) { score += 8; pros.push('Matches your watch list'); }
    return {score: Math.max(0, Math.min(100, score)), hard, pros: pros.slice(0, 4), cons: cons.slice(0, 4), variant: chosen ? chosen.label : null, price, duplicate};
  }

  function clothingFit(item, prefs, global) {
    if (!prefs) return {score: 0, hard: ['No clothing preferences for this profile'], pros: [], cons: [], variant: null, price: item.price, duplicate: null};
    const pros = [], cons = [], hard = [];
    let score = 50;
    if (prefs.genders && prefs.genders.length && !has(prefs.genders, item.gender)) hard.push('Not cut for this profile');
    const sizes = (prefs.sizes || []).map(s => String(s).toUpperCase());
    const variants = (item.variants || []).filter(v => v.available !== false);
    const matching = variants.filter(v => sizes.includes(String(v.size || '').toUpperCase()));
    const chosen = matching.length ? minBy(matching, v => v.price) : null;
    if (chosen) { score += 30; pros.push(`Your size (${chosen.size})`); }
    else if (variants.length) {
      const listed = [...new Set(variants.map(v => String(v.size || v.label)))].sort().join(', ').slice(0, 40);
      hard.push(`Not in your size (listed: ${listed})`);
    } else hard.push('Sold out');
    const price = chosen ? chosen.price : item.price;
    if (prefs.budget && price && price > prefs.budget) hard.push(`Over your ${usd(prefs.budget)} budget`);
    if (item.condition === 'fair') { score -= 10; cons.push('Fair condition: visible wear'); }
    else if (item.condition === 'new' || item.condition === 'new_with_tags') { score += 8; pros.push('Unworn'); }
    if (prefs.conditions && prefs.conditions.length && item.condition && !has(prefs.conditions, item.condition)) hard.push('Condition is outside your preferences');
    const t = text(item);
    if ((global.watch_terms || []).some(term => t.includes(String(term).toLowerCase()))) { score += 10; pros.push('Matches your watch list'); }
    return {score: Math.max(0, Math.min(100, score)), hard, pros: pros.slice(0, 4), cons: cons.slice(0, 4), variant: chosen ? chosen.label : null, price, duplicate: null};
  }

  function evaluate(item, profile, global) {
    const t = text(item);
    let hidden = null;
    const listed = key => (global[key] || []).includes(item.id) || (global[key] || []).includes(item.url);
    if (listed('dismissed')) hidden = 'dismissed';
    else if (listed('owned_listings')) hidden = 'owned';
    else if ((global.muted_terms || []).some(term => t.includes(String(term).toLowerCase()))) hidden = 'muted';
    let result;
    if (item.kind === 'ski') {
      result = profile.ski ? skiFit(item, profile.ski, global)
        : {score: 0, hard: ['No ski preferences for this profile'], pros: [], cons: [], variant: null, price: item.price, duplicate: null};
    } else if (item.kind === 'clothing') {
      result = clothingFit(item, profile.clothing, global);
    } else {
      const budget = (profile.ski || {}).budget;
      result = {score: 50, hard: budget && (item.price || 0) > budget ? [`Over your ${usd(budget)} budget`] : [], pros: [], cons: [], variant: null, price: item.price, duplicate: null};
    }
    result.hidden = hidden;
    return result;
  }

  function verdict(item, fit, target) {
    if (fit.hidden) return ['pass', {dismissed: 'You dismissed this', owned: 'You own this', muted: 'Matches a muted term'}[fit.hidden]];
    if (fit.hard.length) return ['pass', fit.hard[0]];
    const score = item.score || 0, fitness = fit.score;
    const price = fit.price || item.price || 0;
    const verified = item.price_scope === 'exact' && !!item.in_stock && !!item.fresh;
    const duplicate = !!fit.duplicate;
    if (target && price && price <= target) return [verified ? 'buy_now' : 'strong', `At or under your ${usd(target)} target`];
    if (score >= 78 && fitness >= 70 && item.confidence !== 'low' && verified && (!duplicate || score >= 88)) return ['buy_now', 'Exceptional, verified price on a ski that suits you'];
    if (score >= 64 && fitness >= 60 && (!duplicate || score >= 78)) return ['strong', 'Well under fair value and a good fit'];
    if ((score >= 48 && fitness >= 45) || (fitness >= 70 && score >= 35)) return ['watch', score < 64 ? 'Good fit; price could still improve' : 'Strong price, but overlaps what you own'];
    if (score < 48) return ['pass', 'Price is not compelling'];
    return ['pass', 'Weak match for how you ski'];
  }

  function learn(items, global) {
    const dismissed = new Set(global.dismissed || []);
    const brands = {}, categories = {};
    for (const item of items) {
      if (item.kind !== 'ski' || (!dismissed.has(item.id) && !dismissed.has(item.url))) continue;
      if (item.brand) brands[item.brand] = (brands[item.brand] || 0) + 1;
      if (item.category) categories[item.category] = (categories[item.category] || 0) + 1;
    }
    return {brands, categories};
  }

  const api = {evaluate, verdict, skiFit, clothingFit, learn, lowerFirst};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.GearFit = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
