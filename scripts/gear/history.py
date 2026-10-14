"""Compact price history: one record per listing size, storing only price changes.

A listing is marked gone only when its source was read completely in the same
run. A failed or partial source never makes its listings disappear.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

RETENTION_DAYS = 120
WINDOW_DAYS = 90
RUN_LOG = 90


def parse_time(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        moment = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def empty() -> dict[str, Any]:
    return {"schema_version": 3, "updated_at": None, "runs": [], "variants": {}, "offers": {}}


def load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty()
    if not isinstance(payload, dict) or payload.get("schema_version") != 3:
        return empty()
    for key, default in empty().items():
        payload.setdefault(key, default)
    return payload


def save(history: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(history, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def variant_key(offer: dict[str, Any], variant: dict[str, Any]) -> str:
    return f"{offer['id']}|{variant.get('vid') or variant.get('label')}"


def update(history: dict[str, Any], offers: list[dict[str, Any]], reports: list[dict[str, Any]], now: str) -> dict[str, Any]:
    """Record this run. Returns {"new_offers": [...ids], "gone_offers": [...ids]}."""
    complete = {r["source_id"] for r in reports if r["status"] == "ok"}
    attempted = {r["source_id"] for r in reports if r["status"] != "disabled"}
    seen_offers: set[str] = set()
    events = {"new_offers": [], "gone_offers": [], "returned_offers": []}
    for offer in offers:
        seen_offers.add(offer["id"])
        record = history["offers"].get(offer["id"])
        if record is None:
            record = history["offers"][offer["id"]] = {"first": now, "source_id": offer["source_id"]}
            events["new_offers"].append(offer["id"])
        elif record.get("gone"):
            events["returned_offers"].append(offer["id"])
            record["gone"] = None
        record.update(last=now, title=offer["title"], url=offer["url"], image=offer.get("image"),
                      source=offer["source"], source_id=offer["source_id"], kind=offer.get("kind"))
        for variant in offer["variants"]:
            key = variant_key(offer, variant)
            entry = history["variants"].setdefault(key, {"o": offer["id"], "first": now, "seen": 0, "p": []})
            entry["last"] = now
            entry["seen"] = int(entry.get("seen", 0)) + 1
            entry["avail"] = variant.get("available")
            entry["gone"] = None
            if offer.get("price_scope") == "exact" and (not entry["p"] or entry["p"][-1][1] != variant["price"]):
                entry["p"].append([now, variant["price"]])
    for offer_id, record in history["offers"].items():
        if offer_id in seen_offers or record.get("gone"):
            continue
        # Only a complete read of the same source proves a listing is gone.
        if record.get("source_id") in complete:
            record["gone"] = now
            events["gone_offers"].append(offer_id)
        elif record.get("source_id") not in attempted:
            continue
    cutoff = parse_time(now) - timedelta(days=RETENTION_DAYS)
    history["variants"] = {k: v for k, v in history["variants"].items() if (parse_time(v.get("last")) or cutoff) > cutoff}
    live_offers = {v["o"] for v in history["variants"].values()}
    history["offers"] = {k: v for k, v in history["offers"].items() if k in live_offers or (parse_time(v.get("last")) or cutoff) > cutoff}
    history["runs"] = (history.get("runs", []) + [{"at": now, "sources": {r["source_id"]: r["status"] for r in reports}}])[-RUN_LOG:]
    history["updated_at"] = now
    return events


def variant_stats(entry: dict[str, Any] | None, current: float, now: str) -> dict[str, Any]:
    """Observed facts for one listing size. Nothing here is estimated."""
    if not entry:
        return {"first_seen": None, "observations": 0, "previous_price": None, "change": None, "change_pct": None,
                "changed_at": None, "low_90": None, "high_90": None, "history_days": 0, "series": []}
    points = [(parse_time(at), float(price)) for at, price in entry.get("p", []) if parse_time(at)]
    moment = parse_time(now) or datetime.now(timezone.utc)
    window_start = moment - timedelta(days=WINDOW_DAYS)
    in_window = [price for at, price in points if at >= window_start]
    earlier = [price for at, price in points if at < window_start]
    if earlier:
        in_window.append(earlier[-1])  # the price in effect when the window opened
    previous = points[-2][1] if len(points) >= 2 else None
    changed_at = points[-1][0].isoformat() if len(points) >= 2 else None
    change = round(current - previous, 2) if previous is not None else None
    first = parse_time(entry.get("first"))
    return {
        "first_seen": entry.get("first"),
        "observations": int(entry.get("seen", 0)),
        "previous_price": previous,
        "change": change,
        "change_pct": round(change / previous * 100, 1) if change is not None and previous else None,
        "changed_at": changed_at,
        "low_90": min(in_window) if in_window else None,
        "high_90": max(in_window) if in_window else None,
        "history_days": max(0, (moment - first).days) if first else 0,
        "series": [[at.isoformat()[:16], price] for at, price in points if at >= window_start][-40:],
    }


def migrate_legacy(history: dict[str, Any], legacy_path: Path, offers: list[dict[str, Any]]) -> int:
    """Carry verified v2 observations into the new history when a listing can be matched exactly."""
    try:
        legacy = json.loads(legacy_path.read_text(encoding="utf-8")).get("items", {})
    except (OSError, ValueError, AttributeError):
        return 0
    by_url: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for key, item in legacy.items():
        if key.startswith("v2|") and isinstance(item, dict):
            url = str(item.get("url", "")).split("?")[0].rstrip("/").lower()
            by_url.setdefault(url, []).append((key, item))
    migrated = 0
    for offer in offers:
        url = offer["url"].split("?")[0].rstrip("/").lower()
        candidates = by_url.get(url)
        if not candidates:
            continue
        for variant in offer["variants"]:
            key = variant_key(offer, variant)
            entry = history["variants"].get(key)
            if entry and entry.get("migrated"):
                continue
            match = None
            for legacy_key, item in candidates:
                tail = legacy_key.rsplit("|", 1)[-1]
                label = str(variant.get("label", "")).replace(" ", "").lower()
                if (variant.get("vid") and tail == str(variant["vid"]).lower()) or (label and tail.replace(" ", "") == label):
                    match = item
                    break
            if match is None and len(candidates) == 1 and len(offer["variants"]) == 1:
                match = candidates[0][1]
            if match is None:
                continue
            observations = sorted((o for o in match.get("observations", []) if o.get("verified")), key=lambda o: o.get("seen_at") or o.get("date"))
            points: list[list[Any]] = []
            for observation in observations:
                at = parse_time(observation.get("seen_at") or observation.get("date"))
                if at and (not points or points[-1][1] != observation["price"]):
                    points.append([at.astimezone(timezone.utc).isoformat(timespec="seconds"), observation["price"]])
            if not points:
                continue
            entry = history["variants"].setdefault(key, {"o": offer["id"], "seen": 0, "p": []})
            entry["p"] = points + [p for p in entry.get("p", []) if p[0] > points[-1][0] and p[1] != points[-1][1]]
            entry["first"] = points[0][0]
            entry["seen"] = int(entry.get("seen", 0)) + len(observations)
            entry["migrated"] = True
            record = history["offers"].setdefault(offer["id"], {"source_id": offer["source_id"]})
            if not record.get("first") or record["first"] > points[0][0]:
                record["first"] = points[0][0]
            migrated += 1
    return migrated
