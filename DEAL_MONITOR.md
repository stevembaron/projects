# Gear Deals

A static household deal dashboard, retailer collectors, verified offer history,
and a subscription-generated brief. GitHub handles collection and hosting; ChatGPT handles the scheduled brief.

## Daily operation

`External Daily Deal Refresh` runs at 10:17 and 18:17 UTC (04:17 and 12:17 MDT;
03:17 and 11:17 MST). GitHub schedules may be delayed. Manual refresh and the
external Cloudflare dispatch route call the same workflow. The old ski-only
manual workflow now delegates to that workflow. A shared concurrency group
serializes refreshes and deployments.

The refresh collects clothing and skis independently and exports a compact
`data/chatgpt_brief_input.json` alongside the shared tracker. A ChatGPT scheduled
task reads that file through the connected GitHub app and writes only
`data/chatgpt_decisions.json` on main. The resulting push validates the snapshot,
IDs and eligibility, commits the successful brief and archive, and deploys Pages.
Invalid or stale decisions retain the last good brief and record a rejection in
`data/chatgpt_brief_status.json`. Repeated decisions for a published snapshot are
idempotent. Source text is untrusted data, never instructions.

No paid model API or Claude call is made. ChatGPT uses the scheduled task's
normal subscription allowance. No OpenAI API key, OAuth token export, VM or
Claude subscription is required. Subscription limits still apply.

## Preferences

Edit `config/deal_preferences.json` for scheduled runs. Your ski sizes are now
166–172 cm inclusive. Family sizes remain 154–160 cm and clothing S/M.
Budgets are read from this file throughout eligibility and ranking.

The dashboard's Preferences dialog supports local editing, import and export.
Watch, Not interested and Already bought persist on that browser. To apply
those changes across devices and to the scheduled analyst, export the JSON
and replace `config/deal_preferences.json` through the link in the dialog.
A push rebuilds the dashboard with the published configuration. No GitHub or
model credential belongs in this public dashboard.

`shopping_intent` supports `active` and `exceptional_only`. No inventory is
inferred for you: populate `owned_terms`/`owned_urls` with what you want excluded.
Freshness defaults: 24 hours for Act now; cached offers expire after 72 hours.
Meaningful reductions: at least $25 OR 10% for skis, $10 OR 15% for clothing.

## Data integrity

- Offer identity includes the retailer, product and variant/size. Different
  prices for different sizes remain separate offers.
- Search/catalog prices without verified variant prices are labelled From.
- Exact comparisons require matching product identity, model year, condition,
  available sizes, confirmed stock, and an exact price. Widths and years are
  never removed from identity.
- Cache fallback preserves the last successful check. It never creates a price
  observation, marks unknown stock as available, or invents an MSRP.
- History covers 90 calendar days and preserves intraday observations. The
  dashboard shows coverage dates and counts rather than implying full coverage.
- `v2|` history records are verified offer-level records. Legacy product-level
  history stays in the file for reference, but is not promoted to verified
  offer history: old caches and mixed sizes cannot be reliably reconstructed.
- Not-seen listings are included in the shared dataset only for non-failing
  sources. They are not asserted to be sold out; source scans are capped.
- Act now requires a matching size, budget, fresh exact price, confirmed stock,
  and meaningful price evidence. Cached data, unknown stock, and MSRP discounts
  alone cannot qualify.

## Brief contract

`python3 scripts/deal_analyst.py --dry-run` prepares household-relevant offers,
source health, verified history and recent structured recommendations.
ChatGPT writes JSON with a snapshot ID, up to three Act now listing IDs and up
to five Watch listing IDs, each with a short rationale. The renderer looks up
all prices, sizes and purchase URLs itself. Unknown IDs, stale snapshots,
invalid eligibility and invented dollar figures/URLs in rationales are rejected.
Textual rationale is still model-generated and should not be treated as
independently verified product research.

`python3 scripts/deal_analyst.py --render-only /tmp/gear-decisions.json` validates
and publishes. Archives use timestamps, so the second daily run no longer
overwrites the morning brief. Failed validation retains the prior brief.

## ChatGPT scheduled brief

The cloud task runs twice daily, at 05:00 and 13:00 America/Denver, after the
collector windows. Manage its schedule in ChatGPT Scheduled. It uses the account's
available task model; the pipeline does not claim a particular model name.
See `CHATGPT_BRIEF_TASK.md` for the durable task instructions. If a collector is
late or data is stale, the task preserves the prior brief instead of inventing data.
The next normal run retries with the newest snapshot.

Official reference: https://learn.chatgpt.com/docs/automations

## Local commands

```
python3 -m unittest discover tests
node --check assets/deals.js
python3 scripts/deal_monitor.py --config config/clothing_deal_sources.json
python3 scripts/deal_monitor.py
python3 scripts/deal_monitor.py --rerender
python3 scripts/deal_analyst.py --dry-run
python3 scripts/build_public.py
```

Open `ski-deals/index.html` or serve `_site` locally. The interface is plain
HTML/CSS/JavaScript with no build step or runtime framework dependency. Production
collectors use Python's standard library. `make brief` prepares the input only;
generation takes place in the ChatGPT scheduled task.

## Modules

- `deal_monitor.py`: retailer adapters and orchestration.
- `deal_history.py`: verified observations and expiring cache.
- `deal_rules.py`: offer identity, comparisons, eligibility and ranking.
- `deal_dataset.py`: shared dashboard/analyst snapshot.
- `deal_dashboard.py`, `assets/deals.*`: responsive UI and browser preferences.
- `deal_analyst.py`, `deal_brief.py`: model input, validated decisions and rendering.
- `build_public.py`: public asset staging, preserving the repository's other sites.

## Verification and deployment

CI runs offline regressions on pull requests and before publishing. Tests cover
variant prices, cross-store identity, stale cache, calendar history, budget/size
eligibility, brief validation, and public asset staging. Browser smoke tests are
in `tests/browser_smoke.cjs` and require Playwright with Chromium installed.
After deployment, use the workflow summary and Store coverage panel to verify
collection, brief validation, and deployment separately.
