# Ski Gear Deal Monitor

This project now includes a local deal monitor that can check retailer URLs for ski gear prices without API access.

## How It Works

- Add retailer category, sale, search, or product URLs to `config/deal_sources.json`.
- Run `python3 scripts/deal_monitor.py`.
- Open `data/deals.html` for a readable report.
- Open `ski-deals/index.html` for the web-published version.
- Check `data/deal_report.md` for a compact daily summary.
- Check `data/deals.json` if you want raw structured output later.

The monitor looks for product metadata and linked text with prices, filters for ski gear keywords, ranks the best-looking deals, and writes a daily report.

Sierra and evo block plain automated requests, so their configured sources use a reader fallback. The script still tries the retailer URL first, then falls back to a readable copy of the page and parses product links/prices from that.

## Add URLs

Edit `config/deal_sources.json` and add sources like this:

```json
{
  "name": "Retailer ski sale",
  "url": "https://retailer.example/ski/sale",
  "enabled": true
}
```

Good URLs are usually sale pages, clearance pages, category pages, brand searches, or individual product pages.

## Tune Results

- `keywords`: gear terms to keep.
- `exclude_keywords`: terms to ignore.
- `min_discount_percent`: minimum discount when the page exposes both original and sale price.
- `max_results_per_source`: cap noisy sources.

Some sites render prices with JavaScript after the page loads or block automated requests. Those may need a site-specific selector or a browser-based scraper later.

## Daily Use

From Terminal, run either:

```bash
make deals
```

or:

```bash
python3 scripts/deal_monitor.py
```

For the easiest Mac workflow, double-click `Run Ski Deals.command`. It runs the monitor and opens the HTML report.

The HTML report is sorted from lowest price to highest price:

```text
data/deals.html
```

The same page is also written to the static web app path:

```text
ski-deals/index.html
```

After committing and pushing to the GitHub Pages branch, it will be available at:

```text
https://stevembaron.github.io/projects/ski-deals/
```
