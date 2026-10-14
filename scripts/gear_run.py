#!/usr/bin/env python3
"""Gear deals: collect, value, personalize, brief, and build the site.

  python3 scripts/gear_run.py                 collect from every store, then build
  python3 scripts/gear_run.py --offline       rebuild from the last collection (after editing preferences)
  python3 scripts/gear_run.py --only evo,geartrade
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gear import brief, collect, history as hist, pipeline, prefs as preferences, site  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PATHS = {
    "sources": ROOT / "config" / "sources.json",
    "prefs": ROOT / "config" / "deal_preferences.json",
    "offers": DATA / "offers.json",
    "history": DATA / "history.json",
    "run": DATA / "run.json",
    "brief": DATA / "brief.json",
    "legacy_history": DATA / "price_history.json",
}


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path: Path, payload, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(payload, separators=(",", ":"), ensure_ascii=False) if compact else json.dumps(payload, indent=2, ensure_ascii=False)
    temporary.write_text(text + "\n", encoding="utf-8")
    temporary.replace(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def collect_offers(args, now: str, prefs: dict) -> tuple[list, list, dict, dict]:
    run = read_json(PATHS["run"], {})
    history = hist.load(PATHS["history"])
    previous = read_json(PATHS["offers"], {}).get("offers", [])
    if args.offline:
        offers = previous
        reports = run.get("reports", [])
        events = run.get("events", {})
        return offers, reports, history, events
    sources = collect.load_sources(PATHS["sources"])
    only = set(args.only.split(",")) if args.only else None
    reports_objects = collect.run(sources, now, workers=args.workers, only=only)
    reports = [r.summary() for r in reports_objects]
    offers = [o for r in reports_objects for o in r.offers]
    if only:
        # A partial run keeps every other store's last listings as they were.
        offers += [o for o in previous if o["source_id"] not in only]
        reports += [r for r in run.get("reports", []) if r["source_id"] not in only]
    first_history = not history.get("runs")
    events = hist.update(history, offers, reports, now)
    if first_history and PATHS["legacy_history"].exists():
        migrated = hist.migrate_legacy(history, PATHS["legacy_history"], offers)
        print(f"Carried over verified price history for {migrated} listing sizes from the previous tracker.")
    offers = pipeline.carry_over(offers, previous, reports, now, float(prefs.get("freshness", {}).get("hide_cached_after_hours", 72)))
    hist.save(history, PATHS["history"])
    write_json(PATHS["offers"], {"observed_at": now, "offers": offers}, compact=True)
    return offers, reports, history, events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--offline", action="store_true", help="rebuild from the last collection without fetching")
    parser.add_argument("--only", help="comma-separated source ids to refresh")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()

    now = now_iso()
    prefs = preferences.load(PATHS["prefs"])
    problems = preferences.validate(prefs)
    if problems:
        print("Preference problems: " + "; ".join(problems), file=sys.stderr)
        return 2
    offers, reports, history, events = collect_offers(args, now, prefs)
    if not offers:
        print("No listings available; nothing to build.", file=sys.stderr)
        return 1
    generated_at = now if not args.offline else read_json(PATHS["offers"], {}).get("observed_at", now)
    dataset = pipeline.build(offers, reports, history, prefs, generated_at, events, evaluated_at=now)

    run = read_json(PATHS["run"], {})
    market_log = run.get("market_log", [])
    if not args.offline:
        market_log = (market_log + [pipeline.market_snapshot(dataset)])[-120:]
    write_json(PATHS["run"], {"at": now, "generated_at": generated_at, "reports": reports, "events": events, "market_log": market_log,
                              "counts": dataset["counts"]})

    ski_facts = brief.facts(dataset, "ski", "me", market_log)
    clothing_facts = brief.facts(dataset, "clothing", "me")
    family_facts = brief.facts(dataset, "ski", "family", market_log) if any(p["id"] == "family" for p in prefs["profiles"]) else None
    briefs = {
        "generated_at": generated_at,
        "house": {"ski": brief.house_brief(ski_facts), "clothing": brief.house_brief(clothing_facts),
                  **({"family": brief.house_brief(family_facts)} if family_facts else {})},
    }
    write_json(PATHS["brief"], briefs)
    site.build(ROOT, dataset, briefs)

    counts = dataset["counts"]
    print(f"Collected {counts['collected']} listings; published {counts['published']} ({counts['new']} new).")
    for report in reports:
        if report["status"] not in ("ok", "disabled"):
            print(f"  {report['name']}: {report['status']} - {report.get('error') or '; '.join(report.get('notes') or [])}", file=sys.stderr)
    healthy = sum(1 for r in reports if r["status"] in ("ok", "partial"))
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
