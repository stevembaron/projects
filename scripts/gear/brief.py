"""The daily brief: facts first, then words.

facts() extracts and ranks what happened from the dataset. house_brief() writes
it up deterministically, so the page always has a real brief even when no AI
editorial was submitted. Every number in the prose comes from facts().
"""
from __future__ import annotations

import re
import statistics
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

RANK = {"buy_now": 0, "strong": 1, "watch": 2, "pass": 3}
LABEL = {"buy_now": "Buy now", "strong": "Strong deal", "watch": "Worth watching", "pass": "Pass"}
CATEGORY_WORD = {"ski": "skis", "clothing": "clothing listings", "binding": "bindings"}


def money(value: float | None) -> str:
    if value is None:
        return "?"
    return f"${value:,.0f}" if value >= 20 or float(value).is_integer() else f"${value:,.2f}"


def _parse(value: Any) -> datetime | None:
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def short_title(item: dict[str, Any]) -> str:
    brand, model = item.get("brand"), item.get("model")
    if brand and model:
        name = model if model.lower().startswith(brand.lower()) else f"{brand} {model}"
        if item.get("year"):
            name = f"{item['year']} {name}"
        return name[:60]
    return re.sub(r"\s+(?:skis?\b.*|-\s.*)$", "", item["title"], flags=re.I)[:60] or item["title"][:60]


def compact(item: dict[str, Any], profile: str) -> dict[str, Any]:
    verdict, reason = item["verdict"].get(profile, ["pass", ""])
    fit = item["fit"].get(profile, {})
    return {
        "id": item["id"], "title": item["title"], "short": short_title(item), "source": item["source"],
        "price": fit.get("price") or item["price"], "fmv": item.get("fmv"), "vs_fmv": item.get("vs_fmv"),
        "vs_fmv_pct": item.get("vs_fmv_pct"), "claimed_pct": item.get("claimed_pct"), "list_price": item.get("list_price"),
        "score": item["score"], "confidence": item["confidence"], "verdict": verdict, "reason": reason,
        "size": fit.get("variant"), "condition": item.get("condition_text"), "year": item.get("year"),
        "category": item.get("category"), "playful": item.get("playful"), "pros": fit.get("pros", [])[:2],
        "cons": fit.get("cons", [])[:2], "evidence": item.get("evidence", [])[:2], "flags": item.get("flags", [])[:2],
        "change": item["history"].get("change"), "change_pct": item["history"].get("change_pct"),
        "previous_price": item["history"].get("previous_price"), "low_90": item["history"].get("low_90"),
        "is_new": item.get("is_new"), "strong_at": item.get("strong_at"), "url": item["url"],
    }


def facts(dataset: dict[str, Any], kind: str = "ski", profile: str = "me", market_log: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = [i for i in dataset["items"] if i["kind"] == kind]
    prefs = next((p for p in dataset["preferences"].get("profiles", []) if p["id"] == profile), {})
    usable = [i for i in items if not i["fit"].get(profile, {}).get("hard") and not i["fit"].get(profile, {}).get("hidden")]
    by_verdict: dict[str, list[dict[str, Any]]] = {v: [] for v in RANK}
    for item in items:
        by_verdict[item["verdict"].get(profile, ["pass"])[0]].append(item)
    for bucket in by_verdict.values():
        bucket.sort(key=lambda i: (-i["score"], i["price"]))
    picks = (by_verdict["buy_now"] + by_verdict["strong"] + by_verdict["watch"])[:6]

    new = sorted((i for i in items if i.get("is_new")), key=lambda i: -i["score"])
    week_ago = (_parse(dataset["generated_at"]) or datetime.now(timezone.utc)) - timedelta(days=7)
    drops = sorted((i for i in items if (i["history"].get("change") or 0) < 0 and i["history"].get("previous_price")
                    and (_parse(i["history"].get("changed_at")) or week_ago) > week_ago),
                   key=lambda i: i["history"]["change"] / i["history"]["previous_price"])
    approaching = sorted((i for i in usable if i.get("strong_at") and i["verdict"].get(profile, ["pass"])[0] in ("watch", "pass")),
                         key=lambda i: (i["price"] - i["strong_at"]) / i["price"])[:4]
    not_for_you = [i for i in sorted(items, key=lambda i: -i["score"]) if i["score"] >= 62 and i["fit"].get(profile, {}).get("hard")][:4]
    verify = [i for i in sorted(items, key=lambda i: -i["score"])
              if i["score"] >= 50 and (not i.get("fmv") or i.get("price_scope") != "exact" or not i.get("in_stock"))][:4]

    stores = Counter(i["source"] for i in items)
    strong_by_store = Counter(i["source"] for i in items if i["band"] in ("strong", "exceptional"))
    claimed_by_store = {s: statistics.median([i["claimed_pct"] for i in items if i["source"] == s and i.get("claimed_pct")])
                        for s in stores if any(i.get("claimed_pct") for i in items if i["source"] == s)}
    brand_fit = Counter(i["brand"] for i in usable if i.get("brand"))
    brand_strong = Counter(i["brand"] for i in items if i["band"] in ("strong", "exceptional") and i.get("brand"))
    conditions = Counter(i.get("condition") or "unknown" for i in usable)

    trend = None
    log = [m for m in (market_log or []) if m.get("median_claimed_pct") is not None]
    if kind == "ski" and len(log) >= 2:
        now_m, then_m = log[-1], log[max(0, len(log) - 14)]
        trend = {"since": then_m["at"], "claimed_then": then_m["median_claimed_pct"], "claimed_now": now_m["median_claimed_pct"],
                 "strong_then": then_m.get("strong_or_better"), "strong_now": now_m.get("strong_or_better")}

    gone = [g for g in dataset.get("gone", []) if g.get("kind") == kind]
    coverage = [{"source": s["name"], "status": s["status"], "error": s.get("error"), "notes": s.get("notes")}
                for s in dataset.get("sources", []) if s["status"] not in ("ok", "disabled")]
    ski_prefs = prefs.get("ski") or {}
    return {
        "kind": kind,
        "profile": profile,
        "profile_name": prefs.get("name", profile),
        "generated_at": dataset["generated_at"],
        "lengths": (ski_prefs.get("lengths") or {}).get("ideal"),
        "budget": ski_prefs.get("budget") if kind == "ski" else (prefs.get("clothing") or {}).get("budget"),
        "counts": {
            "listings": len(items), "stores": len(stores), "usable": len(usable),
            "buy_now": len(by_verdict["buy_now"]), "strong": len(by_verdict["strong"]), "watch": len(by_verdict["watch"]),
            "new": len(new), "drops": len(drops), "gone": len(gone),
        },
        "picks": [compact(i, profile) for i in picks],
        "new": [compact(i, profile) for i in new[:5]],
        "drops": [compact(i, profile) for i in drops[:5]],
        "approaching": [compact(i, profile) for i in approaching],
        "not_for_you": [compact(i, profile) for i in not_for_you],
        "verify": [compact(i, profile) for i in verify],
        "stores": [{"source": s, "listings": n, "strong": strong_by_store.get(s, 0), "median_claimed_pct": round(claimed_by_store[s]) if s in claimed_by_store else None}
                   for s, n in sorted(stores.items(), key=lambda kv: (-strong_by_store.get(kv[0], 0), -kv[1]))[:5]],
        "brands_fitting": brand_fit.most_common(4),
        "brands_strong": brand_strong.most_common(4),
        "conditions_fitting": conditions.most_common(),
        "trend": trend,
        "gone_recent": [{"title": g["title"], "source": g["source"], "saved": g.get("saved")} for g in gone[:5]],
        "coverage": coverage,
    }


def _pick_line(p: dict[str, Any]) -> str:
    bits = [f"{p['short']} at {p['source']}, {money(p['price'])}"]
    if p.get("size"):
        bits[0] += f" in {p['size']}"
    if p.get("vs_fmv") and p["vs_fmv"] > 0:
        bits.append(f"about {money(p['vs_fmv'])} under our fair-price estimate")
    elif p.get("claimed_pct"):
        bits.append(f"{p['claimed_pct']:.0f}% off list")
    pros = [x for x in p.get("pros") or [] if " cm " not in x]
    cons = [x for x in p.get("cons") or [] if " cm " not in x]
    if pros:
        bits.append(pros[0][0].lower() + pros[0][1:])
    if cons:
        bits.append("but " + cons[0][0].lower() + cons[0][1:])
    return "; ".join(bits) + "."


def house_brief(f: dict[str, Any]) -> dict[str, Any]:
    c = f["counts"]
    noun = CATEGORY_WORD.get(f["kind"], "listings")
    picks = f["picks"]
    lead = picks[0] if picks else None
    size_phrase = f" in {f['lengths'][0]}–{f['lengths'][1]} cm" if f["kind"] == "ski" and f.get("lengths") else ""
    if c["buy_now"] and lead:
        headline = f"Buy now: {lead['short']}, {money(lead['price'])} at {lead['source']}"
    elif c["strong"] and lead:
        headline = f"{c['strong']} strong deal{'s' if c['strong'] != 1 else ''}{size_phrase}; best is {lead['short']} at {money(lead['price'])}"
    elif c["watch"]:
        headline = f"Nothing to pounce on. {c['watch']} {noun}{size_phrase} worth watching"
    else:
        headline = f"A quiet day for {noun}{size_phrase}"

    dek_parts = [f"We checked {c['listings']:,} discounted {noun} across {c['stores']} stores; {c['usable']} are in your size and budget."]
    if c["buy_now"] == 0 and c["strong"] == 0:
        dek_parts.append("None is cheap enough to call a strong deal yet, so the useful news today is in what moved and what is close.")
    trend = f.get("trend")
    if trend and trend["claimed_then"] is not None:
        delta = trend["claimed_now"] - trend["claimed_then"]
        if abs(delta) >= 2:
            dek_parts.append(f"Typical advertised discounts are {'deeper' if delta > 0 else 'shallower'} than a week ago ({trend['claimed_now']:.0f}% vs {trend['claimed_then']:.0f}%).")
    sections = []
    if picks:
        sections.append({"title": "Best of today" if (c["buy_now"] or c["strong"]) else "Worth watching",
                         "lines": [{"text": _pick_line(p), "ref": p["id"]} for p in picks[:4]], "refs": []})
    moved = []
    for d in f["drops"][:3]:
        moved.append({"text": f"{d['short']} ({d['source']}) dropped {money(-d['change'])} to {money(d['price'])} ({abs(d['change_pct']):.0f}%).", "ref": d["id"]})
    for n in [x for x in f["new"] if x["id"] not in {d["id"] for d in f["drops"]}][:3]:
        moved.append({"text": f"New: {n['short']} at {n['source']}, {money(n['price'])}" + (f", scored {n['score']}" if n["score"] >= 48 else "") + ".", "ref": n["id"]})
    if c["gone"]:
        moved.append({"text": f"{c['gone']} listing{'s' if c['gone'] != 1 else ''} sold or came down this week" + (", including one you saved." if any(g.get("saved") for g in f["gone_recent"]) else "."), "ref": None})
    if moved:
        sections.append({"title": "What moved", "lines": moved, "refs": []})
    if f["approaching"]:
        sections.append({"title": "Close to a buy", "lines": [{
            "text": f"{a['short']} at {a['source']} is {money(a['price'])}" + (f" in {a['size']}" if a.get("size") else "") +
            f"; it becomes a strong deal at about {money(a['strong_at'])} ({(a['price'] - a['strong_at']) / a['price'] * 100:.0f}% lower).", "ref": a["id"]}
            for a in f["approaching"]], "refs": []})
    notes = []
    stores = [s for s in f["stores"] if s["strong"]]
    if stores:
        notes.append("Most strong prices: " + ", ".join(f"{s['source']} ({s['strong']})" for s in stores[:3]) + ".")
    deep = [s for s in f["stores"] if s.get("median_claimed_pct")]
    if deep:
        top = max(deep, key=lambda s: s["median_claimed_pct"])
        notes.append(f"{top['source']} has the deepest typical markdown at {top['median_claimed_pct']}% off list across {top['listings']} listings.")
    if f["brands_fitting"]:
        notes.append("In your size and budget, the most choice is from " + ", ".join(f"{b} ({n})" for b, n in f["brands_fitting"][:3]) + ".")
    used = sum(n for cond, n in f["conditions_fitting"] if cond not in ("new", "unknown"))
    if f["kind"] == "ski" and c["usable"]:
        notes.append(f"{used} of the {c['usable']} fitting skis are demo, resale or blemished stock.")
    if notes:
        sections.append({"title": "Market notes", "lines": [{"text": n, "ref": None} for n in notes], "refs": []})
    if f["not_for_you"]:
        sections.append({"title": "Good deals that aren't for you", "lines": [
            {"text": f"{x['short']} at {x['source']}, {money(x['price'])} (score {x['score']}): {x['reason'][0].lower() + x['reason'][1:]}.", "ref": x["id"]} for x in f["not_for_you"]],
            "refs": []})
    if f["verify"]:
        sections.append({"title": "Check before trusting", "lines": [
            {"text": f"{v['short']} at {v['source']}, {money(v['price'])}: {(v['flags'][0] if v['flags'] else 'not enough evidence for a fair price').rstrip('.')}.", "ref": v["id"]} for v in f["verify"][:3]],
            "refs": []})
    if f["coverage"]:
        sections.append({"title": "Coverage", "lines": [
            {"text": f"{g['source']}: {g['status']}" + (f" ({g['error'][:120]})" if g.get("error") else "") + ".", "ref": None} for g in f["coverage"]], "refs": []})
    return {"kind": f["kind"], "headline": headline, "dek": " ".join(dek_parts), "sections": sections,
            "generated_at": f["generated_at"], "author": "house"}
