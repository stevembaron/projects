"""Verified offer history. Legacy product-level observations remain untouched."""
from dataclasses import asdict, fields
from datetime import datetime, timedelta, timezone
import json
from deal_rules import age_hours, offer_key, timestamp


def cached_deals(history, source, found_at, limit, max_age_hours=72):
    from deal_monitor import Deal
    now = timestamp(found_at) or datetime.now(timezone.utc)
    allowed = {f.name for f in fields(Deal)}
    result = []
    for key, item in history.get('items', {}).items():
        # Legacy history may contain days of synthetic cached observations.
        if not key.startswith('v2|') or item.get('source') != source:
            continue
        age = age_hours(item.get('last_verified_at'), now)
        if age is None or age > max_age_hours:
            continue
        snapshot = item.get('snapshot', {})
        if not snapshot:
            continue
        d = Deal(**{k: v for k, v in snapshot.items() if k in allowed})
        d.is_cached = True
        d.last_verified_at = item['last_verified_at']
        result.append(d)
    return sorted(result, key=lambda d: d.current_price)[:limit]


def update(deals, path, generated_at):
    from deal_monitor import load_price_history
    history = load_price_history(path)
    items = history.setdefault('items', {})
    now = timestamp(generated_at)
    cutoff = (now - timedelta(days=89)).date().isoformat()
    today = now.date().isoformat()
    for d in deals:
        key = offer_key(d)
        existing = items.get(key, {})
        if d.is_cached:
            # No new observation, timestamp, stock assertion, or invented MSRP.
            continue
        observations = [x for x in existing.get('observations', []) if cutoff <= str(x.get('date', '')) <= today]
        previous = next(iter(sorted(observations, key=lambda x: x.get('seen_at', x['date']), reverse=True)), None)
        if previous:
            d.previous_price = previous['price']
            d.price_change = round(d.current_price - previous['price'], 2)
            d.price_change_percent = round(d.price_change / previous['price'] * 100, 1) if previous['price'] else None
            d.price_trend = 'down' if d.price_change < 0 else ('up' if d.price_change > 0 else 'flat')
        else:
            d.price_trend = 'new'
        # Preserve all intraday checks; cutoff is calendar-based.
        observations = [x for x in observations if x.get('seen_at') != generated_at]
        observations.append({'date': today, 'price': d.current_price, 'seen_at': generated_at, 'verified': True})
        d.first_seen_at = existing.get('first_seen_at', generated_at)
        d.last_verified_at = generated_at
        d.lowest_price = min(x['price'] for x in observations)
        d.highest_price = max(x['price'] for x in observations)
        d.observation_count = len(observations)
        d.history_start = min(x['date'] for x in observations)
        items[key] = {'title': d.title, 'url': d.url, 'source': d.source, 'image_url': d.image_url,
            'current_price': d.current_price, 'first_seen_at': d.first_seen_at,
            'last_seen_at': generated_at, 'last_verified_at': generated_at,
            'lowest_price': d.lowest_price, 'highest_price': d.highest_price,
            'observations': observations, 'snapshot': asdict(d)}
    history.update(schema_version=2, generated_at=generated_at, tracked_count=len(items))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(history, indent=2) + '\n')
    temporary.replace(path)
    return history
