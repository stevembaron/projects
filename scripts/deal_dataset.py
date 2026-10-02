"""One normalized snapshot consumed by both the UI and the analyst."""
from datetime import datetime, timezone
from deal_rules import enrich, comparisons, offer_key, age_hours


def build_dataset(ski, clothing, preferences, history=None, now=None):
    now = now or datetime.now(timezone.utc)
    deals, errors, health = [], [], []
    cache_hours = preferences.get('freshness', {}).get('hide_cached_after_hours', 72)
    for category, payload in [('ski', ski or {}), ('clothing', clothing or {})]:
        source_errors = {e['source']: e for e in payload.get('errors', [])}
        errors.extend(payload.get('errors', []))
        names = set(source_errors)
        for original in payload.get('deals', []):
            d = dict(original, category=category)
            names.add(d['source'])
            # Old generated data lacks offer-level verification. Display it conservatively.
            if 'price_scope' not in d:
                d['price_scope'] = 'from'
            if not d.get('is_cached'):
                d.setdefault('last_verified_at', d.get('found_at'))
            age = age_hours(d.get('last_verified_at'), now)
            if d.get('is_cached') and (age is None or age > cache_hours):
                continue
            deals.append(d)
        for name in sorted(names):
            rows = [d for d in deals if d['source'] == name and d['category'] == category]
            verified = [d['last_verified_at'] for d in rows if d.get('last_verified_at') and not d.get('is_cached')]
            health.append({'source': name, 'category': category, 'status': 'degraded' if name in source_errors else ('ok' if verified else 'unverified'),
                'count': len(rows), 'last_verified_at': max(verified) if verified else None,
                'error': source_errors.get(name, {}).get('error')})
    enrich(deals, preferences, now)
    for d in deals:
        record = (history or {}).get('items', {}).get(offer_key(d), {})
        d['price_series'] = [x['price'] for x in record.get('observations', []) if x.get('verified')][-90:]
    notes = comparisons(deals)
    for d in deals:
        d['comparison'] = notes.get(id(d))
    deals.sort(key=lambda d: (-d['score'], d['current_price']))
    current = {offer_key(d) for d in deals}
    failed = {e['source'] for e in errors}
    missing = []
    for key, item in (history or {}).get('items', {}).items():
        age = age_hours(item.get('last_verified_at'), now)
        if key.startswith('v2|') and key not in current and item.get('source') not in failed and age is not None and age <= 7 * 24:
            missing.append({k: item.get(k) for k in ('title', 'source', 'url', 'last_verified_at', 'current_price')})
    return {'schema_version': 2, 'generated_at': ski.get('generated_at'), 'evaluated_at': now.isoformat(),
        'deal_count': len(deals), 'deals': deals, 'errors': errors, 'source_health': health,
        'disappeared_deals': sorted(missing, key=lambda d: d['last_verified_at'], reverse=True)[:20],
        'preferences': preferences}
