"""Shared, conservative eligibility and ranking for the dashboard and analyst."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse


def timestamp(value):
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).replace(tzinfo=timezone.utc) if len(str(value)) == 10 else datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def age_hours(value, now=None):
    date = timestamp(value)
    return max(0, ((now or datetime.now(timezone.utc)) - date).total_seconds() / 3600) if date else None


def canonical_url(url):
    p = urlparse(str(url))
    return urlunparse(p._replace(query='', fragment='')).rstrip('/')


def offer_key(deal):
    get = deal.get if isinstance(deal, dict) else lambda k, default=None: getattr(deal, k, default)
    sizes = ','.join(sorted(str(s).lower() for s in (get('sizes') or [])))
    variant = get('variant_id') or sizes or get('title', '').lower()
    return f"v2|{get('source')}|{canonical_url(get('url'))}|{variant}".lower()


def listing_id(deal):
    return hashlib.sha256(offer_key(deal).encode()).hexdigest()[:16]


def normalized_product(deal):
    # Keep width, year, gender, bindings, construction and condition differences.
    title = str(deal.get('title', '')).lower()
    title = re.sub(r'\b(\d{2,3})\s*cm\b', ' ', title)
    title = re.sub(r'\s+-\s+(?:new\s*/\s*)?\d{3}\s*$', '', title)
    title = re.sub(r"\bwomen['’]?s\b", 'womens', title)
    title = re.sub(r'\bskis?\b', ' ', title)
    return ' '.join(sorted(re.findall(r'[a-z0-9]+', title)))


def comparison_key(deal):
    sizes = tuple(sorted(str(s).lower() for s in deal.get('sizes') or []))
    title = str(deal.get('title', ''))
    if not sizes or deal.get('price_scope') != 'exact' or deal.get('is_cached') or deal.get('stock_status') != 'in_stock':
        return None
    # Unknown model year or condition does not prove an equivalent offer.
    year = deal.get('model_year') or next(iter(re.findall(r'\b20\d{2}\b', title)), None)
    condition = deal.get('condition')
    if not year or not condition:
        return None
    return (deal.get('category', 'ski'), normalized_product(deal), str(year), condition, sizes)


def comparisons(deals):
    groups = {}
    for d in deals:
        key = comparison_key(d)
        if key:
            groups.setdefault(key, []).append(d)
    result = {}
    for group in groups.values():
        if len({d['source'] for d in group}) < 2:
            continue
        cheapest = min(group, key=lambda d: float(d['current_price']))
        for d in group:
            result[id(d)] = {'best': d is cheapest, 'stores': len({x['source'] for x in group}),
                'note': f"Also at {cheapest['source']} for ${cheapest['current_price']:.2f}",
                'offers': [{'id': listing_id(x), 'source': x['source'], 'price': x['current_price'], 'url': x['url']} for x in group]}
    return result


def size_match(category, sizes, preferred, clothing):
    if category == 'clothing':
        aliases = {'small': 's', 'medium': 'm', 'large': 'l', 'x-large': 'xl'}
        return any(aliases.get(str(s).strip().lower(), str(s).strip().lower()) in clothing for s in sizes or [])
    return any(int(n) in preferred for s in sizes or [] for n in re.findall(r'(?<!\d)\d{3}(?!\d)', str(s)))


def enrich(deals, preferences, now=None):
    now = now or datetime.now(timezone.utc)
    thresholds = preferences.get('price_drop_thresholds', {})
    fresh_hours = preferences.get('freshness', {}).get('act_now_hours', 24)
    for d in deals:
        category = d.get('category', 'ski')
        text = ' '.join(str(d.get(k, '')) for k in ('title', 'source', 'url')).lower()
        d['id'] = listing_id(d)
        d['is_watchlist'] = any(x.lower() in text for x in preferences.get('watch_terms', [])) or d['url'] in preferences.get('watch_urls', [])
        d['is_muted'] = any(x.lower() in text for x in preferences.get('muted_terms', [])) or d['url'] in preferences.get('muted_urls', [])
        d['already_owned'] = any(x.lower() in text for x in preferences.get('owned_terms', [])) or d['url'] in preferences.get('owned_urls', [])
        d['matches_my_size'] = size_match(category, d.get('sizes'), preferences.get('my_ski_sizes', []), preferences.get('clothing_sizes', []))
        d['matches_family_size'] = category == 'ski' and size_match(category, d.get('sizes'), preferences.get('family_ski_sizes', []), [])
        d['matches_size'] = d['matches_my_size'] or d['matches_family_size']
        cap = preferences.get('max_prices', {}).get(category)
        d['matches_price'] = cap is None or float(d['current_price']) <= float(cap)
        d['age_hours'] = age_hours(d.get('last_verified_at'), now)
        d['is_fresh'] = not d.get('is_cached') and d['age_hours'] is not None and d['age_hours'] <= fresh_hours
        d['verified_fit'] = d['matches_size'] and d.get('price_scope') == 'exact' and d.get('stock_status') == 'in_stock' and d['is_fresh']
        limits = thresholds.get(category, {'amount': 25, 'percent': 10})
        change = float(d.get('price_change') or 0)
        percent = float(d.get('price_change_percent') or 0)
        d['meaningful_drop'] = d['is_fresh'] and change < 0 and (abs(change) >= limits['amount'] or abs(percent) >= limits['percent'])
        d['matches_preferences'] = d['matches_size'] and d['matches_price'] and not d['is_muted'] and not d['already_owned']
        observations = int(d.get('observation_count') or 0)
        low = d.get('lowest_price')
        high = d.get('highest_price')
        d['is_lowest_seen'] = bool(observations >= 3 and low is not None and high is not None and high > low and d['current_price'] <= low)
        history_value = d['meaningful_drop'] or d['is_lowest_seen']
        intent = preferences.get('shopping_intent', {}).get(category, 'exceptional_only')
        eligible = d['verified_fit'] and d['matches_preferences']
        d['act_now_eligible'] = bool(eligible and history_value)
        d['verdict'] = 'Act now' if d['act_now_eligible'] else ('Worth watching' if eligible else 'Check details')
        if d['is_muted'] or d['already_owned']:
            d['verdict'] = 'Hidden'
        d['score'] = (40 * d['matches_size'] + 20 * d['verified_fit'] + 15 * d['matches_price'] + 12 * d['is_watchlist'] + 20 * d['meaningful_drop'] + 10 * d['is_lowest_seen'] + (5 if intent == 'active' else 0) - 100 * (d['is_muted'] or d['already_owned']) - 30 * (not d['is_fresh']))
    return deals
