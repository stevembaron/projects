# Powder Hunter: gear deals

A personal ski-gear deal finder. Twice a day it reads sale, demo, blemished and secondhand listings from about twenty stores, works out which prices are actually good, ranks them for each person in the household, writes a brief, and publishes a static dashboard at `https://stevembaron.github.io/projects/ski-deals/`.

## What runs where

| Part | Automatic? | Where |
|---|---|---|
| Collect listings, value them, rank them, write the market brief, build the site | Automatic, 04:17 and 12:17 Mountain | `.github/workflows/gear-deals.yml` (also runs on every push to main and on manual dispatch) |
| Editor's brief in ChatGPT | Your ChatGPT scheduled task, or by hand from the dashboard | `CHATGPT_BRIEF_TASK.md` |
| Preferences, saved items, targets | Instantly in your browser; export to make the daily build use them | dashboard **Preferences**, `config/deal_preferences.json` |
| Local run | When you double-click | `Run Ski Deals.command` (opens the dashboard on this Mac; pushes nothing) |

No paid services, API keys or servers. GitHub Actions and Pages are the only infrastructure; the optional Cloudflare worker in `external-scheduler/` can wake the workflow if GitHub's own schedule is late.

## Commands

```
python3 scripts/gear_run.py                 # collect from every store and build
python3 scripts/gear_run.py --offline       # rebuild from the last collection (after editing preferences)
python3 scripts/gear_run.py --only evo,geartrade
python3 scripts/gear_run.py --accept-brief reply.json
python3 -m unittest discover tests
make serve                                   # then open http://127.0.0.1:8000/ski-deals/
```

## How listings are collected

`config/sources.json` lists every store. Most are Shopify stores, read through their public `/collections/<handle>/products.json` feed: structured prices, compare-at prices, sizes, stock and tags, with no page scraping. The fetcher (`scripts/gear/net.py`) identifies itself honestly, honours robots.txt (including the `*` and `$` wildcards Shopify uses), waits between requests to the same store, and reports every failure. To add a Shopify store, copy an entry and set its collection handles; another platform needs one small adapter in `scripts/gear/adapters.py`.

Each store's result is recorded as `ok`, `partial` (a page cap was hit or one feed failed), `failed` or `blocked`. A store that fails keeps its last good listings for up to 72 hours, clearly marked as not freshly checked; it never quietly drops to zero. A listing counts as sold or removed only when its store was read completely and the listing was missing.

Listing text is normalized into brand, model, model year, waist width, length (never confused with waist), gender, condition (`new`, `blem`, `new_with_tags`, `demo`, `excellent`, `good`, `fair`, `used`, including Geartrade's "UnNew With Tags"), bindings (flat, included, demo) and size. Ski character (category, playfulness, how demanding, ability range, quality tier) comes from the curated catalog in `scripts/gear/data/ski_catalog.json`, or is inferred from width and construction and labelled as inferred.

## How deals are valued (`scripts/gear/valuation.py`)

The deal score (0–100) estimates a fair price for this exact listing and compares the real cost with it:

- **List price evidence:** the retailer's compare-at price, marked "confirmed" when two or more stores agree within 4%.
- **Market price:** what other stores currently charge for the same model, width, year and package.
- **Age:** a typical new-stock discount by seasons since the model year (current models ~8%, last season's ~35%, two seasons ~45%, older ~52–58%; deeper in spring).
- **Condition:** how much of the new price each condition typically keeps (demo ~70%, used-good ~52%; apparel resells lower).
- **Our own history:** verified price cuts and 90-day lows for this listing.

Points: value against fair price (45), absolute savings (10), verified price drop or historical low (15), model quality (15), condition and age (10), seller reliability (5). There are penalties for "from" prices, unconfirmed stock and headline discounts that mostly reflect an old model. Confidence (high/medium/low) reflects how much evidence agrees. No list price is ever invented: without evidence there is no fair price, and the listing says so.

A 70%-off headline on a three-season-old ski is usually a normal price; a 35%-off current model can be the better deal. The engine shows this explicitly.

## How listings are ranked for you (`scripts/gear/fit.py`, mirrored in `assets/fit.js`)

Fit (0–100) per profile: length against the ideal and acceptable ranges (never at or above the hard limit), budget, gender, playful versus carving-oriented character, how demanding the ski is, entry-level skis for an advanced skier, touring skis for resort skiing, categories you avoid, and near-duplicates of skis you own (same family, or same type within 5 mm). The verdict combines both scores:

- **Buy now:** deal ≥ 78, fit ≥ 70, confidence not low, exact price, in stock, checked within your freshness window; a near-duplicate of something you own needs ≥ 88.
- **Strong deal:** deal ≥ 64 and fit ≥ 60.
- **Worth watching:** deal ≥ 48 and fit ≥ 45, or a great fit at a fair-ish price.
- **Pass:** wrong size or budget, a poor match, or not a compelling price. The reason is always shown.

A target price you set wins: at or below it the listing becomes Buy now (or Strong deal if not freshly verified).

## Preferences (`config/deal_preferences.json`, schema 3)

Profiles (`me`, `family`) each have ski length ranges, budget, style, ability, cuts, categories to avoid, categories already owned, the skis you own (`quiver`), conditions and binding preference, plus clothing sizes and budget. Watch and muted terms, saved, dismissed and owned listings and target prices are shared. The two quiver skis came from an earlier ChatGPT brief; edit them if they are wrong.

## The brief

Every build writes a **market brief** from the data (`scripts/gear/brief.py`): best picks for you, what moved (price cuts, new listings, sold items), listings close to a buy with the price that would make them a strong deal, market notes by store and brand, good deals that don't fit you, listings to double-check, and coverage gaps. It always has something real to say, even when nothing is worth buying.

The optional **editor's brief** is written in ChatGPT from `data/brief_packet.json`. The reply is checked before it is shown: every listing must exist, every dollar figure and percentage must match the packet, no links, and nothing may be called "Buy now" unless its verdict is. From the dashboard you can show an accepted reply on your device immediately, or publish it for every device by committing it to `data/brief_inbox/` (the dashboard opens GitHub with the file prefilled). Rejections are shown on the page with the reasons.

## Dashboard

`ski-deals/index.html` with `assets/gear.js`, `assets/fit.js`, `assets/gear.css` and the generated `ski-deals/data.js`. No build step or framework. The Skis/Clothing switch is at the top and opens on Skis. Views: For you, All deals, New, Price drops, Saved, Hidden. Each listing shows its verdict and score, sizes coloured against your range, why it is interesting, why it fits or doesn't, price against fair value and list price, condition, store, when it was checked, and on expansion its price history, evidence and score breakdown. You can save, set a target, compare up to three, dismiss, or mark as owned. **Since your last visit** lists new strong deals, target hits, cheaper saved items and saved items that sold. `ski-deals/alerts.xml` is an Atom feed of Buy now and Strong deal listings for any feed reader.

## Data files

| File | What it is |
|---|---|
| `data/offers.json` | every normalized listing from the last collection |
| `data/history.json` | price changes per listing size (only changes are stored) and the run log |
| `data/run.json` | per-store results for the last run and a market trend log |
| `data/brief.json` | market briefs, the accepted ChatGPT brief and its status |
| `data/brief_packet.json` | the packet for ChatGPT; `brief_packets.json` keeps the last six |
| `data/brief_inbox/` | drop a ChatGPT reply here to publish it |
| `data/briefs/` | archive of accepted ChatGPT briefs |

The old `/clothing-deals/` and `/deal-brief/` addresses redirect to the dashboard.
