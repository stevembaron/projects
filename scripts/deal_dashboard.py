"""Static dashboard shell. Data and recommendations share a single snapshot."""
import json
import hashlib
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render_dashboard(payload, config):
    try:
        brief = json.loads((ROOT/'data/deal_brief.json').read_text())
    except (OSError, ValueError):
        brief = None
    try:
        payload['run_status'] = json.loads((ROOT/'data/run_status.json').read_text())
    except (OSError, ValueError):
        payload['run_status'] = None
    from deal_brief import snapshot_id
    current = bool(brief and brief.get('snapshot_id') == snapshot_id(payload))
    refresh_brief_page(brief, payload, current)
    data = json.dumps({'dataset': payload, 'brief': brief, 'briefCurrent': current}, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gear Deals | Your daily shortlist</title><link rel="stylesheet" href="../assets/deals.css"></head>
<body><main>
<header><div><p class="eyebrow">THE HOUSEHOLD GEAR WATCH</p><h1>Good gear. Better timing.</h1><p class="muted" id="freshness"></p></div><button id="openPreferences" class="secondary">Preferences</button></header>
<nav aria-label="Gear category" id="categories" class="category-toggle"><button data-category="ski" aria-pressed="true">Skis</button><button data-category="clothing" aria-pressed="false">Clothing</button></nav>
<div class="status" id="status" role="status"></div>
<nav aria-label="Deal views" id="views"><button data-view="today" aria-pressed="true">Today</button><button data-view="me" aria-pressed="false">For me</button><button data-view="family" aria-pressed="false">Family</button><button data-view="all" aria-pressed="false">All deals</button></nav>
<section class="metrics" id="metrics" aria-label="Deal summary"></section>
<section id="brief" class="brief-summary" aria-label="Buying brief" aria-live="polite"><!--inline-brief--></section>
<section class="browse"><div class="browse-heading"><h2 id="listTitle">Today's shortlist</h2><span class="muted" id="count" aria-live="polite"></span></div>
<details class="filters"><summary>Search and filters</summary><div class="filter-grid">
<label>Search<input id="search" type="search" placeholder="Brand, model, store"></label>
<label>Sort<select id="sort"><option value="relevance">Best match</option><option value="price">Lowest price</option><option value="drop">Largest verified drop</option><option value="new">Recently found</option></select></label>
<label>Store<select id="store"><option value="">All stores</option></select></label>
<label class="check"><input id="drops" type="checkbox"> Meaningful drops only</label>
<label class="check"><input id="budget" type="checkbox" checked> Within my budgets</label>
<label class="check"><input id="hidden" type="checkbox"> Include dismissed / owned</label>
<button id="reset" class="secondary">Reset filters</button><button id="share" class="secondary">Copy this view</button>
</div></details><div id="list" class="deal-list"></div></section>
<details class="health"><summary id="healthTitle">Store coverage</summary><div id="health"></div></details>
<footer>Prices are observed listings. Confirm your size, condition, bindings and checkout total with the retailer. <a href="../deal-brief/">Full brief</a></footer>
</main>
<dialog id="preferences"><form id="preferencesForm"><div class="dialog-heading"><h2>Your preferences</h2><button type="button" id="closePreferences" aria-label="Close preferences">×</button></div>
<p class="muted">Changes apply in this browser. Export them to use on another device or update the scheduled brief's saved preferences.</p>
<div class="pref-grid"><label>My ski sizes (cm)<input name="my_ski_sizes" required></label><label>Family ski sizes (cm)<input name="family_ski_sizes" required></label>
<label>Clothing sizes<input name="clothing_sizes" required></label><label>Ski budget ($)<input name="ski_budget" type="number" min="1" max="100000" required></label><label>Clothing budget ($)<input name="clothing_budget" type="number" min="1" max="100000" required></label>
<label>Watch terms, separated by commas<input name="watch_terms"></label><label>Muted terms<input name="muted_terms"></label><label>Already owned models<input name="owned_terms"></label>
<label>Ski shopping<select name="ski_intent"><option value="exceptional_only">Exceptional deals only</option><option value="active">Actively shopping</option></select></label>
<label>Clothing shopping<select name="clothing_intent"><option value="exceptional_only">Exceptional deals only</option><option value="active">Actively shopping</option></select></label></div>
<p id="preferenceError" class="error" role="alert"></p><div class="actions"><button type="submit">Save in this browser</button><button type="button" id="export" class="secondary">Export preferences</button><label class="import secondary">Import JSON<input id="import" type="file" accept="application/json,.json"></label><button type="button" id="restore" class="secondary">Restore published preferences</button></div>
<p class="muted">To update the automatic brief, replace <a href="https://github.com/stevembaron/projects/edit/main/config/deal_preferences.json" target="_blank" rel="noopener">saved preferences</a> with your exported JSON. Until then, the brief uses the published settings.</p>
</form></dialog><script id="gear-data" type="application/json">''' + data + '''</script><script src="../assets/deals.js" defer></script></body></html>'''

    for asset in ('deals.css', 'deals.js'):
        version = hashlib.sha256((ROOT/'assets'/asset).read_bytes()).hexdigest()[:12]
        page = page.replace('../assets/'+asset, '../assets/'+asset+'?v='+version)
    return page.replace('<!--inline-brief-->', initial_brief(brief, payload, current))


def initial_brief(brief, dataset, current):
    if not brief:
        return '<h2>Ski brief</h2><p>A buying brief will appear after the next successful ChatGPT run.</p>'
    from deal_analyst import markdown_to_html
    from deal_brief import markdown
    eligible = {d['id'] for d in dataset['deals'] if d.get('category') == 'ski'
                and d.get('matches_preferences')}
    selected = dict(brief, decisions=[r for r in brief.get('decisions', []) if r['id'] in eligible])
    text = markdown(selected, dataset).split('\n', 1)[1]
    notice = '' if current else '<p class="warning">Previous brief. Confirm current prices and availability before buying.</p>'
    return '<h2>Ski brief</h2><p class="muted">Last brief: ' + html.escape(brief['generated_at']) + '</p>' + notice + markdown_to_html(text)


def refresh_brief_page(brief, dataset, current):
    from deal_analyst import markdown_to_html
    from deal_brief import html_page
    output = ROOT/'deal-brief/index.html'
    output.parent.mkdir(parents=True, exist_ok=True)
    if current:
        content = html_page(brief, dataset)
    else:
        try:
            previous = (ROOT/'data/deal_brief.md').read_text()
        except OSError:
            previous = 'No brief has been generated yet.'
        content = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Previous gear brief</title><link rel="stylesheet" href="../assets/deals.css"><main class="brief-page"><a href="../ski-deals/">← Gear Deals</a><p class="warning">Previous brief. These recommendations have not been validated against the current data and preferences. Check the dashboard for current listings.</p>' + markdown_to_html(previous) + '</main></html>'
    output.write_text(content)
