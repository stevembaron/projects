"""Deal valuation: how good is the price, on what evidence, and how sure are we.

All numbers come from observed listings: retailer list prices, other retailers'
current prices for the same product, and our own price history. The only
modelled inputs are the documented market heuristics below (typical discount
by model age, value retained by condition). The engine never fabricates an
original price; when the evidence is thin it says so and lowers confidence.
"""
from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any

# Typical discount from list price for NEW stock, by seasons since the model year.
# Fall and early winter: current models rarely move; last season's are commonly 30-40% off.
AGE_DISCOUNT = {0: 0.08, 1: 0.35, 2: 0.45, 3: 0.52}
AGE_DISCOUNT_OLDER = 0.58
SPRING_EXTRA = {0: 0.14, 1: 0.06}
# Share of the equivalent new price a buyer should expect to pay, by condition.
CONDITION_VALUE = {
    "new": 1.0, "blem": 0.88, "new_with_tags": 0.85, "demo": 0.70, "excellent": 0.66,
    "good": 0.52, "fair": 0.38, "used": 0.52,
}
# Used apparel resells for less of its original price than skis do.
CLOTHING_VALUE = {"new": 0.80, "new_with_tags": 0.65, "blem": 0.65, "excellent": 0.50, "good": 0.38, "fair": 0.25, "used": 0.38, "demo": 0.5}
CONDITION_POINTS = {"new": 10, "blem": 8, "new_with_tags": 8, "demo": 6, "excellent": 6, "good": 3, "fair": 1, "used": 3}
TIER_POINTS = {"A": 15, "B": 10, "C": 3}
BANDS = ((78, "exceptional"), (64, "strong"), (48, "interesting"), (0, "ordinary"))


def current_model_year(now: datetime) -> int:
    """Skis for the 2026/27 season are model year 2027 and arrive from late summer."""
    return now.year + 1 if now.month >= 7 else now.year


def typical_new_discount(age: int, now: datetime) -> float:
    base = AGE_DISCOUNT.get(age, AGE_DISCOUNT_OLDER) if age >= 0 else 0.0
    if 3 <= now.month <= 6:
        base += SPRING_EXTRA.get(age, 0.0)
    return min(base, 0.7)


def comp_key(offer: dict[str, Any]) -> tuple:
    """Same product for price comparison: brand, model, width, gender, package, year."""
    gender = "w" if offer.get("gender") == "womens" else "u"
    model = offer.get("model_key") or ""
    if gender == "w" and model.endswith(" w"):
        model = model[:-2]
    package = "sys" if (offer.get("bindings") or {}).get("included") else "flat"
    return (offer.get("kind"), offer.get("brand"), model, gender, package, offer.get("model_year"))


def best_variant(offer: dict[str, Any]) -> dict[str, Any]:
    pool = [v for v in offer["variants"] if v.get("available") is not False] or offer["variants"]
    return min(pool, key=lambda v: v["price"])


def build_market(offers: list[dict[str, Any]]) -> dict[tuple, dict[str, Any]]:
    """Evidence per product: list-price claims and current street prices across stores."""
    market: dict[tuple, dict[str, Any]] = {}
    for offer in offers:
        if not offer.get("brand") or not offer.get("model_key"):
            continue
        entry = market.setdefault(comp_key(offer), {"claims": {}, "new_prices": {}, "used_prices": []})
        for variant in offer["variants"]:
            if variant.get("compare_at") and offer.get("price_scope") == "exact":
                entry["claims"].setdefault(offer["source_id"], set()).add(variant["compare_at"])
        if offer.get("price_scope") != "exact":
            continue
        available = [v["price"] for v in offer["variants"] if v.get("available") is not False]
        if not available:
            continue
        if offer.get("condition") in ("new", "blem", None):
            current = market[comp_key(offer)]["new_prices"]
            current[offer["source_id"]] = min(min(available), current.get(offer["source_id"], float("inf")))
        elif offer.get("condition") in ("demo", "excellent", "good", "fair", "used", "new_with_tags"):
            entry["used_prices"].append((offer["condition"], min(available), offer["source_id"]))
    return market


def list_price_evidence(entry: dict[str, Any] | None, own_claim: float | None) -> tuple[float | None, str, int]:
    """(list price, basis, number of stores agreeing). Agreement within 4% counts as corroboration."""
    claims: list[tuple[str, float]] = []
    for source, values in (entry or {}).get("claims", {}).items():
        claims.append((source, max(values)))
    if own_claim and not claims:
        return own_claim, "this retailer's list price", 1
    if not claims:
        return None, "no list price published", 0
    values = sorted(v for _, v in claims)
    best: tuple[int, float] = (0, values[-1])
    for anchor in values:
        agreeing = [v for v in values if abs(v - anchor) / anchor <= 0.04]
        if len(agreeing) > best[0] or (len(agreeing) == best[0] and statistics.median(agreeing) > best[1]):
            best = (len(agreeing), statistics.median(agreeing))
    stores = best[0]
    if stores >= 2:
        return round(best[1], 2), f"list price confirmed by {stores} stores", stores
    claim = own_claim or values[-1]
    return claim, "one store's list price", 1


def value_offer(offer: dict[str, Any], market: dict[tuple, dict[str, Any]], stats: dict[str, Any], now: datetime,
                profile_facts: dict[str, Any] | None = None) -> dict[str, Any]:
    """Score one offer. Uses the cheapest available size; fit picks sizes later."""
    variant = best_variant(offer)
    price = variant["price"]
    condition = offer.get("condition") or "unknown"
    entry = market.get(comp_key(offer))
    evidence: list[str] = []
    flags: list[str] = []

    list_price, list_basis, list_stores = list_price_evidence(entry, variant.get("compare_at"))
    age = None
    age_assumed = False
    if offer.get("model_year"):
        age = max(0, current_model_year(now) - int(offer["model_year"]))
    elif offer.get("kind") in ("ski", "binding") and list_price:
        # No year listed: assume last season's model, which lowers the estimate rather than flattering the deal.
        age, age_assumed = 1, True

    street_new = sorted((entry or {}).get("new_prices", {}).values())
    other_street = [p for s, p in (entry or {}).get("new_prices", {}).items() if s != offer["source_id"]]
    expected_new = None
    basis_parts = []
    if offer.get("kind") == "clothing":
        if list_price:
            expected_new = list_price
            basis_parts.append(f"{list_basis} as the original price")
    elif list_price and age is not None:
        expected_new = list_price * (1 - typical_new_discount(age, now))
        if age_assumed:
            basis_parts.append(f"{list_basis}; year not listed, so priced as last season's model (typical {round(typical_new_discount(age, now) * 100)}% off)")
        else:
            basis_parts.append(f"{list_basis}, typical {round(typical_new_discount(age, now) * 100)}% off for a {age}-season-old model" if age else f"{list_basis}, current model")
    if len(other_street) >= 2:
        street = statistics.median(other_street)
        expected_new = street if expected_new is None else (expected_new + street) / 2
        basis_parts.append(f"new at {len(other_street)} other stores (median ${street:,.0f})")
    elif len(other_street) == 1 and expected_new is not None:
        expected_new = (expected_new * 2 + other_street[0]) / 3
        basis_parts.append(f"one other store at ${other_street[0]:,.0f}")

    fmv = None
    retained = CLOTHING_VALUE if offer.get("kind") == "clothing" else CONDITION_VALUE
    if expected_new is not None and condition in retained:
        fmv = expected_new * retained[condition]
        used_comps = [p for c, p, s in (entry or {}).get("used_prices", []) if c == condition and s != offer["source_id"]]
        if len(used_comps) >= 2:
            fmv = (fmv + statistics.median(used_comps)) / 2
            basis_parts.append(f"{len(used_comps)} similar {condition.replace('_', ' ')} listings")
        fmv = round(fmv, 2)

    confidence_points = 0
    if list_stores >= 2:
        confidence_points += 2
    elif list_stores == 1:
        confidence_points += 1
    if len(other_street) >= 2:
        confidence_points += 2
    if age is not None and not age_assumed:
        confidence_points += 1
    if offer.get("price_scope") == "exact":
        confidence_points += 1
    else:
        flags.append("Price is a starting price; your size may cost more")
    if variant.get("available") is not True:
        flags.append("Stock not confirmed" if variant.get("available") is None else "Sold out")
    if offer.get("model_year") is None:
        flags.append("Model year not listed")
    if condition == "unknown":
        flags.append("Condition not stated")
    confidence = "high" if confidence_points >= 5 and fmv else ("medium" if confidence_points >= 3 and fmv else "low")

    shipping = (offer.get("shipping") or {}).get("cost")
    cost = price + (shipping or 0)
    claimed_pct = round((1 - price / variant["compare_at"]) * 100, 1) if variant.get("compare_at") else None
    vs_fmv = round(fmv - cost, 2) if fmv else None
    vs_fmv_pct = round((fmv - cost) / fmv * 100, 1) if fmv else None

    points: dict[str, float] = {}
    if fmv:
        points["value"] = max(0.0, min(1.0, (fmv - cost) / fmv / 0.35)) * 45
        points["savings"] = max(0.0, min(1.0, (fmv - cost) / 250)) * 10
    elif claimed_pct:
        points["value"] = max(0.0, min(1.0, claimed_pct / 60)) * 20
        points["savings"] = 0.0
    else:
        points["value"] = 0.0
        points["savings"] = 0.0

    drop = 0.0
    if stats.get("change") is not None and stats["change"] < 0 and stats.get("previous_price"):
        pct = -stats["change"] / stats["previous_price"]
        if pct >= 0.10 or -stats["change"] >= 40:
            drop += 10
            evidence.append(f"Price cut ${-stats['change']:,.0f} ({pct * 100:.0f}%) since we last saw it at ${stats['previous_price']:,.0f}")
        elif pct > 0:
            drop += 4
            evidence.append(f"Small price cut of ${-stats['change']:,.0f}")
    if stats.get("observations", 0) >= 3 and stats.get("low_90") is not None and stats.get("high_90", 0) > stats["low_90"] and price <= stats["low_90"]:
        drop += 5
        evidence.append(f"Lowest price in {stats.get('history_days', 0)} days of tracking")
    points["drop"] = min(drop, 15)

    tier = (profile_facts or {}).get("tier")
    points["quality"] = TIER_POINTS.get(tier, 7) if offer.get("kind") == "ski" else 8
    condition_points = CONDITION_POINTS.get(condition, 2)
    if condition == "new" and age is not None:
        condition_points = 10 if age == 0 else (8 if age == 1 else max(3, 9 - 2 * age))
    elif age is not None and age >= 4:
        condition_points = max(0, condition_points - (age - 3))
    points["condition"] = condition_points
    points["seller"] = float((offer.get("seller") or {}).get("trust", 0.75)) * 5

    penalty = 0.0
    if offer.get("price_scope") != "exact":
        penalty += 10
    if variant.get("available") is None:
        penalty += 4
    if claimed_pct is not None and vs_fmv_pct is not None and claimed_pct - max(vs_fmv_pct, 0) >= 30 and claimed_pct >= 40:
        penalty += 5
        flags.append(f"The {claimed_pct:.0f}% off headline mostly reflects the model's age, not an unusual price")
    if fmv and cost > fmv * 1.05:
        flags.append("Priced above what this model typically sells for in this condition")

    score = round(max(0.0, min(100.0, sum(points.values()) - penalty)))
    band = next(name for floor, name in BANDS if score >= floor)
    if confidence == "low" and band == "exceptional":
        band = "strong"

    if fmv and vs_fmv and vs_fmv > 0:
        evidence.insert(0, f"About ${vs_fmv:,.0f} ({vs_fmv_pct:.0f}%) under an estimated fair price of ${fmv:,.0f}")
    elif fmv:
        evidence.insert(0, f"Estimated fair price ${fmv:,.0f}; this listing is not below it")
    if list_price and list_stores >= 2:
        evidence.append(f"List price ${list_price:,.0f} is confirmed by {list_stores} stores")
    if len(street_new) >= 2:
        evidence.append(f"New elsewhere from ${min(street_new):,.0f}")
    if shipping:
        evidence.append(f"Includes ${shipping:,.0f} shipping")
    return {
        "score": score,
        "band": band,
        "confidence": confidence,
        "price": price,
        "cost": round(cost, 2),
        "shipping": shipping,
        "list_price": list_price,
        "list_basis": list_basis,
        "claimed_pct": claimed_pct,
        "fmv": fmv,
        "fmv_basis": "; ".join(basis_parts) or None,
        "vs_fmv": vs_fmv,
        "vs_fmv_pct": vs_fmv_pct,
        "street_low": min(street_new) if street_new else None,
        "stores_with_product": len((entry or {}).get("new_prices", {})),
        "age_seasons": age,
        "points": {k: round(v, 1) for k, v in points.items()},
        "penalty": penalty,
        "evidence": evidence[:5],
        "flags": flags[:4],
    }


def price_for_score(offer: dict[str, Any], market: dict[tuple, dict[str, Any]], stats: dict[str, Any], now: datetime,
                    facts: dict[str, Any] | None, target: int = 64) -> float | None:
    """Highest price at which this listing would reach `target`, everything else unchanged."""
    variant = best_variant(offer)

    def score_at(price: float) -> int:
        repriced = dict(offer, variants=[dict(v, price=price) if v is variant else v for v in offer["variants"]])
        return value_offer(repriced, market, stats, now, facts)["score"]

    high = variant["price"]
    low = round(high * 0.3, 2)
    if score_at(high) >= target or score_at(low) < target:
        return None
    for _ in range(18):
        middle = (low + high) / 2
        if score_at(middle) >= target:
            low = middle
        else:
            high = middle
    step = 5 if low >= 50 else 1
    return float(int(low // step) * step)
