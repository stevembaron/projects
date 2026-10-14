"""What a ski is for and how it skis: curated families first, then cautious inference."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parent / "data" / "ski_catalog.json"
CATEGORY_LABELS = {
    "carving": "Carver",
    "frontside": "Frontside",
    "all_mountain": "All-mountain",
    "all_mountain_wide": "Wide all-mountain",
    "freeride": "Freeride",
    "powder": "Powder",
    "park": "Park & freestyle",
    "touring": "Touring",
}
TOURING_WORDS = re.compile(r"\b(?:tour|touring|backland|zero g|helio|transalp|ultravector|hypercharger|superguide|mtn|skimo|alp tracks|tracks|backcountry)\b", re.I)
PARK_WORDS = re.compile(r"\b(?:park|pipe|jib|twin|freestyle)\b", re.I)


class Catalog:
    def __init__(self, families: list[dict[str, Any]]) -> None:
        self.families = families
        self._index: dict[str, list[tuple[tuple[str, ...], dict[str, Any]]]] = {}
        for family in families:
            for key in family.get("match", []):
                tokens = tuple(key.split())
                if tokens:
                    self._index.setdefault(family["brand"], []).append((tokens, family))
        for entries in self._index.values():
            entries.sort(key=lambda item: -len(item[0]))

    def match(self, brand: str | None, model_key: str, gender: str | None = None) -> dict[str, Any] | None:
        if not brand or not model_key:
            return None
        tokens = tuple(model_key.split())
        if gender == "womens" and tokens and tokens[-1] == "w":
            candidates = [tokens, tokens[:-1]]
        else:
            candidates = [tokens]
        best: tuple[int, int, dict[str, Any]] | None = None
        for wanted in candidates:
            for prefix, family in self._index.get(brand, []):
                if wanted[: len(prefix)] != prefix:
                    continue
                # Prefer the longest key, then the family whose gender agrees with the listing.
                gender_bonus = 1 if (family.get("gender") == "womens") == (gender == "womens") else 0
                rank = (len(prefix), gender_bonus, family)
                if best is None or rank[:2] > best[:2]:
                    best = rank
        return best[2] if best else None


@lru_cache(maxsize=1)
def load(path: str = str(DATA)) -> Catalog:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Catalog([])
    return Catalog([f for f in payload.get("families", []) if isinstance(f, dict) and f.get("brand")])


def infer_category(waist: int | None, text: str) -> str | None:
    if TOURING_WORDS.search(text):
        return "touring"
    if PARK_WORDS.search(text) and (waist is None or waist <= 100):
        return "park"
    if waist is None:
        return None
    if waist < 78:
        return "carving"
    if waist < 89:
        return "frontside"
    if waist < 100:
        return "all_mountain"
    if waist < 107:
        return "all_mountain_wide"
    if waist < 112:
        return "freeride"
    return "powder"


def ski_profile(brand: str | None, model: str, model_key: str, gender: str | None, waist: int | None, title: str) -> dict[str, Any]:
    """Character facts for a ski listing, labelled with where they came from."""
    family = load().match(brand, model_key, gender)
    if family:
        return {
            "source": "catalog",
            "family": " ".join(filter(None, [family["brand"], family["names"][0] if family.get("names") else model])),
            "category": family.get("category"),
            "waist_mm": waist or family.get("waist_mm"),
            "playful": family.get("playful"),
            "demanding": family.get("demanding"),
            "level": family.get("level"),
            "tier": family.get("tier"),
            "twin": family.get("twin"),
            "touring": bool(family.get("touring")),
            "summary": family.get("summary"),
            "gender": family.get("gender"),
        }
    text = f"{model} {title}"
    category = infer_category(waist, text)
    metal = bool(re.search(r"\b\d{2,3}\s?(?:ti|cti)\b|\bti\b|titanal|metal", model_key + " " + title.lower()))
    playful = None
    demanding = None
    if category:
        playful = {"park": 5, "powder": 4, "freeride": 3, "all_mountain_wide": 3, "all_mountain": 3, "frontside": 2, "carving": 1, "touring": 3}[category]
        demanding = {"carving": 4, "frontside": 3, "freeride": 4}.get(category, 3)
        if metal:
            playful = max(1, playful - 1)
            demanding = min(5, demanding + 1)
    return {
        "source": "inferred" if category else "unknown",
        "family": None,
        "category": category,
        "waist_mm": waist,
        "playful": playful,
        "demanding": demanding,
        "level": None,
        "tier": None,
        "twin": None,
        "touring": category == "touring",
        "summary": None,
    }
