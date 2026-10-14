"""Turn inconsistent retailer text into structured product facts.

Everything here is deterministic and returns None when the text does not
support a value. Nothing is guessed to fill a gap.
"""
from __future__ import annotations

import html
import re
import unicodedata
from typing import Any, Iterable

SPACE = re.compile(r"\s+")
TAG = re.compile(r"<[^>]+>")

# Canonical brand -> extra spellings seen in feeds. The canonical name is matched too.
BRANDS: dict[str, tuple[str, ...]] = {
    "4FRNT": ("4frnt skis",),
    "Armada": (),
    "Atomic": (),
    "Black Crows": ("blackcrows",),
    "Black Diamond": (),
    "Blizzard": (),
    "Candide": ("candide skis",),
    "DPS": ("dps skis",),
    "Dynafit": (),
    "Dynastar": (),
    "Elan": (),
    "Faction": (),
    "Fischer": (),
    "G3": (),
    "Hagan": (),
    "Head": (),
    "Icelantic": (),
    "J Skis": ("j skis", "jskis"),
    "K2": (),
    "Kastle": ("kästle",),
    "La Sportiva": (),
    "Liberty": ("liberty skis",),
    "Lib Tech": ("libtech",),
    "Wagner": ("wagner custom",),
    "Bomber": (),
    "Crosson": (),
    "Folsom": ("folsom custom",),
    "Line": ("line skis",),
    "Majesty": (),
    "Moment": ("moment skis",),
    "Movement": (),
    "Nordica": (),
    "ON3P": (),
    "Peak": ("peak skis",),
    "Renoun": (),
    "RMU": ("rocky mountain underground",),
    "Rossignol": ("rossingol",),
    "Salomon": (),
    "Scott": (),
    "Season": ("season eqpt", "season equipment"),
    "Sego": (),
    "Ski Trab": (),
    "Stockli": ("stöckli",),
    "Volkl": ("völkl", "vlkl"),
    "Voile": ("voilé",),
    "WNDR Alpine": ("wndr",),
    "Zag": (),
    "Marker": (),
    "Look": (),
    "Tyrolia": (),
    "ATK": (),
    "Plum": (),
    "Lange": (),
    "Tecnica": (),
    "Dalbello": (),
    "Scarpa": (),
    "Stio": (),
    "Patagonia": (),
    "Arc'teryx": ("arcteryx",),
    "Flylow": (),
    "Trew": ("trew gear",),
    "Norrona": ("norrøna",),
    "Outdoor Research": (),
    "Strafe": (),
    "Helly Hansen": (),
    "Mammut": (),
    "The North Face": (),
}

CONDITIONS = ("new", "new_with_tags", "blem", "demo", "excellent", "good", "fair", "used")
CONDITION_LABELS = {
    "new": "New",
    "new_with_tags": "New with tags (resale)",
    "blem": "New, cosmetic blemish",
    "demo": "Demo",
    "excellent": "Used, excellent",
    "good": "Used, good",
    "fair": "Used, fair",
    "used": "Used",
}
_CONDITION_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bun-?new with tags\b|\bnew[- ]with[- ]tags\b|\bnwt\b|\bbrand new\b.*\btags\b", "new_with_tags"),
    (r"\bblem(?:ish(?:ed)?)?s?\b|\bfactory seconds?\b|\bcosmetic seconds?\b|\b2nds\b", "blem"),
    (r"\bexcellent\b|\blike[- ]new\b|\bvery good\b", "excellent"),
    (r"\bgood\b", "good"),
    (r"\bfair\b|\bwell[- ]used\b", "fair"),
    (r"\bdemo(?:s|ed)?\b|\bex[- ]?rental\b", "demo"),
    (r"\bused\b|\bpre[- ]?owned\b|\bsecond[- ]?hand\b|\bconsignment\b", "used"),
    (r"\bnew\b", "new"),
)

KID_PATTERN = re.compile(r"\b(?:kids?['’]?s?|juniors?|jr\.?|youth|boys?['’]?s?|girls?['’]?s?|groms?|toddlers?|children['’]?s)\b", re.I)
WOMEN_PATTERN = re.compile(r"\b(?:women['’]?s|womens|wmns|ladies|w['’]s)\b|\bW\b(?=\s|$)", re.I)
MEN_PATTERN = re.compile(r"\b(?:men['’]?s|mens)\b", re.I)
UNISEX_PATTERN = re.compile(r"\bunisex\b", re.I)

BINDING_CLAUSE = re.compile(
    r"\s*(?:\+|&|w/|with|and)\s+(?P<binding>[^+]*?\bbindings?\b)(?P<rest>.*)$",
    re.I,
)
# "Sender Soul 92 + Xp11 Mens Demo Skis": a binding model after "+" with no "bindings" word.
BINDING_PLUS = re.compile(r"\s\+\s*(?P<binding>[A-Za-z][A-Za-z.-]*\s?\d{1,2}(?:\.\d)?(?:\s?GW)?)(?=\s|$)")
SINGLE_SKI = re.compile(r"\bsingle\s+skis?\b|\b(?:left|right)\s+ski\s+only\b|\bsingle\s+(?:left|right)\b", re.I)
YEAR_RANGE = re.compile(r"(?<![\d$])(?:20)?(?P<a>\d{2})\s*[/\-–]\s*(?:20)?(?P<b>\d{2})(?!\d)")
YEAR_SINGLE = re.compile(r"(?<![\d$.])(20[12]\d)(?![\d.])")
LENGTH_CM = re.compile(r"(?<![\d.])(\d{3}(?:\.\d)?)\s*cm\b", re.I)
BARE_LENGTH = re.compile(r"(?<![\d.$])(1[3-9]\d|20\d)(?:\.\d)?(?![\d.]|\s*mm)")
WAIST = re.compile(r"(?<![\d.$/])(\d{2,3})(?=\s*(?:mm\b|ti\b|c\b|cti\b|w\b|x\b|sc\b|[a-z]{0,3}(?:\s|$|[^\w.])))", re.I)

NOISE_WORDS = re.compile(
    r"\b(?:skis?|alpine|downhill|all[- ]mountain|freeride|flat|open|unmounted|mounted|pair|"
    r"men['’]?s|mens|women['’]?s|womens|unisex|adult|new|used|demo|blem(?:ish(?:ed)?)?|"
    r"closeout|clearance|sale|outlet|only|system)\b",
    re.I,
)


def clean(value: Any) -> str:
    return SPACE.sub(" ", html.unescape(str(value or ""))).strip()


def strip_tags(value: Any) -> str:
    return clean(TAG.sub(" ", str(value or "")))


def fold(value: str) -> str:
    """Lowercase ASCII, so Völkl and Volkl compare equal."""
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c)).lower()


def money(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2) if value > 0 else None
    match = re.search(r"\d[\d,]*(?:\.\d+)?", str(value))
    if not match:
        return None
    number = float(match.group(0).replace(",", ""))
    return round(number, 2) if number > 0 else None


def detect_brand(title: str, vendor: str | None = None) -> str | None:
    haystack = fold(clean(title))
    vendor_folded = fold(clean(vendor or ""))
    best: tuple[int, int, str] | None = None
    for canonical, aliases in BRANDS.items():
        for name in (canonical,) + aliases:
            needle = fold(name)
            if vendor_folded == needle:
                return canonical
            match = re.search(r"(?<![a-z0-9])" + re.escape(needle) + r"(?![a-z0-9])", haystack)
            if match:
                # Earliest mention wins; the longer name breaks ties ("Black Diamond" over "Black").
                rank = (match.start(), -len(needle), canonical)
                if best is None or rank < best:
                    best = rank
    return best[2] if best else None


def model_year(title: str, tags: Iterable[str] = ()) -> int | None:
    """Season ranges resolve to the later year: 24/25 and 2024-2025 are both 2025."""
    text = clean(title)
    for match in YEAR_RANGE.finditer(text):
        first, second = int(match.group("a")), int(match.group("b"))
        if second == (first + 1) % 100 and 10 <= first <= 35:
            return 2000 + second
    years = [int(y) for y in YEAR_SINGLE.findall(text) if 2010 <= int(y) <= 2035]
    if years:
        return max(years)
    for tag in tags:
        tag_text = clean(tag)
        match = re.fullmatch(r"(?:season:\s*)?(20[12]\d)(?:map)?", tag_text, re.I)
        if match:
            return int(match.group(1))
    return None


def gender(title: str, tags: Iterable[str] = ()) -> str | None:
    text = clean(title)
    tag_text = " ".join(fold(clean(t)) for t in tags)
    if KID_PATTERN.search(text) or re.search(r"gender[_: ]+kids|\bkids\b|\bjunior\b|\byouth\b", tag_text):
        return "kids"
    tag_women = bool(re.search(r"gender[_: ]+womens|\bwomens?\b", tag_text))
    tag_men = bool(re.search(r"gender[_: ]+mens|\bmens?\b", tag_text))
    if WOMEN_PATTERN.search(text):
        return "womens"
    if tag_women and tag_men and not MEN_PATTERN.search(text):
        return "unisex"
    if tag_women:
        return "womens"
    if UNISEX_PATTERN.search(text) or "unisex" in tag_text:
        return "unisex"
    if MEN_PATTERN.search(text) or re.search(r"gender[_: ]+mens|\bmens?\b", tag_text):
        return "mens"
    return None


def condition(*labels: Any) -> str | None:
    """First label that names a condition wins, so pass the most specific first."""
    for label in labels:
        text = fold(clean(label))
        if not text:
            continue
        for pattern, value in _CONDITION_PATTERNS:
            if re.search(pattern, text):
                return value
    return None


def length_cm(*texts: Any, allow_bare: bool = True) -> float | None:
    """Ski length. Needs a cm unit, or a bare 130-209 number in a size field."""
    for text in texts:
        value = clean(text)
        if not value:
            continue
        match = LENGTH_CM.search(value)
        if match and 100 <= float(match.group(1)) <= 215:
            return float(match.group(1))
    if allow_bare:
        for text in texts:
            match = BARE_LENGTH.search(clean(text))
            if match:
                return float(match.group(0))
    return None


def bindings(title: str, default: str | None = None) -> dict[str, Any]:
    """included: True, False or None (unknown). demo marks adjustable demo bindings."""
    text = clean(title)
    match = BINDING_CLAUSE.search(text)
    if match:
        name = clean(re.sub(r"\b(?:ski\s+)?bindings?\b", "", match.group("binding"), flags=re.I))
        name = clean(re.sub(r"\bdemo\b", "", name, flags=re.I))
        return {"included": True, "demo": bool(re.search(r"\bdemo\b", match.group(0), re.I)), "model": name or None}
    plus = BINDING_PLUS.search(text)
    if plus:
        return {"included": True, "demo": bool(re.search(r"\bdemo\b", text, re.I)), "model": clean(plus.group("binding"))}
    if re.search(r"\b(?:flat|unmounted|ski only|skis only|no bindings?|without bindings?)\b", text, re.I):
        return {"included": False, "demo": False, "model": None}
    if default == "included":
        return {"included": True, "demo": bool(re.search(r"\bdemo\b", text, re.I)), "model": None}
    if default == "none":
        return {"included": False, "demo": False, "model": None}
    return {"included": None, "demo": False, "model": None}


def waist_mm(model_text: str) -> int | None:
    """Waist width from a model name. Lengths, years and prices never qualify."""
    text = LENGTH_CM.sub(" ", clean(model_text))
    text = YEAR_RANGE.sub(" ", text)
    text = YEAR_SINGLE.sub(" ", text)
    for match in WAIST.finditer(text):
        number = int(match.group(1))
        if 60 <= number <= 135:
            return number
    return None


def model_name(title: str, brand: str | None) -> str:
    """Product model without brand, year, gender, bindings, condition or marketing."""
    text = clean(title)
    text = BINDING_CLAUSE.sub("", text)
    text = BINDING_PLUS.sub(" ", text)
    text = re.sub(r"[\"“”][^\"“”]{1,40}[\"“”]", " ", text)  # graphic names such as "NIGHTLIFER"
    text = LENGTH_CM.sub(" ", text)
    text = YEAR_RANGE.sub(" ", text)
    text = YEAR_SINGLE.sub(" ", text)
    if brand:
        for name in sorted((brand,) + BRANDS.get(brand, ()), key=len, reverse=True):
            text = re.sub(r"(?<![\w])" + re.escape(name) + r"(?![\w])", " ", text, flags=re.I)
    text = re.sub(r"\s[-–|]\s(?:used|new|demo|blem\w*|women['’]?s|men['’]?s|unisex|excellent|good|fair)\b.*$", " ", text, flags=re.I)
    text = WOMEN_PATTERN.sub(" W ", text)
    text = NOISE_WORDS.sub(" ", text)
    text = re.sub(r"[()\[\],]", " ", text)
    text = re.sub(r"\s[-–|/+&]+(?=\s|$)", " ", text)
    text = re.sub(r"^\s*the\s+", "", clean(text), flags=re.I)
    text = clean(text).strip("-–|/ ")
    if brand and re.match(r"\d", text):
        # "Peak Skis Peak 98": the brand is also the model family.
        text = brand + " " + text
    return text


def model_key(model: str) -> str:
    """Order-preserving token key: 'M-Pro 99' and 'MPro 99' collapse, '99' and '90' do not."""
    text = fold(model)
    text = re.sub(r"(?<=[a-z])[-.](?=[a-z])", "", text)
    text = re.sub(r"(\d)\s*(ti|c|cti|x|sc|w)\b", r"\1 \2", text)
    tokens = re.findall(r"[a-z]+|\d+(?:\.\d+)?", text)
    return " ".join(tokens)


def clothing_size(*texts: Any) -> str | None:
    aliases = {
        "xxs": "XXS", "xs": "XS", "x-small": "XS", "extra small": "XS",
        "s": "S", "sm": "S", "small": "S",
        "m": "M", "md": "M", "med": "M", "medium": "M",
        "l": "L", "lg": "L", "large": "L",
        "xl": "XL", "x-large": "XL", "extra large": "XL",
        "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "3xl": "XXXL", "xxxl": "XXXL",
    }
    for text in texts:
        value = fold(clean(text))
        if not value:
            continue
        value = re.sub(r"^(?:estimated(?: size)?|size)\s+", "", value)
        head = re.split(r"\s*[/|]\s*|\s+-\s+", value)[0].strip()
        if head in aliases:
            return aliases[head]
        if re.fullmatch(r"\d{1,2}(?:\.\d)?(?:\s?(?:r|reg|regular|s|short|l|long))?", head):
            return head.upper().replace("REGULAR", "R").replace("REG", "R")
        if head in ("one size", "os", "o/s"):
            return "One Size"
    return None
