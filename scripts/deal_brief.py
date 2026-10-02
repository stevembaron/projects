"""Validate model decisions against observed offers, then render trusted values."""
from datetime import datetime, timezone
import hashlib
import copy
import html
import json
from pathlib import Path


def snapshot_id(dataset):
    stable = {'generated_at': dataset.get('generated_at'), 'preferences': dataset.get('preferences'),
              'deals': [{k: d.get(k) for k in ('id', 'current_price', 'sizes', 'stock_status', 'last_verified_at', 'price_scope')} for d in dataset['deals']]}
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()[:20]


def validate_decisions(result, dataset, now=None):
    if not isinstance(result, dict) or result.get('snapshot_id') != snapshot_id(dataset):
        raise ValueError('Brief does not match the current data snapshot')
    from deal_rules import enrich
    current = enrich(copy.deepcopy(dataset['deals']), dataset['preferences'], now)
    deals = {d['id']: d for d in current}
    seen, records = set(), []
    for section, maximum in [('act_now', 3), ('watch', 5)]:
        values = result.get(section, [])
        if not isinstance(values, list) or len(values) > maximum:
            raise ValueError(f'{section}: expected no more than {maximum} decisions')
        for item in values:
            if not isinstance(item, dict) or set(item) != {'id', 'reason'}:
                raise ValueError('Decisions must contain only id and reason')
            identity = item['id']
            d = deals.get(identity)
            if not d or identity in seen:
                raise ValueError('Unknown or duplicate listing ID')
            if d['is_muted'] or d['already_owned'] or not d['matches_price'] or not d['matches_size']:
                raise ValueError('Recommendation violates saved household preferences')
            if section == 'act_now' and not d['act_now_eligible']:
                raise ValueError('Act-now recommendation lacks verified fit, stock, freshness or price evidence')
            if not isinstance(item['reason'], str) or not 1 <= len(item['reason']) <= 360:
                raise ValueError('Reason must contain 1-360 characters')
            # Values and purchase links are always rendered from the source dataset.
            if 'http' in item['reason'].lower() or '$' in item['reason']:
                raise ValueError('Reason must not introduce unvalidated prices or links')
            seen.add(identity)
            records.append({'id': identity, 'section': section, 'reason': item['reason']})
    return {'schema_version': 2, 'snapshot_id': result['snapshot_id'], 'generated_at': datetime.now(timezone.utc).isoformat(),
            'source_generated_at': dataset['generated_at'], 'provider': 'claude_code_subscription', 'model': None, 'decisions': records}


def markdown(brief, dataset):
    deals = {d['id']: d for d in dataset['deals']}
    lines = [f"# Gear brief | {brief['generated_at'][:10]}"]
    for section, title in [('act_now', 'Act now'), ('watch', 'Worth watching')]:
        lines += ['', f'## {title}']
        records = [r for r in brief['decisions'] if r['section'] == section]
        if not records:
            lines.append('Nothing clears the bar today.' if section == 'act_now' else 'No additional picks.')
        for r in records:
            d = deals[r['id']]
            size = ', '.join(d.get('sizes') or [])
            lines.append(f"- **{d['title']}** | {'from ' if d.get('price_scope') != 'exact' else ''}${d['current_price']:.2f} | {size} | [{d['source']}]({d['url']}): {r['reason']}")
    if dataset['errors']:
        lines += ['', '## Coverage', *[f"- {e['source']}: unavailable or incomplete this run." for e in dataset['errors']]]
    return '\n'.join(lines) + '\n'


def html_page(brief, dataset):
    import deal_analyst
    body = deal_analyst.markdown_to_html(markdown(brief, dataset))
    return '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gear brief</title><link rel="stylesheet" href="../assets/deals.css"><main class="brief-page"><a href="../ski-deals/">← Gear Deals</a>' + body + '<p class="muted">Generated ' + html.escape(brief['generated_at']) + ' · Claude subscription · model not reported by runner</p></main></html>'


def publish(result, dataset, root):
    brief = validate_decisions(result, dataset)
    output = {root/'data/deal_brief.json': json.dumps(brief, indent=2)+'\n', root/'data/deal_brief.md': markdown(brief, dataset),
              root/'deal-brief/index.html': html_page(brief, dataset)}
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')
    output[root/f'data/briefs/{stamp}.json'] = json.dumps(brief, indent=2)+'\n'
    output[root/f'data/briefs/{stamp}.md'] = markdown(brief, dataset)
    for path, content in output.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix+'.tmp'); temp.write_text(content); temp.replace(path)
    return brief
