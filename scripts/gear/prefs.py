"""Household preference model (schema 3) with migration from the v2 file."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

ALL_CONDITIONS = ["new", "blem", "new_with_tags", "demo", "excellent", "good", "fair", "used"]

DEFAULT_PROFILE_SKI = {
    "lengths": {"ideal": [168, 172], "ok": [166, 174], "never_at_or_above": 178},
    "waist_mm": {"min": None, "max": None},
    "genders": ["mens", "unisex", None],
    "style": "playful",
    "ability": "advanced",
    "resort_only": True,
    "categories_avoid": [],
    "categories_owned": [],
    "quiver": [],
    "budget": 500,
    "conditions": list(ALL_CONDITIONS),
    "bindings": "any",
}


def defaults() -> dict[str, Any]:
    return {
        "schema_version": 3,
        "profiles": [
            {"id": "me", "name": "Me", "ski": copy.deepcopy(DEFAULT_PROFILE_SKI),
             "clothing": {"sizes": ["S", "M"], "genders": ["mens", "unisex", None], "budget": 100, "conditions": list(ALL_CONDITIONS)}},
        ],
        "watch_terms": [],
        "muted_terms": [],
        "saved": [],
        "dismissed": [],
        "owned_listings": [],
        "targets": {},
        "alerts": {"price_drop_pct": 10},
        "freshness": {"act_now_hours": 30, "hide_cached_after_hours": 72},
    }


def _range(sizes: list[int]) -> list[int] | None:
    numbers = sorted(int(s) for s in sizes if isinstance(s, (int, float)) or str(s).isdigit())
    return [numbers[0], numbers[-1]] if numbers else None


def migrate(raw: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a v2 file without dropping any of its settings."""
    if raw.get("schema_version") == 3:
        merged = defaults()
        merged.update({k: v for k, v in raw.items() if k != "profiles"})
        merged["profiles"] = [normalize_profile(p) for p in raw.get("profiles", [])] or merged["profiles"]
        return merged
    result = defaults()
    me = result["profiles"][0]
    mine = _range(raw.get("my_ski_sizes") or raw.get("ski_sizes") or [])
    if mine:
        me["ski"]["lengths"] = {"ideal": mine, "ok": [mine[0] - 2, mine[1] + 2], "never_at_or_above": mine[1] + 6}
    budgets = raw.get("max_prices") or {}
    if budgets.get("ski"):
        me["ski"]["budget"] = budgets["ski"]
    if raw.get("clothing_sizes"):
        me["clothing"]["sizes"] = [str(s).upper() for s in raw["clothing_sizes"]]
    if budgets.get("clothing"):
        me["clothing"]["budget"] = budgets["clothing"]
    family = _range(raw.get("family_ski_sizes") or [])
    if family:
        ski = copy.deepcopy(DEFAULT_PROFILE_SKI)
        ski.update(lengths={"ideal": family, "ok": [family[0] - 2, family[1] + 2], "never_at_or_above": family[1] + 8},
                   genders=["mens", "womens", "unisex", None], style=None, ability=None, budget=budgets.get("ski", 500))
        result["profiles"].append({"id": "family", "name": "Family", "ski": ski, "clothing": None})
    for key in ("watch_terms", "muted_terms", "freshness"):
        if raw.get(key):
            result[key] = raw[key]
    result["dismissed"] = list(raw.get("muted_urls", []))
    result["saved"] = list(raw.get("watch_urls", []))
    result["owned_listings"] = list(raw.get("owned_urls", []))
    if raw.get("owned_terms"):
        result["owned_terms"] = raw["owned_terms"]
    return result


def normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(profile)
    if out.get("ski") is not None:
        ski = copy.deepcopy(DEFAULT_PROFILE_SKI)
        ski.update(out.get("ski") or {})
        out["ski"] = ski
    return out


def load(path: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaults()
    return migrate(raw if isinstance(raw, dict) else {})


def validate(prefs: dict[str, Any]) -> list[str]:
    """Problems that would make recommendations wrong. Empty means usable."""
    problems = []
    ids = [p.get("id") for p in prefs.get("profiles", [])]
    if not ids or len(set(ids)) != len(ids):
        problems.append("Profiles need unique ids")
    for profile in prefs.get("profiles", []):
        ski = profile.get("ski")
        if ski:
            lengths = ski.get("lengths", {})
            ideal, ok = lengths.get("ideal"), lengths.get("ok")
            if not (isinstance(ideal, list) and len(ideal) == 2 and isinstance(ok, list) and len(ok) == 2):
                problems.append(f"{profile.get('id')}: lengths need ideal and ok ranges")
            elif not (ok[0] <= ideal[0] <= ideal[1] <= ok[1]):
                problems.append(f"{profile.get('id')}: the ideal length range must sit inside the ok range")
            if not isinstance(ski.get("budget"), (int, float)) or ski["budget"] <= 0:
                problems.append(f"{profile.get('id')}: ski budget must be positive")
    return problems
