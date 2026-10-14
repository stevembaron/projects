"""Retailer adapters. Each returns a SourceReport; none ever raises for a bad source.

Adding a Shopify retailer is a config change (config/sources.json). Other
platforms get one small function registered in ADAPTERS.
"""
from __future__ import annotations

import hashlib
import html
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urljoin

from . import textparse as tp
from .net import Client, FetchError

DEFAULT_EXCLUDE = (
    r"\bsnowboard", r"\bsplitboard", r"\bwater\s?ski", r"\bwakeboard", r"\bnordic\b", r"\bcross[- ]country\b",
    r"\bxc\b", r"\bskate ski", r"\bclassic ski", r"\bski poles?\b", r"\bski straps?\b", r"\bski bag\b", r"\bskins?\b(?!.*\bskis?\b)",
    r"\bski (?:lock|holder|rack|leash)\b", r"\bgift card\b", r"\btune\b", r"\bmount(?:ing)? service\b",
)
SKI_TYPES = re.compile(r"ski|d s [mw]|h s [mw]|^skis?$", re.I)
GEARTRADE_CONDITION = re.compile(r'class="condition">\s*([^<]{2,40}?)\s*<', re.I)
SHIPPING_TAG = re.compile(r"^ship_fee_flatrate_(\d{1,3})$", re.I)


@dataclass
class SourceReport:
    source_id: str
    name: str
    status: str = "ok"  # ok | partial | failed | blocked | disabled
    offers: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    notes: list[str] = field(default_factory=list)
    pages: int = 0
    products_seen: int = 0
    elapsed_s: float = 0.0

    def summary(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "status": self.status,
            "error": self.error,
            "notes": self.notes,
            "pages": self.pages,
            "products_seen": self.products_seen,
            "offers": len(self.offers),
            "elapsed_s": round(self.elapsed_s, 1),
        }


def stable_id(*parts: Any) -> str:
    return hashlib.sha256("|".join(str(p) for p in parts).lower().encode()).hexdigest()[:14]


def classify_kind(title: str, product_type: str, fixed: str | None) -> str | None:
    """Product type first, then title. A ski sold "w/ ... Bindings" is a ski package, not a binding."""
    if fixed and fixed != "auto":
        return fixed
    kind = product_type.lower()
    if re.search(r"\bbindings?\b", kind) and not re.search(r"\bskis\b|\bski\s*-|with bindings|w/ bindings", kind):
        return "binding"
    if re.search(r"\bboots?\b", kind):
        return "boot"
    if re.search(r"\bskis?\b", kind) and not re.search(r"\bpoles?\b|\bbags?\b|\bskins?\b|\bapparel\b|\bjackets?\b|\bpants?\b", kind):
        return "ski"
    if tp.BINDING_CLAUSE.search(title) or tp.BINDING_PLUS.search(title):
        return "ski"
    if re.search(r"\bbindings?\b", title, re.I):
        return "binding"
    if re.search(r"\bboots?\b", title, re.I):
        return "boot"
    if re.search(r"\bskis?\b", title, re.I):
        return "ski"
    return None


def excluded(title: str, product_type: str, patterns: list[str], hardgoods: bool = True) -> str | None:
    text = f"{title} {product_type}"
    if tp.SINGLE_SKI.search(title):
        return "single ski"
    for pattern in (list(DEFAULT_EXCLUDE) if hardgoods else []) + patterns:
        if re.search(pattern, text, re.I):
            return pattern
    return None


def variant_option(product: dict[str, Any], variant: dict[str, Any], *names: str) -> str | None:
    for index, option in enumerate(product.get("options") or [], start=1):
        option_name = str(option.get("name", "") if isinstance(option, dict) else option).lower()
        if any(name in option_name for name in names):
            value = variant.get(f"option{index}")
            if value not in (None, "", "Default Title"):
                return tp.clean(value)
    return None


def shopify_offers(product: dict[str, Any], source: dict[str, Any], feed: dict[str, Any], observed_at: str) -> list[dict[str, Any]]:
    """One offer per product and condition, with every size as a variant."""
    title = tp.clean(product.get("title"))
    handle = product.get("handle")
    if not title or not handle:
        return []
    product_type = tp.clean(product.get("product_type"))
    tags = [tp.clean(t) for t in product.get("tags") or []]
    fixed = feed.get("kind")
    auto = classify_kind(title, product_type, None)
    # A ski feed often carries bindings, apparel or chairs. Trust the words first;
    # an unlabelled product only counts as a ski if a size parses as a ski length.
    needs_length = fixed == "ski" and auto is None
    kind = (auto if auto in ("ski", "binding", "boot") else "ski") if fixed == "ski" else classify_kind(title, product_type, fixed)
    if not kind or excluded(title, product_type, feed.get("exclude_title", []), kind in ("ski", "binding", "boot")):
        return []
    if feed.get("product_types") and not re.search(feed["product_types"], product_type, re.I):
        return []
    tag_set = {t.lower() for t in tags}
    if feed.get("require_tags") and not {t.lower() for t in feed["require_tags"]} <= tag_set:
        return []
    if feed.get("exclude_tags") and tag_set & {t.lower() for t in feed["exclude_tags"]}:
        return []

    who = tp.gender(title, tags)
    if who == "kids":
        return []
    if feed.get("genders") and who not in feed["genders"] and not (who is None and None in feed["genders"]):
        return []

    brand = tp.detect_brand(title, product.get("vendor")) or (tp.clean(product.get("vendor")) if feed.get("vendor_is_brand") else None)
    model = tp.model_name(title, brand)
    body_condition = None
    if feed.get("condition_from") == "body_html":
        match = GEARTRADE_CONDITION.search(product.get("body_html") or "")
        body_condition = html.unescape(match.group(1)) if match else None
    binding = tp.bindings(title, feed.get("bindings"))
    shipping = None
    for tag in tags:
        match = SHIPPING_TAG.match(tag)
        if match:
            shipping = {"cost": float(match.group(1)), "basis": "retailer flat-rate shipping tag"}
    if shipping is None and source.get("shipping", {}).get("flat") is not None:
        shipping = {"cost": float(source["shipping"]["flat"]), "basis": source["shipping"].get("basis", "retailer policy in config")}

    images = product.get("images") or []
    product_image = images[0].get("src") if images and isinstance(images[0], dict) else None
    base_url = source["base_url"].rstrip("/")
    groups: dict[str, dict[str, Any]] = {}
    for variant in product.get("variants") or []:
        price = tp.money(variant.get("price"))
        if price is None:
            continue
        available = variant.get("available")
        if feed.get("available_only", True) and available is False:
            continue
        raw_condition_label = body_condition or variant_option(product, variant, "condition")
        cond = (
            tp.condition(raw_condition_label)
            or tp.condition(variant.get("title"))
            or tp.condition(title, " ".join(t for t in tags if re.search(r"demo|blem|used|consign", t, re.I)))
            or next((value for tag, value in source.get("tag_conditions", {}).items() if tag.lower() in tag_set), None)
            or feed.get("condition")
        )
        if cond == "used" and binding.get("demo"):
            cond = "demo"
        if cond == "new" and re.search(r"\bblem", title, re.I):
            cond = "blem"
        size_text = variant_option(product, variant, "size", "length") or tp.clean(variant.get("title"))
        length = tp.length_cm(size_text, variant.get("title"), allow_bare=kind == "ski") if kind == "ski" else None
        if kind == "ski" and length is None:
            length = tp.length_cm(title, allow_bare=False)
        size = tp.clothing_size(size_text) if kind in ("clothing", "outerwear", "boot") else None
        if kind == "ski" and length is not None and not 120 <= length <= 200:
            continue
        if kind == "ski" and length is None and re.search(r"\b\d{2}\s*cm\b", size_text, re.I):
            continue  # junior lengths such as 80cm
        compare = tp.money(variant.get("compare_at_price"))
        if compare is not None and compare <= price:
            compare = None
        image = None
        featured = variant.get("featured_image")
        if isinstance(featured, dict):
            image = featured.get("src")
        key = cond or "unknown"
        group = groups.setdefault(key, {"condition": cond, "condition_label": raw_condition_label, "variants": [], "image": image})
        group["variants"].append({
            "vid": str(variant.get("id")) if variant.get("id") is not None else None,
            "label": (f"{int(length) if float(length).is_integer() else length} cm" if length else (size or tp.clean(variant.get("title")) or "One size")),
            "length_cm": length,
            "size": size,
            "price": price,
            "compare_at": compare,
            "available": available if isinstance(available, bool) else None,
        })

    if needs_length and not any(v["length_cm"] for g in groups.values() for v in g["variants"]):
        return []
    offers = []
    for key, group in groups.items():
        if not group["variants"]:
            continue
        url = f"{base_url}/products/{handle}"
        if len(group["variants"]) == 1 and group["variants"][0]["vid"] and len(product.get("variants") or []) > 1:
            url += f"?variant={group['variants'][0]['vid']}"
        offers.append({
            "id": stable_id(source["id"], handle, key),
            "source_id": source["id"],
            "source": source.get("name", source["id"]),
            "seller": source.get("seller", {}),
            "url": url,
            "title": title,
            "brand": brand,
            "model": model,
            "model_key": tp.model_key(model),
            "model_year": tp.model_year(title, tags),
            "gender": who,
            "kind": kind,
            "condition": group["condition"],
            "condition_label": group["condition_label"],
            "bindings": binding,
            "waist_mm": tp.waist_mm(model) if kind == "ski" else None,
            "image": group["image"] or product_image,
            "listed_at": product.get("published_at") or product.get("created_at"),
            "shipping": shipping,
            "tags": [t for t in tags if re.match(r"(?:ability-|skill level:|skis-best use:|skis-rocker profile:|flex:)", t, re.I)][:6],
            "price_scope": "exact",
            "variants": sorted(group["variants"], key=lambda v: (v["length_cm"] or 0, v["label"])),
            "observed_at": observed_at,
        })
    return offers


def collect_shopify(source: dict[str, Any], client: Client, observed_at: str) -> SourceReport:
    report = SourceReport(source["id"], source.get("name", source["id"]))
    seen: set[str] = set()
    failures: list[str] = []
    for feed in source.get("feeds", []):
        max_pages = int(feed.get("max_pages", source.get("max_pages", 6)))
        for page in range(1, max_pages + 1):
            url = f"{source['base_url'].rstrip('/')}/collections/{feed['collection']}/products.json?limit=250&page={page}"
            try:
                payload = client.get_json(url)
            except FetchError as error:
                failures.append(f"{feed['collection']} page {page}: {error}")
                if error.kind in ("blocked", "robots"):
                    report.status = "blocked"
                break
            products = payload.get("products") if isinstance(payload, dict) else None
            if not isinstance(products, list):
                failures.append(f"{feed['collection']} page {page}: unexpected response shape")
                break
            report.pages += 1
            for product in products:
                if not isinstance(product, dict):
                    continue
                report.products_seen += 1
                for offer in shopify_offers(product, source, feed, observed_at):
                    if offer["id"] not in seen:
                        seen.add(offer["id"])
                        report.offers.append(offer)
            if len(products) < 250:
                break
            if page == max_pages:
                report.notes.append(f"{feed['collection']}: stopped at the {max_pages}-page cap; later products were not checked")
    if failures:
        report.error = "; ".join(failures)[:600]
        if report.status != "blocked":
            report.status = "partial" if report.pages else "failed"
        elif report.pages:
            report.status = "partial"
    elif report.notes:
        report.status = "partial"
    return report


CAMPSAVER_ITEM = re.compile(r'<div\b(?P<attrs>[^>]*\bgtmProduct\b[^>]*)>(?P<body>.*?)(?=<div\b[^>]*\bgtmProduct\b|<script\b|</main>|</body>)', re.I | re.S)
HTML_ATTR = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"')


def campsaver_offers(markup: str, source: dict[str, Any], feed: dict[str, Any], observed_at: str) -> list[dict[str, Any]]:
    """CampSaver's grid shows one "from" price per product and no sizes."""
    offers = []
    base = source["base_url"]
    for match in CAMPSAVER_ITEM.finditer(markup):
        attrs = {k.lower(): html.unescape(v) for k, v in HTML_ATTR.findall(match.group("attrs"))}
        title = tp.clean(attrs.get("data-name"))
        price = tp.money(attrs.get("data-price"))
        slug = attrs.get("data-url") or ""
        if not title or price is None or not slug or excluded(title, "", feed.get("exclude_title", [])):
            continue
        who = tp.gender(title)
        if who == "kids":
            continue
        body = match.group("body")
        saving = re.search(r"Save\s+(?:Up\s+to\s+)?\$\s?([0-9,]+(?:\.[0-9]{2})?)", body, re.I)
        image = re.search(r'<img[^>]+src="([^"]+)"', body, re.I)
        brand = tp.detect_brand(title)
        model = tp.model_name(title, brand)
        url = urljoin(base, slug if slug.endswith(".html") else slug + ".html")
        offers.append({
            "id": stable_id(source["id"], url, "new"),
            "source_id": source["id"],
            "source": source.get("name", source["id"]),
            "seller": source.get("seller", {}),
            "url": url,
            "title": title,
            "brand": brand,
            "model": model,
            "model_key": tp.model_key(model),
            "model_year": tp.model_year(title),
            "gender": who,
            "kind": feed.get("kind", "ski"),
            "condition": "new",
            "condition_label": None,
            "bindings": tp.bindings(title),
            "waist_mm": tp.waist_mm(model),
            "image": image.group(1) if image else None,
            "listed_at": None,
            "shipping": None,
            "tags": [],
            # "Save up to $X" applies to the best variant, so it is not a verified original price.
            "price_scope": "from",
            "variants": [{"vid": None, "label": "Sizes not listed", "length_cm": None, "size": None, "price": price,
                          "compare_at": None, "available": None, "save_up_to": tp.money(saving.group(1)) if saving else None}],
            "observed_at": observed_at,
        })
    return offers


def collect_campsaver(source: dict[str, Any], client: Client, observed_at: str) -> SourceReport:
    report = SourceReport(source["id"], source.get("name", source["id"]))
    for feed in source.get("feeds", []):
        try:
            markup = client.get_text(feed["url"])
        except FetchError as error:
            report.status = "blocked" if error.kind in ("blocked", "robots") else "failed"
            report.error = str(error)
            continue
        report.pages += 1
        offers = campsaver_offers(markup, source, feed, observed_at)
        report.products_seen += len(offers)
        report.offers.extend(offers)
        if not offers:
            report.status = "failed"
            report.error = "The page loaded but no products could be read; the layout may have changed"
    return report


ADAPTERS: dict[str, Callable[[dict[str, Any], Client, str], SourceReport]] = {
    "shopify": collect_shopify,
    "campsaver": collect_campsaver,
}


def collect(source: dict[str, Any], client: Client, observed_at: str) -> SourceReport:
    if not source.get("enabled", True):
        return SourceReport(source["id"], source.get("name", source["id"]), status="disabled")
    adapter = ADAPTERS.get(source.get("adapter", "shopify"))
    started = time.monotonic()
    if adapter is None:
        report = SourceReport(source["id"], source.get("name", source["id"]), status="failed", error=f"Unknown adapter {source.get('adapter')}")
    else:
        try:
            report = adapter(source, client, observed_at)
        except Exception as error:  # an adapter bug must not take down the run
            report = SourceReport(source["id"], source.get("name", source["id"]), status="failed", error=f"Adapter error: {type(error).__name__}: {error}")
    report.elapsed_s = time.monotonic() - started
    return report
