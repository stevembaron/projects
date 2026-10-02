# Gear Deals

A static household deal dashboard, retailer collectors, verified offer history,
and a subscription-generated brief. Hosting and schedules remain on GitHub.

## Daily operation

`External Daily Deal Refresh` runs at 10:17 and 18:17 UTC (04:17 and 12:17 MDT;
03:17 and 11:17 MST). GitHub schedules may be delayed. Manual refresh and the
external Cloudflare dispatch route call the same workflow. The old ski-only
manual workflow now delegates to that workflow. A shared concurrency group
serializes refreshes and deployments.

The refresh collects clothing and skis independently, writes a shared
`data/tracker.json`, asks Claude Code for decisions, validates them, rebuilds
the dashboard, commits generated files, then deploys a public-only `_site`
directory. Collection or brief failures are reported separately. A failed
brief never replaces the last successfully validated one.

No paid model API calls are made by these scripts. The existing
`CLAUDE_CODE_OAUTH_TOKEN` secret powers Claude Code through its subscription.
The footer identifies the provider and does not claim an unreported model.

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
Claude writes JSON with a snapshot ID, up to three Act now listing IDs and up
to five Watch listing IDs, each with a short rationale. The renderer looks up
all prices, sizes and purchase URLs itself. Unknown IDs, stale snapshots,
invalid eligibility and invented dollar figures/URLs in rationales are rejected.
Textual rationale is still model-generated and should not be treated as
independently verified product research.

`python3 scripts/deal_analyst.py --render-only /tmp/gear-decisions.json` validates
and publishes. Archives use timestamps, so the second daily run no longer
overwrites the morning brief. Failed validation retains the prior brief.

## ChatGPT Plus / Astra migration

The required future route is **ChatGPT plan OAuth**, with no paid API fallback.
It is not activated in this change. Sign in with ChatGPT supports eligible
open-source/local clients and documents self-hosted VMs. GitHub-hosted unattended
runner support and persistent token renewal have not been verified. No VM is
required for this upgrade, and Claude stays active until that migration gate passes.

After completing the official SIWC consent flow, the optional read-only check is:

```
python3 scripts/check_chatgpt_plan.py --credentials /protected/path/chatgpt-auth.json
```

It checks for plan consent and whether `gpt-6-astra` is in the account's model
catalog. It does not perform inference, search for existing credentials, log
secrets, or prove GitHub runner compatibility. Do not use a copied browser cookie
or arbitrary Codex token in its place.

Official references:
- https://developers.openai.com/siwc/token-sharing-open-source
- https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference
- https://developers.openai.com/siwc/token-sharing-open-source/self-hosted-vms

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
generation is subscription-authenticated in the workflow.

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
