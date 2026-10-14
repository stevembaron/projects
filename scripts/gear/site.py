"""Static site output: page shell, data file, alert feed, and redirects for old URLs."""
from __future__ import annotations

import hashlib
import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .aibrief import prompt_text

REPO_URL = "https://github.com/stevembaron/projects"


def asset_version(root: Path, name: str) -> str:
    try:
        return hashlib.sha256((root / "assets" / name).read_bytes()).hexdigest()[:10]
    except OSError:
        return "0"


def script_json(payload: Any) -> str:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def page(root: Path, brief_headline: str) -> str:
    v = {name: asset_version(root, name) for name in ("gear.css", "fit.js", "gear.js")}
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Powder Hunter · Ski deals</title>
<meta name="description" content="{html.escape(brief_headline)}">
<link rel="alternate" type="application/atom+xml" title="Powder Hunter alerts" href="alerts.xml">
<link rel="stylesheet" href="../assets/gear.css?v={v['gear.css']}">
</head>
<body>
<a class="skip" href="#deals">Skip to deals</a>
<header class="masthead">
  <div class="wrap masthead-row">
    <div class="brand"><span class="mark" aria-hidden="true"></span><span>Powder&nbsp;Hunter</span></div>
    <div class="masthead-meta" id="freshness" aria-live="polite"></div>
    <div class="masthead-actions">
      <label class="profile-switch"><span class="sr">Shopping for</span><select id="profile" aria-label="Shopping for"></select></label>
      <button class="ghost" id="openPrefs" type="button">Preferences</button>
    </div>
  </div>
</header>
<main class="wrap">
  <nav class="category" aria-label="Gear category">
    <button type="button" data-category="ski" aria-pressed="true"><span>Skis</span><b id="countSki"></b></button>
    <button type="button" data-category="clothing" aria-pressed="false"><span>Clothing</span><b id="countClothing"></b></button>
  </nav>
  <section id="alerts" class="alerts" aria-live="polite" hidden></section>
  <section id="brief" class="brief" aria-labelledby="briefHeadline"></section>
  <section class="scoreboard" id="scoreboard" aria-label="Today at a glance"></section>
  <section class="deals" id="deals" aria-labelledby="listTitle">
    <div class="toolbar">
      <div class="views" role="tablist" aria-label="Deal views" id="views"></div>
      <div class="tools">
        <label class="search"><span class="sr">Search</span><input id="search" type="search" placeholder="Search brand, model, store" autocomplete="off"></label>
        <label class="sort"><span class="sr">Sort</span><select id="sort">
          <option value="verdict">Best for me</option><option value="score">Deal score</option><option value="value">Most under fair price</option>
          <option value="price">Lowest price</option><option value="drop">Biggest price drop</option><option value="new">Newest</option></select></label>
        <button class="ghost" type="button" id="toggleFilters" aria-expanded="false" aria-controls="filters">Filters</button>
      </div>
    </div>
    <div class="filters" id="filters" hidden></div>
    <div class="list-head"><h2 id="listTitle">For you</h2><span id="listCount" aria-live="polite"></span></div>
    <div id="list" class="list"></div>
    <button type="button" class="more ghost" id="more" hidden>Show more</button>
  </section>
  <section class="gone" id="gone" aria-labelledby="goneTitle"></section>
  <details class="health" id="health"><summary id="healthTitle">Store coverage</summary><div id="healthBody"></div></details>
  <footer class="foot">
    <p>Prices are what each store listed when we checked. Fair prices are estimates from list prices, other stores and price history; confirm size, condition, bindings and the checkout total with the seller.</p>
    <p><a href="alerts.xml">Alert feed (Atom)</a> · <a href="{REPO_URL}/blob/main/DEAL_MONITOR.md">How this works</a></p>
  </footer>
</main>
<div class="compare-bar" id="compareBar" hidden></div>
<dialog id="prefsDialog" class="sheet" aria-labelledby="prefsTitle"></dialog>
<dialog id="studioDialog" class="sheet" aria-labelledby="studioTitle"></dialog>
<dialog id="compareDialog" class="sheet wide" aria-labelledby="compareTitle"></dialog>
<noscript><p class="wrap">This dashboard needs JavaScript. The latest data is in data.js.</p></noscript>
<script src="data.js?v={{DATA_VERSION}}"></script>
<script src="../assets/fit.js?v={v['fit.js']}"></script>
<script src="../assets/gear.js?v={v['gear.js']}" defer></script>
</body>
</html>
"""


def slim(dataset: dict[str, Any], keep_ids: set[str] | None = None) -> dict[str, Any]:
    """What the page needs. Fit and verdicts are recomputed in the browser from
    preferences, so only listings that fit a profile, score well, moved, or are
    cited by a brief are shipped."""
    keep_ids = keep_ids or set()
    watch = [t.lower() for t in dataset["preferences"].get("watch_terms", [])]
    items = []
    for item in dataset["items"]:
        fits = any(not f["hard"] for f in item.get("fit", {}).values())
        moved = (item.get("history") or {}).get("change") not in (None, 0)
        watched = any(t in item["title"].lower() for t in watch)
        if not (fits or item["score"] >= 35 or moved or watched or item["id"] in keep_ids):
            continue
        out = {k: v for k, v in item.items() if k not in ("fit", "verdict", "model") and v not in (None, [], {}, "")}
        if out.get("history"):
            out["history"] = {k: v for k, v in out["history"].items() if v not in (None, [], 0) or k == "observations"}
        out["variants"] = [{k: v for k, v in variant.items() if v is not None} for variant in item["variants"]]
        items.append(out)
    return dict(dataset, items=items)


def alerts_feed(dataset: dict[str, Any], updated: str) -> str:
    entries = []
    for item in dataset["items"]:
        for profile, (verdict, reason) in item.get("verdict", {}).items():
            if verdict not in ("buy_now", "strong"):
                continue
            label = "BUY NOW" if verdict == "buy_now" else "STRONG DEAL"
            fit = item["fit"][profile]
            title = f"{label}: {item['title']} — ${fit.get('price') or item['price']:,.2f} at {item['source']}"
            summary = "; ".join(filter(None, [reason, (item.get("evidence") or [""])[0], fit.get("variant") and f"Size {fit['variant']}"]))
            entry_id = f"tag:powderhunter,{item['id']}-{profile}-{int(item['price'])}"
            entries.append(f"""<entry><id>{html.escape(entry_id)}</id><title>{html.escape(title)}</title><updated>{html.escape(item.get('verified_at') or updated)}</updated>
<link href="{html.escape(item['url'])}"/><summary>{html.escape(summary)}</summary></entry>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Powder Hunter alerts</title><id>tag:powderhunter,alerts</id><updated>{html.escape(updated)}</updated>
{''.join(entries[:60])}
</feed>
"""


def redirect(target: str, title: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<meta http-equiv="refresh" content="0; url={html.escape(target)}"><link rel="canonical" href="{html.escape(target)}"></head>
<body><p><a href="{html.escape(target)}">{html.escape(title)} moved here.</a></p></body></html>
"""


def build(root: Path, dataset: dict[str, Any], briefs: dict[str, Any], packet: dict[str, Any]) -> None:
    out = root / "ski-deals"
    out.mkdir(parents=True, exist_ok=True)
    cited = {ref for b in list((briefs.get("house") or {}).values()) + [briefs.get("ai") or {}] for sec in (b or {}).get("sections", []) for ref in sec.get("refs", [])}
    cited |= set(packet.get("listings", {}))
    payload = {"dataset": slim(dataset, cited), "briefs": briefs, "packet": packet, "prompt": prompt_text(packet), "repo": REPO_URL}
    data = "window.GEAR=" + script_json(payload) + ";\n"
    (out / "data.js").write_text(data, encoding="utf-8")
    headline = (briefs.get("house", {}).get("ski") or {}).get("headline", "Ski deals")
    shell = page(root, headline).replace("{DATA_VERSION}", hashlib.sha256(data.encode()).hexdigest()[:10])
    (out / "index.html").write_text(shell, encoding="utf-8")
    (out / "alerts.xml").write_text(alerts_feed(dataset, dataset["generated_at"]), encoding="utf-8")
    for folder, target, title in (("clothing-deals", "../ski-deals/?category=clothing", "Clothing deals"),
                                  ("deal-brief", "../ski-deals/#brief", "The gear brief")):
        path = root / folder
        path.mkdir(exist_ok=True)
        (path / "index.html").write_text(redirect(target, title), encoding="utf-8")
