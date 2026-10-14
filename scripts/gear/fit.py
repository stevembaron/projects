"""Personal fit and the final verdict.

assets/fit.js implements the same rules for in-browser preference edits;
tests/test_fit_parity.py checks both against shared vectors. Change them together.
"""
from __future__ import annotations

from typing import Any

CATEGORY_NOUN = {
    "carving": "carver", "frontside": "frontside ski", "all_mountain": "all-mountain ski",
    "all_mountain_wide": "wide all-mountain ski", "freeride": "freeride ski", "powder": "powder ski",
    "park": "park ski", "touring": "touring ski",
}
VERDICTS = ("buy_now", "strong", "watch", "pass")


def _fmt_len(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def _text(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(k) or "") for k in ("title", "source", "url")).lower()


def ski_fit(item: dict[str, Any], prefs: dict[str, Any], global_prefs: dict[str, Any]) -> dict[str, Any]:
    pros: list[str] = []
    cons: list[str] = []
    hard: list[str] = []
    score = 50
    genders = prefs.get("genders")
    if genders and item.get("gender") not in genders:
        hard.append("Women's-specific model" if item.get("gender") == "womens" else "Not cut for this profile")

    lengths = prefs.get("lengths") or {}
    ideal, ok = lengths.get("ideal") or [0, 999], lengths.get("ok") or [0, 999]
    never = lengths.get("never_at_or_above")
    variants = [v for v in item.get("variants", []) if v.get("available") is not False]
    sized = [v for v in variants if v.get("length_cm")]
    in_ok = [v for v in sized if ok[0] <= v["length_cm"] <= ok[1] and (never is None or v["length_cm"] < never)]
    in_ideal = [v for v in in_ok if ideal[0] <= v["length_cm"] <= ideal[1]]
    chosen = None
    if in_ideal:
        chosen = min(in_ideal, key=lambda v: v["price"])
        score += 25
        pros.append(f"{_fmt_len(chosen['length_cm'])} cm is in your {ideal[0]}–{ideal[1]} cm range")
    elif in_ok:
        middle = (ideal[0] + ideal[1]) / 2
        chosen = min(in_ok, key=lambda v: (abs(v["length_cm"] - middle), v["price"]))
        score += 12
        side = "short" if chosen["length_cm"] < ideal[0] else "long"
        cons.append(f"{_fmt_len(chosen['length_cm'])} cm is a touch {side} of your {ideal[0]}–{ideal[1]} cm range")
    elif sized:
        available = ", ".join(_fmt_len(v["length_cm"]) for v in sorted(sized, key=lambda v: v["length_cm"])[:6])
        hard.append(f"No length between {ok[0]} and {ok[1]} cm (has {available})")
    elif variants:
        chosen = min(variants, key=lambda v: v["price"])
        cons.append("Lengths not listed; check your size before buying")
    else:
        hard.append("Sold out")

    price = chosen["price"] if chosen else item.get("price")
    budget = prefs.get("budget")
    if budget and price and price > budget:
        hard.append(f"Over your ${budget:,.0f} budget")

    playful, demanding = item.get("playful"), item.get("demanding")
    if prefs.get("style") == "playful":
        if playful is None:
            score -= 5
            cons.append("How it skis is unknown for this model")
        elif playful >= 4:
            score += 15
            pros.append("Playful and easy to pivot or slarve")
        elif playful == 3:
            score += 5
        else:
            score -= 22
            cons.append("Prefers to be carved; less forgiving of slarved turns")
        if demanding is not None and demanding >= 4:
            score -= 12
            cons.append("Demanding: wants speed and precise technique")
        elif demanding is not None and demanding <= 2:
            score += 4
            pros.append("Forgiving")

    category = item.get("category")
    if category and category in (prefs.get("categories_avoid") or []):
        score -= 15
        cons.append(f"A {CATEGORY_NOUN.get(category, category)}, which you avoid")
    if category == "touring" and prefs.get("resort_only"):
        score -= 12
        cons.append("Built light for touring; less damp on resort snow")
    level = item.get("level") or []
    if prefs.get("ability") in ("advanced", "expert") and len(level) == 2 and level[1] in ("beginner", "intermediate"):
        hard.append("Entry-level ski, below your ability")

    duplicate = None
    for owned in prefs.get("quiver") or []:
        same_family = owned.get("model_key") and owned.get("brand") == item.get("brand") and str(item.get("model_key") or "").startswith(owned["model_key"])
        similar = owned.get("category") == category and owned.get("waist_mm") and item.get("waist_mm") and abs(owned["waist_mm"] - item["waist_mm"]) <= 5
        if same_family or similar:
            duplicate = owned.get("name")
            score -= 20
            cons.append(f"Close to your {owned.get('name')}")
            break
    if not duplicate and category and category in (prefs.get("categories_owned") or []):
        score -= 6
        cons.append(f"You already own a {CATEGORY_NOUN.get(category, category)}")

    conditions = prefs.get("conditions")
    if conditions and item.get("condition") and item["condition"] not in conditions:
        hard.append("Condition is outside your preferences")
    binding = item.get("bindings") or {}
    if prefs.get("bindings") == "flat" and binding.get("included"):
        cons.append("Comes with bindings you may not want")
    elif prefs.get("bindings") == "included" and binding.get("included") is False:
        score -= 6
        cons.append("Bindings not included")
    if binding.get("included") and binding.get("demo"):
        pros.append("Includes adjustable demo bindings")
    learned = global_prefs.get("learned") or {}
    brand_passes = (learned.get("brands") or {}).get(item.get("brand") or "", 0)
    category_passes = (learned.get("categories") or {}).get(category or "", 0)
    if brand_passes >= 2:
        score -= 6
        cons.append(f"You've passed on {brand_passes} {item.get('brand')} skis")
    if category_passes >= 3:
        score -= 6
        cons.append(f"You've passed on {category_passes} {CATEGORY_NOUN.get(category, category)}s")
    text = _text(item)
    if any(term.lower() in text for term in global_prefs.get("watch_terms") or []):
        score += 8
        pros.append("Matches your watch list")
    return {"score": max(0, min(100, score)), "hard": hard, "pros": pros[:4], "cons": cons[:4],
            "variant": chosen.get("label") if chosen else None, "price": price, "duplicate": duplicate}


def learn(items: list[dict[str, Any]], global_prefs: dict[str, Any]) -> dict[str, Any]:
    """Count dismissed skis by brand and type, so similar listings rank lower."""
    dismissed = set(global_prefs.get("dismissed") or [])
    brands: dict[str, int] = {}
    categories: dict[str, int] = {}
    for item in items:
        if item.get("kind") != "ski" or (item.get("id") not in dismissed and item.get("url") not in dismissed):
            continue
        if item.get("brand"):
            brands[item["brand"]] = brands.get(item["brand"], 0) + 1
        if item.get("category"):
            categories[item["category"]] = categories.get(item["category"], 0) + 1
    return {"brands": brands, "categories": categories}


def clothing_fit(item: dict[str, Any], prefs: dict[str, Any] | None, global_prefs: dict[str, Any]) -> dict[str, Any]:
    if not prefs:
        return {"score": 0, "hard": ["No clothing preferences for this profile"], "pros": [], "cons": [], "variant": None, "price": item.get("price"), "duplicate": None}
    pros: list[str] = []
    cons: list[str] = []
    hard: list[str] = []
    score = 50
    genders = prefs.get("genders")
    if genders and item.get("gender") not in genders:
        hard.append("Not cut for this profile")
    sizes = [str(s).upper() for s in prefs.get("sizes") or []]
    variants = [v for v in item.get("variants", []) if v.get("available") is not False]
    matching = [v for v in variants if str(v.get("size") or "").upper() in sizes]
    chosen = min(matching, key=lambda v: v["price"]) if matching else None
    if chosen:
        score += 30
        pros.append(f"Your size ({chosen['size']})")
    elif variants:
        listed = ", ".join(sorted({str(v.get('size') or v.get('label')) for v in variants}))[:40]
        hard.append(f"Not in your size (listed: {listed})")
    else:
        hard.append("Sold out")
    price = chosen["price"] if chosen else item.get("price")
    if prefs.get("budget") and price and price > prefs["budget"]:
        hard.append(f"Over your ${prefs['budget']:,.0f} budget")
    if item.get("condition") == "fair":
        score -= 10
        cons.append("Fair condition: visible wear")
    elif item.get("condition") in ("new", "new_with_tags"):
        score += 8
        pros.append("Unworn")
    conditions = prefs.get("conditions")
    if conditions and item.get("condition") and item["condition"] not in conditions:
        hard.append("Condition is outside your preferences")
    text = _text(item)
    if any(term.lower() in text for term in global_prefs.get("watch_terms") or []):
        score += 10
        pros.append("Matches your watch list")
    return {"score": max(0, min(100, score)), "hard": hard, "pros": pros[:4], "cons": cons[:4],
            "variant": chosen.get("label") if chosen else None, "price": price, "duplicate": None}


def evaluate(item: dict[str, Any], profile: dict[str, Any], global_prefs: dict[str, Any]) -> dict[str, Any]:
    text = _text(item)
    hidden = None
    if item.get("id") in (global_prefs.get("dismissed") or []) or item.get("url") in (global_prefs.get("dismissed") or []):
        hidden = "dismissed"
    elif item.get("id") in (global_prefs.get("owned_listings") or []) or item.get("url") in (global_prefs.get("owned_listings") or []):
        hidden = "owned"
    elif any(term.lower() in text for term in global_prefs.get("muted_terms") or []):
        hidden = "muted"
    if item.get("kind") == "ski":
        result = ski_fit(item, profile.get("ski") or {}, global_prefs) if profile.get("ski") else {"score": 0, "hard": ["No ski preferences for this profile"], "pros": [], "cons": [], "variant": None, "price": item.get("price"), "duplicate": None}
    elif item.get("kind") == "clothing":
        result = clothing_fit(item, profile.get("clothing"), global_prefs)
    else:
        budget = (profile.get("ski") or {}).get("budget")
        hard = [f"Over your ${budget:,.0f} budget"] if budget and item.get("price", 0) > budget else []
        result = {"score": 50, "hard": hard, "pros": [], "cons": [], "variant": None, "price": item.get("price"), "duplicate": None}
    result["hidden"] = hidden
    return result


def verdict(item: dict[str, Any], fit: dict[str, Any], target: float | None = None) -> tuple[str, str]:
    """BUY NOW / STRONG DEAL / WORTH WATCHING / PASS with the main reason."""
    if fit.get("hidden"):
        return "pass", {"dismissed": "You dismissed this", "owned": "You own this", "muted": "Matches a muted term"}[fit["hidden"]]
    if fit["hard"]:
        return "pass", fit["hard"][0]
    score, fitness = item.get("score", 0), fit["score"]
    price = fit.get("price") or item.get("price") or 0
    verified = item.get("price_scope") == "exact" and item.get("in_stock") and item.get("fresh")
    duplicate = bool(fit.get("duplicate"))
    if target and price and price <= target:
        return ("buy_now" if verified else "strong"), f"At or under your ${target:,.0f} target"
    if score >= 78 and fitness >= 70 and item.get("confidence") != "low" and verified and (not duplicate or score >= 88):
        return "buy_now", "Exceptional, verified price on a ski that suits you"
    if score >= 64 and fitness >= 60 and (not duplicate or score >= 78):
        return "strong", "Well under fair value and a good fit"
    if (score >= 48 and fitness >= 45) or (fitness >= 70 and score >= 35):
        return "watch", "Good fit; price could still improve" if score < 64 else "Strong price, but overlaps what you own"
    if score < 48:
        return "pass", "Price is not compelling"
    return "pass", "Weak match for how you ski"
