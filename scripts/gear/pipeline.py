"""Collected offers + history + preferences -> the published dataset."""
from __future__ import annotations

import statistics
from datetime import datetime, timedelta, timezone
from typing import Any

from . import catalog, fit, history as hist, valuation
from .textparse import CONDITION_LABELS, WOMEN_PATTERN as WOMEN_WORDS

PUBLISH_KINDS = ("ski", "clothing", "binding")
NEW_HOURS = 48


def parse(value: Any) -> datetime | None:
    return hist.parse_time(value)


def carry_over(current: list[dict[str, Any]], previous: list[dict[str, Any]], reports: list[dict[str, Any]], now: str, max_hours: float) -> list[dict[str, Any]]:
    """Keep the last good listings for a source that failed this run, clearly marked stale."""
    status = {r["source_id"]: r["status"] for r in reports}
    have = {o["id"] for o in current}
    moment = parse(now)
    kept = []
    for offer in previous:
        if offer["id"] in have or status.get(offer["source_id"]) not in ("failed", "blocked", "partial"):
            continue
        seen = parse(offer.get("observed_at"))
        if not seen or (moment - seen).total_seconds() / 3600 > max_hours:
            continue
        kept.append(dict(offer, stale=True))
    return current + kept


def ski_facts(offer: dict[str, Any]) -> dict[str, Any]:
    if offer.get("kind") != "ski":
        return {}
    return catalog.ski_profile(offer.get("brand"), offer.get("model") or "", offer.get("model_key") or "", offer.get("gender"), offer.get("waist_mm"), offer.get("title") or "")


def reconcile_gender(offer: dict[str, Any], family_gender: str) -> dict[str, Any]:
    """Store tags are unreliable for skis sold to everyone. The title wins; then the catalog."""
    if WOMEN_WORDS.search(offer.get("title") or ""):
        return offer
    if family_gender == "womens" and offer.get("gender") != "womens":
        return dict(offer, gender="womens")
    if family_gender == "unisex" and offer.get("gender") == "womens":
        return dict(offer, gender="unisex")
    return offer


def is_dealish(offer: dict[str, Any], value: dict[str, Any], stats: dict[str, Any], prefs: dict[str, Any]) -> bool:
    if offer.get("condition") not in ("new", None):
        return True
    if (value.get("claimed_pct") or 0) >= 15 or (value.get("vs_fmv_pct") or 0) >= 10:
        return True
    if stats.get("change") is not None and stats["change"] < 0:
        return True
    text = f"{offer.get('title')} {offer.get('source')}".lower()
    return any(t.lower() in text for t in prefs.get("watch_terms") or [])


def build(offers: list[dict[str, Any]], reports: list[dict[str, Any]], history: dict[str, Any], prefs: dict[str, Any],
          now: str, events: dict[str, Any] | None = None, evaluated_at: str | None = None) -> dict[str, Any]:
    """`now` is when the data was collected; `evaluated_at` (default: now) is the clock used for freshness."""
    moment = parse(now) or datetime.now(timezone.utc)
    clock = parse(evaluated_at) or moment
    fresh_hours = float(prefs.get("freshness", {}).get("act_now_hours", 30))
    runs = history.get("runs", [])
    first_run = len(runs) <= 1
    # "New" means it appeared after tracking began, not that tracking just started.
    tracking_start = (parse(runs[0]["at"]) if runs else None) or moment
    new_after = tracking_start + timedelta(hours=1)
    market = valuation.build_market([o for o in offers if not o.get("stale")])
    items = []
    for offer in offers:
        if offer.get("kind") not in PUBLISH_KINDS or offer.get("gender") == "kids":
            continue
        if not any(v.get("available") is not False for v in offer["variants"]):
            continue
        facts = ski_facts(offer)
        if facts.get("source") == "catalog" and facts.get("gender"):
            offer = reconcile_gender(offer, facts["gender"])
        best = valuation.best_variant(offer)
        stats = hist.variant_stats(history["variants"].get(hist.variant_key(offer, best)), best["price"], now)
        value = valuation.value_offer(offer, market, stats, moment, facts)
        if not is_dealish(offer, value, stats, prefs):
            continue
        strong_at = None
        if value["fmv"] and value["score"] < 64 and value["score"] >= 25 and offer.get("price_scope") == "exact":
            strong_at = valuation.price_for_score(offer, market, stats, moment, facts, 64)
        record = history["offers"].get(offer["id"], {})
        first_seen = record.get("first") or offer.get("observed_at")
        seen_at = parse(offer.get("observed_at"))
        age_hours = (clock - seen_at).total_seconds() / 3600 if seen_at else None
        first = parse(first_seen)
        item = {
            "id": offer["id"],
            "kind": offer["kind"],
            "title": offer["title"],
            "brand": offer.get("brand"),
            "model": offer.get("model"),
            "model_key": offer.get("model_key"),
            "year": offer.get("model_year"),
            "gender": offer.get("gender"),
            "condition": offer.get("condition"),
            "condition_text": CONDITION_LABELS.get(offer.get("condition") or "", "Condition not stated"),
            "condition_label": offer.get("condition_label"),
            "source": offer["source"],
            "source_id": offer["source_id"],
            "seller_type": (offer.get("seller") or {}).get("type"),
            "url": offer["url"],
            "image": offer.get("image"),
            "bindings": offer.get("bindings"),
            "waist_mm": facts.get("waist_mm") or offer.get("waist_mm"),
            "category": facts.get("category"),
            "playful": facts.get("playful"),
            "demanding": facts.get("demanding"),
            "level": facts.get("level"),
            "tier": facts.get("tier"),
            "family": facts.get("family"),
            "summary": facts.get("summary"),
            "character_source": facts.get("source"),
            "variants": [{k: v.get(k) for k in ("label", "length_cm", "size", "price", "compare_at", "available")} for v in offer["variants"]],
            "price": best["price"],
            "price_scope": offer.get("price_scope", "exact"),
            "in_stock": best.get("available") is True,
            "shipping": offer.get("shipping"),
            "verified_at": offer.get("observed_at"),
            "fresh": bool(not offer.get("stale") and age_hours is not None and age_hours <= fresh_hours),
            "stale": bool(offer.get("stale")),
            "listed_at": offer.get("listed_at"),
            "first_seen": first_seen,
            "strong_at": strong_at,
            "is_new": bool(not first_run and first and first > new_after and (moment - first) <= timedelta(hours=NEW_HOURS)),
            "history": {k: stats.get(k) for k in ("observations", "previous_price", "change", "change_pct", "changed_at", "low_90", "high_90", "history_days", "series")},
            **{k: value[k] for k in ("score", "band", "confidence", "list_price", "list_basis", "claimed_pct", "fmv", "fmv_basis",
                                      "vs_fmv", "vs_fmv_pct", "street_low", "stores_with_product", "age_seasons", "points", "evidence", "flags", "cost")},
        }
        item["fit"] = {}
        item["verdict"] = {}
        for profile in prefs.get("profiles", []):
            result = fit.evaluate(item, profile, prefs)
            item["fit"][profile["id"]] = result
            target = (prefs.get("targets") or {}).get(item["id"])
            item["verdict"][profile["id"]] = list(fit.verdict(item, result, target))
        items.append(item)

    learned = fit.learn(items, prefs)
    if learned["brands"] or learned["categories"]:
        scoped = dict(prefs, learned=learned)
        for item in items:
            for profile in prefs.get("profiles", []):
                result = fit.evaluate(item, profile, scoped)
                item["fit"][profile["id"]] = result
                item["verdict"][profile["id"]] = list(fit.verdict(item, result, (prefs.get("targets") or {}).get(item["id"])))
    duplicates(items)
    items.sort(key=lambda i: (-i["score"], i["price"]))
    gone = gone_items(history, moment, prefs)
    return {
        "schema_version": 3,
        "generated_at": now,
        "items": items,
        "gone": gone,
        "sources": source_health(reports, history),
        "preferences": prefs,
        "counts": {
            "collected": len(offers),
            "published": len(items),
            "new": sum(1 for i in items if i["is_new"]),
        },
        "events": events or {},
    }


def duplicates(items: list[dict[str, Any]]) -> None:
    """Link the same product (model, width, year, condition) across stores."""
    groups: dict[tuple, list[dict[str, Any]]] = {}
    for item in items:
        if not item.get("brand") or not item.get("model_key"):
            continue
        model = item["model_key"][:-2] if item.get("gender") == "womens" and item["model_key"].endswith(" w") else item["model_key"]
        key = (item["kind"], item["brand"], model, item.get("gender") == "womens", item.get("year"), item.get("condition"),
               bool((item.get("bindings") or {}).get("included")))
        groups.setdefault(key, []).append(item)
    for group in groups.values():
        stores = {i["source_id"] for i in group}
        for item in group:
            others = [o for o in group if o["source_id"] != item["source_id"]]
            if len(stores) < 2 or not others:
                item["also_at"] = []
                continue
            item["also_at"] = sorted(({"id": o["id"], "source": o["source"], "price": o["price"], "url": o["url"]} for o in others), key=lambda o: o["price"])[:4]
            item["cheapest_in_group"] = item["price"] <= min(o["price"] for o in group)


def gone_items(history: dict[str, Any], moment: datetime, prefs: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    saved = set(prefs.get("saved") or [])
    for offer_id, record in history.get("offers", {}).items():
        gone = parse(record.get("gone"))
        if not gone or moment - gone > timedelta(days=7):
            continue
        out.append({"id": offer_id, "title": record.get("title"), "source": record.get("source"), "url": record.get("url"),
                    "image": record.get("image"), "kind": record.get("kind"), "gone_at": record.get("gone"),
                    "last_seen": record.get("last"), "saved": offer_id in saved})
    out.sort(key=lambda r: r["gone_at"] or "", reverse=True)
    return out[:150]


def source_health(reports: list[dict[str, Any]], history: dict[str, Any]) -> list[dict[str, Any]]:
    runs = history.get("runs", [])[-20:]
    out = []
    for report in reports:
        statuses = [r["sources"].get(report["source_id"]) for r in runs if report["source_id"] in r.get("sources", {})]
        good = sum(1 for s in statuses if s == "ok")
        last_ok = next((r["at"] for r in reversed(runs) if r.get("sources", {}).get(report["source_id"]) == "ok"), None)
        out.append(dict(report, success_rate=round(good / len(statuses), 2) if statuses else None, runs=len(statuses), last_ok=last_ok))
    return out


def market_snapshot(dataset: dict[str, Any]) -> dict[str, Any]:
    """Small numbers worth keeping run over run, for trend lines in the brief."""
    skis = [i for i in dataset["items"] if i["kind"] == "ski"]
    claimed = [i["claimed_pct"] for i in skis if i.get("claimed_pct")]
    under = [i["vs_fmv_pct"] for i in skis if i.get("vs_fmv_pct") is not None]
    return {
        "at": dataset["generated_at"],
        "skis": len(skis),
        "median_claimed_pct": round(statistics.median(claimed), 1) if claimed else None,
        "median_vs_fmv_pct": round(statistics.median(under), 1) if under else None,
        "strong_or_better": sum(1 for i in skis if i["band"] in ("strong", "exceptional")),
    }
