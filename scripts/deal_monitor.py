#!/usr/bin/env python3
"""
Ski gear deal monitor.

This intentionally uses only the Python standard library so it can run from a
plain local checkout or a scheduled Codex automation without dependency setup.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "deal_sources.json"
DATA_DIR = ROOT / "data"
JSON_OUTPUT = DATA_DIR / "deals.json"
HTML_OUTPUT = DATA_DIR / "deals.html"
MD_OUTPUT = DATA_DIR / "deal_report.md"
PRICE_HISTORY_OUTPUT = DATA_DIR / "price_history.json"
EVO_CONSTRUCTOR_KEY_CACHE = DATA_DIR / "evo_constructor_key.json"
CLOTHING_JSON_OUTPUT = DATA_DIR / "clothing_deals.json"
PREFERENCES_CONFIG = ROOT / "config" / "deal_preferences.json"
WEB_DIR = ROOT / "ski-deals"
WEB_OUTPUT = WEB_DIR / "index.html"

# Keep this looking like a real, current browser. WAFs flag stale Chrome
# versions and custom UA suffixes (the old "... SkiDealMonitor/1.0" tail was a
# likely trigger for evo's 403s).
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/137.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Sec-Ch-Ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

PRICE_RE = re.compile(r"\$\s?([0-9]{1,4}(?:,[0-9]{3})?(?:\.[0-9]{2})?)")
SPACE_RE = re.compile(r"\s+")
MARKDOWN_LINK_RE = re.compile(r"\[(?P<label>[^\]]+)\]\((?P<url>https?://[^)]+)\)")
MARKDOWN_IMAGE_LINK_RE = re.compile(
    r"\[(?P<prefix>[^\]]*?)!\[(?P<alt>[^\]]*)\]\((?P<img>[^)]+)\)(?P<tail>[^\]]*?)\]\((?P<url>https?://[^)]+)\)",
    re.DOTALL,
)
EMBEDDED_PROMO_IMAGE_RE = re.compile(
    r"!\[[^\]]*\]\(https?://static\.evo\.com/[^)]+\)",
    re.IGNORECASE,
)
JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
REMIX_CONTEXT_RE = re.compile(r"window\.__remixContext\s*=\s*(\{.*?\});__remixContext\.p", re.DOTALL)
GEARTRADE_CARD_RE = re.compile(r"<product-card\b.*?</product-card>", re.IGNORECASE | re.DOTALL)
GEARTRADE_TITLE_RE = re.compile(
    r'<a(?=[^>]*\bcard-link\b)(?=[^>]*href="(?P<href>[^"]+)")[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
GEARTRADE_PRICE_RE = re.compile(
    r'<strong[^>]+class="[^"]*\bprice__current\b[^"]*"[^>]*>\$(?P<dollars>[0-9,]+)<sup>(?P<cents>[0-9]{2})',
    re.IGNORECASE | re.DOTALL,
)
GEARTRADE_DISCOUNT_RE = re.compile(r"(?P<discount>[0-9]{1,3})%\s*Off", re.IGNORECASE)
GEARTRADE_SIZE_RE = re.compile(r'<span[^>]+class="[^"]*\bplp_size\b[^"]*"[^>]*>.*?<b>\s*Size:\s*</b>\s*&nbsp;\s*(?P<size>[^<]+)', re.IGNORECASE | re.DOTALL)
GEARTRADE_IMAGE_RE = re.compile(r'<img[^>]+(?:src|data-src)="(?P<src>[^"]+)"', re.IGNORECASE | re.DOTALL)
CAMPSAVER_GRID_RE = re.compile(
    r'<div\b(?P<attrs>[^>]*\bgtmProduct\b[^>]*)>(?P<body>.*?)(?=<div\b[^>]*\bgtmProduct\b|<script\b|</main>|</body>)',
    re.IGNORECASE | re.DOTALL,
)
HTML_ATTR_RE = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"')
EVO_COLLECTION_ITEM_RE = re.compile(
    r'\{id:"[^"]+",name:"(?P<name>(?:[^"\\]|\\.)+)",.*?variant:"(?P<variant>(?:[^"\\]|\\.)*)",'
    r'\s*price:\s*"(?P<price>[^"]+)",.*?variantId:\s*"(?P<variant_id>\d+)",.*?handle:"(?P<handle>[^"]+)",\s*compareAtPrice:\s*"(?P<compare>[^"]+)"',
    re.DOTALL,
)
EVO_META_RE = re.compile(r"var meta = (?P<payload>\{\"products\":.*?\"page\":\{.*?\}\});", re.DOTALL)
EVO_CONSTRUCTOR_KEY_RE = re.compile(r'window\.eHS\.constructor_index_key\s*=\s*"(?P<key>[^"]+)"')
BLOCK_PATTERNS = [
    "before we continue",
    "human challenge",
    "captcha",
    "access denied",
    "forbidden",
    "verify you are human",
    "unusual traffic",
    "attention required",
    "sorry, you have been blocked",
    "something went wrong",
    "looking to shop",
    "awswaf",
    "challenge.js",
    "max challenge attempts exceeded",
    "javascript is disabled",
    "request blocked",
    "cloudfront",
]


@dataclass
class Deal:
    title: str
    url: str
    source: str
    current_price: float
    original_price: float | None
    discount_percent: float | None
    savings: float | None
    score: float
    found_at: str
    sizes: list[str] | None = None
    stock_status: str | None = None
    image_url: str | None = None
    is_cached: bool = False
    previous_price: float | None = None
    price_change: float | None = None
    price_change_percent: float | None = None
    price_trend: str | None = None
    first_seen_at: str | None = None
    lowest_price: float | None = None
    highest_price: float | None = None
    variant_id: str | None = None
    price_scope: str = "from"
    condition: str | None = None
    last_verified_at: str | None = None
    observation_count: int = 0
    history_start: str | None = None


@dataclass
class SourceError:
    source: str
    url: str
    error: str


class LinkTextParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.links: list[dict[str, str]] = []
        self._active_href: str | None = None
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attr_map = {key.lower(): value for key, value in attrs if value}
        href = attr_map.get("href")
        if href:
            self._active_href = urljoin(self.base_url, href)
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._active_href:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or not self._active_href:
            return
        text = clean_text(" ".join(self._text_parts))
        if text:
            self.links.append({"url": self._active_href, "text": text})
        self._active_href = None
        self._text_parts = []


def clean_text(value: str) -> str:
    return SPACE_RE.sub(" ", html.unescape(value)).strip()


def money(value: str | int | float | None) -> float | None:
    if value is None:
        return None
    match = re.search(r"[0-9][0-9,]*(?:\.[0-9]+)?", str(value))
    if not match:
        return None
    try:
        return round(float(match.group(0).replace(",", "")), 2)
    except ValueError:
        return None


def image_url(value: Any, base_url: str = "") -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        candidate = clean_text(value)
        if not candidate:
            return None
        if candidate.startswith("//"):
            return f"https:{candidate}"
        if candidate.startswith(("http://", "https://")):
            return candidate
        if base_url and candidate.startswith("/"):
            return urljoin(base_url, candidate)
        return None
    if isinstance(value, list):
        for item in value:
            candidate = image_url(item, base_url)
            if candidate:
                return candidate
    if isinstance(value, dict):
        for key in ("src", "url", "image", "imageUrl", "thumbnail", "thumbnailUrl"):
            candidate = image_url(value.get(key), base_url)
            if candidate:
                return candidate
        for key in ("nodes", "edges"):
            candidate = image_url(value.get(key), base_url)
            if candidate:
                return candidate
    return None


def first_image_from_fields(item: dict[str, Any], base_url: str, fields: tuple[str, ...]) -> str | None:
    for field in fields:
        candidate = image_url(item.get(field), base_url)
        if candidate:
            return candidate
    return None


def fetch(url: str, timeout: int = 25) -> str:
    request = Request(url, headers=REQUEST_HEADERS)
    for attempt in range(3):
        try:
            with urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)
    raise RuntimeError("Fetch retries exhausted")



def reader_url(url: str) -> str:
    return f"https://r.jina.ai/http://r.jina.ai/http://{quote(url, safe='')}"


def reader_url_variants(url: str) -> list[str]:
    variants = [url]
    parsed = urlparse(url)
    if parsed.scheme == "https":
        variants.append(urlunparse(parsed._replace(scheme="http")))
    return [reader_url(variant) for variant in variants]


def fetch_reader_target(url: str, timeout: int = 45) -> str:
    last_error: Exception | None = None
    last_block: str | None = None
    for candidate in reader_url_variants(url):
        try:
            markup = fetch(candidate, timeout=timeout)
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
            continue
        blocked = block_reason(markup)
        if not blocked:
            return markup
        last_block = blocked

    if last_block:
        raise OSError(last_block)
    if last_error:
        raise last_error
    raise OSError("Reader fallback failed")


def block_reason(markup: str) -> str | None:
    if "collectionView:{" in markup and "handle:" in markup and "compareAtPrice:" in markup:
        return None

    sample = clean_text(markup[:15000]).lower()
    for pattern in BLOCK_PATTERNS:
        if pattern in sample:
            return f"Blocked by retailer anti-bot page: {pattern}"
    return None


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def keyword_allowed(title: str, keywords: list[str], excludes: list[str]) -> bool:
    lowered = title.lower()
    if any(exclude_keyword_matches(lowered, excluded) for excluded in excludes):
        return False
    return not keywords or any(keyword.lower() in lowered for keyword in keywords)


def exclude_keyword_matches(value: str, keyword: str) -> bool:
    normalized = keyword.lower().strip()
    if not normalized:
        return False
    if normalized in {"kid", "kids", "kid's", "kids'"}:
        return bool(re.search(r"(?<![a-z0-9])kids?'?s?(?![a-z0-9])", value))
    pattern = re.escape(normalized).replace(r"\ ", r"[-\s]+")
    return bool(re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", value))


def flatten_json_ld(item: Any) -> list[dict[str, Any]]:
    if isinstance(item, list):
        flattened: list[dict[str, Any]] = []
        for child in item:
            flattened.extend(flatten_json_ld(child))
        return flattened
    if not isinstance(item, dict):
        return []

    nodes: list[dict[str, Any]] = []
    item_type = item.get("@type")
    types = item_type if isinstance(item_type, list) else [item_type]
    if any(str(kind).lower() == "product" for kind in types):
        nodes.append(item)

    graph = item.get("@graph")
    if graph:
        nodes.extend(flatten_json_ld(graph))

    for key in ("itemListElement", "offers", "mainEntity", "hasVariant"):
        if key in item:
            nodes.extend(flatten_json_ld(item[key]))

    if "item" in item:
        nodes.extend(flatten_json_ld(item["item"]))

    return nodes


def json_ld_candidates(markup: str, base_url: str, source_name: str, found_at: str) -> list[Deal]:
    deals: list[Deal] = []
    for match in JSON_LD_RE.finditer(markup):
        raw = clean_text(match.group(1))
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue

        for product in flatten_json_ld(payload):
            title = clean_text(str(product.get("name", "")))
            if not title:
                continue

            offers = product.get("offers", {})
            offer = offers[0] if isinstance(offers, list) and offers else offers
            offer = offer if isinstance(offer, dict) else {}

            current = money(offer.get("price") or product.get("price"))
            price_spec = offer.get("priceSpecification")
            price_spec_price = price_spec.get("price") if isinstance(price_spec, dict) else None
            original = money(offer.get("highPrice") or price_spec_price)
            url = offer.get("url") or product.get("url") or base_url
            if current:
                deals.append(
                    make_deal(
                        title,
                        urljoin(base_url, str(url)),
                        source_name,
                        current,
                        original,
                        found_at,
                        image_url=image_url(product.get("image"), base_url),
                    )
                )
    return deals


def remix_candidates(markup: str, base_url: str, source_name: str, found_at: str) -> list[Deal]:
    match = REMIX_CONTEXT_RE.search(markup)
    if not match:
        return []

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []

    loader_data = payload.get("state", {}).get("loaderData", {})
    deals: list[Deal] = []
    for route_data in loader_data.values():
        collection = route_data.get("collection") if isinstance(route_data, dict) else None
        products = collection.get("products", {}).get("nodes", []) if isinstance(collection, dict) else []
        for product in products:
            deals.extend(product_variant_deals(product, base_url, source_name, found_at))
    return deals


def shopify_products_json_candidates(
    payload_text: str,
    base_url: str,
    source_name: str,
    found_at: str,
    ignore_sold_out: bool = True,
    required_tags: list[str] | None = None,
    required_variant_terms: list[str] | None = None,
    size_min_cm: int | None = None,
    size_max_cm: int | None = None,
) -> list[Deal]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return []

    deals: list[Deal] = []
    required_tag_set = {tag.lower() for tag in required_tags or []}
    required_terms = [term.lower() for term in required_variant_terms or []]
    for product in payload.get("products", []):
        title = clean_text(str(product.get("title", "")))
        handle = product.get("handle")
        if not title or not handle:
            continue
        product_tags = {str(tag).lower() for tag in product.get("tags", [])}
        if required_tag_set and not required_tag_set.issubset(product_tags):
            continue

        product_url = urljoin(base_url, f"/products/{handle}")
        product_image = image_url(product.get("image"), base_url) or image_url(product.get("images"), base_url)
        for variant in product.get("variants", []):
            if ignore_sold_out and variant.get("available") is False:
                continue

            current = money(variant.get("price"))
            if current is None:
                continue

            original = money(variant.get("compare_at_price"))
            variant_title = normalize_shopify_variant_title(variant.get("title"))
            variant_text = variant_title.lower()
            if required_terms and not all(term in variant_text for term in required_terms):
                continue
            if not shopify_variant_size_allowed(variant_title, size_min_cm, size_max_cm):
                continue
            variant_size = shopify_variant_size_label(variant_title)
            deal_title = title if variant_title in ("", "Default Title") else f"{title} - {variant_title}"
            deals.append(
                make_deal(
                    deal_title,
                    product_url,
                    source_name,
                    current,
                    original,
                    found_at,
                    sizes=[variant_size] if variant_size else None,
                    variant_id=str(variant.get("id")) if variant.get("id") else None,
                    price_scope="exact",
                    stock_status="in_stock" if variant.get("available") is True else ("sold_out" if variant.get("available") is False else None),
                    condition="new" if "new" in variant_text or "new" in required_tag_set else None,
                    image_url=image_url(variant.get("featured_image"), base_url) or product_image,
                )
            )

    return deals


def shopify_variant_size_label(variant_title: str) -> str | None:
    match = re.search(r"\b(\d{2,3})\s*cm\b", variant_title, re.IGNORECASE)
    return f"{int(match.group(1))}cm" if match else None


def shopify_variant_size_allowed(variant_title: str, size_min_cm: int | None, size_max_cm: int | None) -> bool:
    if size_min_cm is None and size_max_cm is None:
        return True
    label = shopify_variant_size_label(variant_title)
    if not label:
        return False
    size = int(label.removesuffix("cm"))
    if size_min_cm is not None and size < size_min_cm:
        return False
    if size_max_cm is not None and size > size_max_cm:
        return False
    return True


def searchspring_candidates(
    payload_text: str,
    base_url: str,
    source_name: str,
    found_at: str,
) -> list[Deal]:
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        return []

    deals: list[Deal] = []
    for item in payload.get("results", []):
        if not isinstance(item, dict):
            continue

        title = clean_text(str(item.get("name") or item.get("title") or ""))
        current = money(item.get("price") or item.get("ss_price"))
        original = money(item.get("msrp") or item.get("compare_at_price"))
        if not title or current is None:
            continue

        handle = clean_text(str(item.get("handle") or ""))
        item_url = clean_text(str(item.get("url") or ""))
        if handle:
            item_url = urljoin(base_url, f"/products/{handle}")
        elif item_url:
            item_url = item_url.replace("https://utahskis.myshopify.com", "https://utahskis.com")
        else:
            item_url = base_url

        deals.append(
            make_deal(
                title,
                item_url,
                source_name,
                current,
                original,
                found_at,
                sizes=searchspring_sizes(item),
                stock_status="in_stock" if str(item.get("ss_sold_out", "0")) != "1" else "sold_out",
                image_url=first_image_from_fields(
                    item,
                    base_url,
                    (
                        "thumbnailImageUrl",
                        "imageUrl",
                        "image",
                        "thumbnail",
                        "ss_image",
                        "ss_image_url",
                        "primary_image",
                    ),
                ),
            )
        )

    return deals


def searchspring_sizes(item: dict[str, Any]) -> list[str] | None:
    sizes: set[str] = set()
    for value in item.get("ss_variants_in_stock") or []:
        text = clean_text(str(value))
        for pattern in (
            r"\boption1=([^,}]+)",
            r"\bdisplay_name=[^-]+-\s*([^,}]+)",
            r"\btitle=([^,}]+)",
        ):
            match = re.search(pattern, text)
            if not match:
                continue
            size = normalize_shopify_variant_title(match.group(1))
            if size and re.search(r"\d", size):
                sizes.add(size)
                break
    return sorted(sizes) or None


def product_variant_deals(product: dict[str, Any], base_url: str, source_name: str, found_at: str) -> list[Deal]:
    title = clean_text(str(product.get("title", "")))
    handle = product.get("handle")
    if not title or not handle:
        return []

    product_url = urljoin(base_url, f"/products/{handle}")
    product_image = image_url(product.get("featuredImage"), base_url) or image_url(product.get("images"), base_url)
    variants = product.get("variants", {}).get("nodes", [])
    deals: list[Deal] = []
    for variant in variants:
        if variant.get("availableForSale") is False:
            continue

        current = money(variant.get("price", {}).get("amount"))
        if current is None:
            continue

        original = money((variant.get("compareAtPrice") or {}).get("amount"))
        variant_title = normalize_shopify_variant_title(variant.get("title"))
        deal_title = title if variant_title in ("", "Default Title") else f"{title} - {variant_title}"
        deals.append(make_deal(deal_title, product_url, source_name, current, original, found_at, image_url=product_image,
            sizes=[shopify_variant_size_label(variant_title)] if shopify_variant_size_label(variant_title) else None,
            variant_id=str(variant.get("id")) if variant.get("id") else None, price_scope="exact",
            stock_status="in_stock" if variant.get("availableForSale") is True else None))
    return deals


def normalize_shopify_variant_title(value: Any) -> str:
    title = clean_text(str(value or ""))
    if not title:
        return ""
    return clean_text(re.sub(r"(?i)\s*/\s*n/?a\s*$", "", title))


def link_candidates(markup: str, base_url: str, source_name: str, found_at: str) -> list[Deal]:
    parser = LinkTextParser(base_url)
    parser.feed(markup)
    deals: list[Deal] = []

    for link in parser.links:
        prices = extract_offer_prices(link["text"], source_name)
        if not prices:
            continue

        current, original = choose_prices(prices)
        title = PRICE_RE.sub("", link["text"])
        title = clean_text(re.sub(r"\b(now|sale|was|reg|regular|from|save)\b", " ", title, flags=re.I))
        if len(title) < 8:
            continue
        deals.append(make_deal(title, link["url"], source_name, current, original, found_at))

    return deals


def markdown_candidates(markdown: str, base_url: str, source_name: str, found_at: str) -> list[Deal]:
    if "Markdown Content:" in markdown:
        markdown = markdown.split("Markdown Content:", 1)[1]

    # Evo's reader view sometimes injects a second promo image inside a
    # product card. Remove those embedded badges so the outer product link
    # still parses as a single markdown image link.
    markdown = EMBEDDED_PROMO_IMAGE_RE.sub(" ", markdown)

    deals = markdown_image_candidates(markdown, source_name, found_at)
    deals.extend(markdown_sierra_sequence_candidates(markdown, source_name, found_at))
    return deals


def campsaver_grid_candidates(markup: str, base_url: str, source_name: str, found_at: str) -> list[Deal]:
    if "campsaver" not in source_name.lower():
        return []

    deals: list[Deal] = []
    for match in CAMPSAVER_GRID_RE.finditer(markup):
        attrs = {name.lower(): html.unescape(value) for name, value in HTML_ATTR_RE.findall(match.group("attrs"))}
        title = clean_text(attrs.get("data-name") or "")
        current = money(attrs.get("data-price"))
        slug = attrs.get("data-url") or ""
        if not title or current is None or not slug:
            continue

        body = match.group("body")
        save_match = re.search(r"Save\s+(?:Up\s+to\s+)?\$\s?([0-9,]+(?:\.[0-9]{2})?)", body, re.I)
        savings = money(save_match.group(1)) if save_match else None
        original = round(current + savings, 2) if savings else None
        image_match = re.search(r'<img[^>]+src="(?P<src>[^"]+)"', body, re.I | re.DOTALL)
        model_match = re.search(r'title="(?P<count>[0-9]+\s+models?)\s+available"', body, re.I)
        flag_match = re.search(r'class="[^"]*\bgrid__item-flag\b[^"]*".*?<span\s+title="(?P<flag>[^"]+)"', body, re.I | re.DOTALL)
        prefix = f"{model_match.group('count')} " if model_match else ""
        suffix = f" {clean_text(flag_match.group('flag'))}" if flag_match else ""
        product_url = urljoin(base_url, slug if slug.endswith(".html") else f"{slug}.html")
        deals.append(
            make_deal(
                f"{prefix}{title}{suffix}",
                product_url,
                source_name,
                current,
                original,
                found_at,
                image_url=image_url(image_match.group("src"), base_url) if image_match else None,
            )
        )

    return deals


def geartrade_search_candidates(markup: str, base_url: str, source_name: str, found_at: str) -> list[Deal]:
    deals: list[Deal] = []
    for card in GEARTRADE_CARD_RE.findall(markup):
        title_match = GEARTRADE_TITLE_RE.search(card)
        price_match = GEARTRADE_PRICE_RE.search(card)
        if not title_match or not price_match:
            continue

        title = clean_text(re.sub(r"<[^>]+>", " ", title_match.group("title")))
        if len(title) < 4:
            continue

        current = money(f"{price_match.group('dollars')}.{price_match.group('cents')}")
        if current is None:
            continue

        discount_match = GEARTRADE_DISCOUNT_RE.search(card)
        discount = float(discount_match.group("discount")) if discount_match else None
        original = None
        if discount and 0 < discount < 100:
            original = round(current / (1 - (discount / 100)), 2)

        size_match = GEARTRADE_SIZE_RE.search(card)
        image_match = GEARTRADE_IMAGE_RE.search(card)
        sizes = [clean_text(size_match.group("size"))] if size_match else None
        deals.append(
            make_deal(
                title,
                urljoin(base_url, html.unescape(title_match.group("href"))),
                source_name,
                current,
                original,
                found_at,
                sizes=sizes,
                price_scope="exact",
                image_url=image_url(image_match.group("src"), base_url) if image_match else None,
            )
        )
    return deals


def evo_collection_candidates(markup: str, base_url: str, source_name: str, found_at: str) -> list[Deal]:
    if "evo.com" not in base_url:
        return []

    size_prefixes = evo_size_prefixes(base_url)
    if not size_prefixes:
        return []

    meta_products = evo_meta_products(markup)
    availability_cache: dict[str, dict[str, Any] | None] = {}
    deals: list[Deal] = []
    for match in EVO_COLLECTION_ITEM_RE.finditer(markup):
        handle = clean_text(match.group("handle").replace("\\/", "/"))
        title = clean_text(match.group("name").replace("\\/", "/"))
        current = money(match.group("price"))
        original = money(match.group("compare"))
        if not title or not handle or current is None:
            continue

        sizes, stock_status = evo_collection_stock_details(
            meta_products.get(handle),
            evo_product_availability(availability_cache, base_url, handle),
            current,
            size_prefixes,
        )
        if not sizes:
            continue

        deals.append(
            make_deal(
                title,
                urljoin(base_url, f"/products/{handle}"),
                source_name,
                current,
                original,
                found_at,
                sizes=sizes,
                price_scope="exact",
                stock_status=stock_status,
                image_url=evo_meta_product_image(meta_products.get(handle), base_url),
            )
        )

    return deals


def evo_hydrated_collection_candidates(
    markup: str,
    base_url: str,
    source_name: str,
    found_at: str,
    max_results: int,
) -> list[Deal]:
    if "evo.com" not in base_url:
        return []

    api_key = evo_constructor_api_key(markup)
    if not api_key:
        return []

    save_cached_evo_constructor_key(api_key)
    return evo_constructor_deals(api_key, base_url, source_name, found_at, max_results)


def evo_api_fallback_candidates(
    base_url: str,
    source: dict[str, Any],
    source_name: str,
    found_at: str,
    max_results: int,
) -> list[Deal]:
    """Query evo's Constructor search API directly when the page fetch is blocked.

    The API key is a public client-side key embedded in evo's pages. It rarely
    changes, so the last key seen on a successful page fetch is cached and
    reused here; a `constructor_key` field on the source config wins if set.
    """
    if "evo.com" not in base_url:
        return []

    api_key = clean_text(str(source.get("constructor_key") or "")) or load_cached_evo_constructor_key()
    if not api_key:
        return []
    return evo_constructor_deals(api_key, base_url, source_name, found_at, max_results)


def evo_constructor_deals(
    api_key: str,
    base_url: str,
    source_name: str,
    found_at: str,
    max_results: int,
) -> list[Deal]:
    parsed = urlparse(base_url)
    base_query = parse_qs(parsed.query, keep_blank_values=True)
    page = 1
    per_page = min(max_results, 100)
    deals: list[Deal] = []

    while len(deals) < max_results:
        url = evo_constructor_api_url(api_key, base_query, page, per_page)
        try:
            with urlopen(Request(url, headers=REQUEST_HEADERS), timeout=30) as response:
                payload = json.load(response)
        except (json.JSONDecodeError, HTTPError, URLError, TimeoutError, OSError):
            break

        page_results = payload.get("response", {}).get("results", [])
        if not isinstance(page_results, list) or not page_results:
            break

        for item in page_results:
            deal = evo_constructor_result_deal(item, source_name, found_at)
            if deal:
                deals.append(deal)
            if len(deals) >= max_results:
                break

        total = payload.get("response", {}).get("total_num_results")
        if not isinstance(total, int) or page * per_page >= total:
            break
        page += 1

    return deals[:max_results]


def evo_constructor_api_key(markup: str) -> str | None:
    match = EVO_CONSTRUCTOR_KEY_RE.search(markup)
    return match.group("key") if match else None


def load_cached_evo_constructor_key(path: Path | None = None) -> str | None:
    path = path or EVO_CONSTRUCTOR_KEY_CACHE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    key = clean_text(str(payload.get("key") or "")) if isinstance(payload, dict) else ""
    return key or None


def save_cached_evo_constructor_key(api_key: str, path: Path | None = None) -> None:
    path = path or EVO_CONSTRUCTOR_KEY_CACHE
    if load_cached_evo_constructor_key(path) == api_key:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"key": api_key, "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass


def evo_constructor_api_url(api_key: str, query: dict[str, list[str]], page: int, per_page: int) -> str:
    params: list[tuple[str, str]] = [
        ("key", api_key),
        ("sort_by", (query.get("sortBy") or ["relevance"])[0]),
        ("sort_order", (query.get("sortOrder") or ["descending"])[0]),
        ("num_results_per_page", str(per_page)),
        ("page", str(page)),
    ]
    for key, values in query.items():
        if key in {"sortBy", "sortOrder", "page"}:
            continue
        if key.startswith("filters["):
            for value in values:
                params.append((key, value))
    return "https://ac.cnstrc.com/browse/group_id/skis?" + "&".join(
        f"{quote(key, safe='')}={quote(value, safe='')}" for key, value in params
    )


def evo_constructor_result_deal(item: Any, source_name: str, found_at: str) -> Deal | None:
    if not isinstance(item, dict):
        return None
    data = item.get("data")
    title = clean_text(str(item.get("value", "")))
    if not isinstance(data, dict) or not title:
        return None

    url = clean_text(str(data.get("url") or ""))
    current = money(data.get("price"))
    original = money(data.get("compare_at_price"))
    size = clean_text(str(data.get("size") or ""))
    if not url or current is None:
        return None

    available = data.get("availability")
    stock_status = "in_stock" if available is True or str(available).lower() in {"true", "in_stock", "instock"} else ("sold_out" if available is False else None)
    sizes = [size] if evo_size_text(size) else None
    return make_deal(
        title,
        url,
        source_name,
        current,
        original,
        found_at,
        sizes=sizes,
        stock_status=stock_status,
        image_url=first_image_from_fields(
            data,
            url,
            (
                "image_url",
                "image",
                "thumbnail_url",
                "thumbnail",
                "primary_image",
                "groups_image_url",
            ),
        ),
    )


def evo_stock_status_from_payload(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return "availability_unknown"
    if payload.get("available", False):
        return "in_stock"
    return "sold_out"


def evo_size_text(value: str) -> bool:
    return bool(re.search(r"\b\d{2,3}\s*cm\b", value, re.I))


def evo_meta_products(markup: str) -> dict[str, dict[str, Any]]:
    match = EVO_META_RE.search(markup)
    if not match:
        return {}

    try:
        payload = json.loads(match.group("payload"))
    except json.JSONDecodeError:
        return {}

    products = payload.get("products", [])
    return {
        clean_text(str(product.get("handle", ""))): product
        for product in products
        if isinstance(product, dict) and product.get("handle")
    }


def evo_meta_product_image(product: dict[str, Any] | None, base_url: str) -> str | None:
    if not isinstance(product, dict):
        return None
    return first_image_from_fields(
        product,
        base_url,
        (
            "featured_image",
            "featuredImage",
            "image",
            "imageUrl",
            "images",
        ),
    )


def evo_product_availability(
    cache: dict[str, dict[str, Any] | None],
    base_url: str,
    handle: str,
) -> dict[str, Any] | None:
    if handle in cache:
        return cache[handle]

    product_url = urljoin(base_url, f"/products/{handle}.js")
    try:
        payload = json.loads(fetch(product_url, timeout=30))
    except (json.JSONDecodeError, HTTPError, URLError, TimeoutError, OSError):
        payload = None

    cache[handle] = payload if isinstance(payload, dict) else None
    return cache[handle]


def evo_collection_stock_details(
    product: dict[str, Any] | None,
    availability_payload: dict[str, Any] | None,
    current_price: float,
    size_prefixes: set[str],
) -> tuple[list[str], str | None]:
    if not isinstance(product, dict):
        return [], None

    available_variant_ids = evo_available_variant_ids(availability_payload)
    matching_sizes: list[str] = []
    available_sizes: list[str] = []
    for variant in product.get("variants", []):
        if not isinstance(variant, dict):
            continue
        variant_id = str(variant.get("id") or "")
        variant_price = evo_meta_variant_price(variant.get("price"))
        variant_title = clean_text(str(variant.get("public_title") or ""))
        if (
            not variant_id
            or variant_price != current_price
            or not evo_variant_matches_size_filter(variant_title, size_prefixes)
        ):
            continue
        matching_sizes.append(variant_title)
        if variant_id in available_variant_ids:
            available_sizes.append(variant_title)

    if available_sizes:
        return sorted(set(available_sizes)), "in_stock"
    if matching_sizes:
        if availability_payload is None:
            return sorted(set(matching_sizes)), "availability_unknown"
        return sorted(set(matching_sizes)), "sold_out"
    return [], None


def evo_available_variant_ids(payload: dict[str, Any] | None) -> set[str]:
    if not isinstance(payload, dict) or not payload.get("available", False):
        return set()

    return {
        str(variant.get("id"))
        for variant in payload.get("variants", [])
        if isinstance(variant, dict) and variant.get("available", False) and variant.get("id") is not None
    }


def evo_meta_variant_price(value: Any) -> float | None:
    if isinstance(value, int):
        return round(value / 100, 2)
    if isinstance(value, str) and value.isdigit():
        return round(int(value) / 100, 2)
    return money(value)


def evo_size_prefixes(base_url: str) -> set[str]:
    query = parse_qs(urlparse(base_url).query)
    prefixes: set[str] = set()
    for value in query.get("filters[size]", []):
        match = re.search(r"\b([0-9]{2})[0-9]\s*cm\b", value, re.I)
        if match:
            prefixes.add(match.group(1))
    return prefixes


def evo_variant_matches_size_filter(variant_title: str, size_prefixes: set[str]) -> bool:
    match = re.search(r"\b([0-9]{2})[0-9]\s*cm\b", variant_title, re.I)
    return bool(match and match.group(1) in size_prefixes)


def markdown_image_candidates(markdown: str, source_name: str, found_at: str) -> list[Deal]:
    deals: list[Deal] = []
    matches = list(MARKDOWN_IMAGE_LINK_RE.finditer(markdown))
    for index, match in enumerate(matches):
        url = match.group("url")
        if not is_product_url(url):
            continue

        title = clean_markdown_image_title(match.group("alt"))
        if len(title) < 8:
            title = clean_markdown_title(
                f"{match.group('prefix')} {match.group('alt')} {match.group('tail')}"
            )
        if not title:
            title = title_from_sierra_image(match.group("img"))
        if not title or len(title) < 8:
            continue

        next_start = matches[index + 1].start() if index + 1 < len(matches) else min(len(markdown), match.end() + 800)
        block = markdown[match.start() : next_start]
        prices = extract_offer_prices(block, source_name)
        if not prices:
            continue

        compare_at = re.search(r"Compare At\s+\$\s?([0-9,]+(?:\.[0-9]{2})?)", block, re.I)
        list_at = re.search(r"\bList:?\s+\$\s?([0-9,]+(?:\.[0-9]{2})?)", block, re.I)
        current, original = choose_prices(prices)
        if compare_at:
            original = money(compare_at.group(1))
        elif list_at:
            original = money(list_at.group(1))
        deals.append(make_deal(title, url, source_name, current, original, found_at, image_url=image_url(match.group("img"))))
    return deals


def clean_markdown_image_title(value: str) -> str:
    value = clean_markdown_title(value)
    value = re.sub(r"^(?:image\s+)?\d+\s*:?\s*", "", value, flags=re.I)
    return value


def markdown_sierra_sequence_candidates(markdown: str, source_name: str, found_at: str) -> list[Deal]:
    deals: list[Deal] = []
    matches = list(MARKDOWN_LINK_RE.finditer(markdown))

    for index, match in enumerate(matches):
        label = match.group("label")
        url = match.group("url")
        if "sierra.com" not in url or "~p~" not in url:
            continue

        next_start = matches[index + 1].start() if index + 1 < len(matches) else min(len(markdown), match.end() + 500)
        block = markdown[match.end() : next_start]
        title = clean_markdown_title(label)
        if title.lower().startswith("image"):
            img_match = re.search(r"https://[^)]+/([^/~]+(?:-[^/~]+)*)~p~", match.group(0))
            title = img_match.group(1).replace("-", " ").title() if img_match else ""

        prices = extract_prices(block)
        if not title or not prices:
            continue

        current = prices[0]
        original_match = re.search(r"Compare At\s+\$\s?([0-9,]+(?:\.[0-9]{2})?)", block, re.I)
        original = money(original_match.group(1)) if original_match else (prices[1] if len(prices) > 1 else None)
        deals.append(make_deal(title, url, source_name, current, original, found_at))

    return deals


def extract_prices(value: str) -> list[float]:
    prices = [money(match.group(1)) for match in PRICE_RE.finditer(value)]
    return [price for price in prices if price is not None]


def extract_offer_prices(value: str, source_name: str) -> list[float]:
    if "campsaver" in source_name.lower():
        # CampSaver variant rows include "Save $X" next to List/current prices.
        # Treating that savings amount as a price creates impossible $69 ski deals.
        value = re.sub(r"\bSave\s+(?:Up\s+to\s+)?\$\s?[0-9,]+(?:\.[0-9]{2})?", " ", value, flags=re.I)
    return extract_prices(value)


def choose_prices(prices: list[float]) -> tuple[float, float | None]:
    if len(prices) == 1:
        return prices[0], None
    current = min(prices)
    original = max(prices)
    return current, original if original > current else None


def clean_markdown_title(value: str) -> str:
    value = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", value)
    value = re.sub(r"\b(Image|Sale|Compare|View Selections)\b", " ", value, flags=re.I)
    value = PRICE_RE.sub(" ", value)
    value = re.sub(r"\b(Sale\s*-\s*)\b", " ", value, flags=re.I)
    return collapse_repeated_title(clean_text(value))


def collapse_repeated_title(value: str) -> str:
    parts = value.split()
    if len(parts) % 2:
        return collapse_repeated_prefix(parts, value)
    midpoint = len(parts) // 2
    if parts[:midpoint] == parts[midpoint:]:
        return " ".join(parts[:midpoint])
    return collapse_repeated_prefix(parts, value)


def collapse_repeated_prefix(parts: list[str], fallback: str) -> str:
    max_prefix = len(parts) // 2
    for size in range(max_prefix, 2, -1):
        if parts[:size] == parts[size : size * 2]:
            return " ".join(parts[:size] + parts[size * 2 :])
    return fallback


def title_from_sierra_image(image_url: str) -> str:
    filename = image_url.rsplit("/", 1)[-1]
    slug = filename.split("~p~", 1)[0]
    slug = re.sub(r"-in-[a-z0-9-]+$", "", slug, flags=re.I)
    return clean_text(slug.replace("-", " ")).title()


def is_product_url(url: str) -> bool:
    if "sierra.com" in url:
        return "~p~" in url
    if "evo.com" in url:
        return "static.evo.com" not in url and "/shop/" not in url
    if "campsaver.com" in url:
        return True
    return url.startswith("http")


def make_deal(
    title: str,
    url: str,
    source: str,
    current: float,
    original: float | None,
    found_at: str,
    sizes: list[str] | None = None,
    stock_status: str | None = None,
    image_url: str | None = None,
    is_cached: bool = False,
    variant_id: str | None = None,
    price_scope: str = "from",
    condition: str | None = None,
) -> Deal:
    discount = None
    savings = None
    if original and original > current:
        savings = round(original - current, 2)
        discount = round((savings / original) * 100, 1)

    score = current_score(current, discount, savings)
    return Deal(
        title=title[:180],
        url=url,
        source=source,
        current_price=current,
        original_price=original,
        discount_percent=discount,
        savings=savings,
        score=score,
        found_at=found_at,
        sizes=sizes,
        stock_status=stock_status,
        image_url=image_url,
        is_cached=is_cached,
        variant_id=variant_id,
        price_scope=price_scope,
        condition=condition,
        last_verified_at=None if is_cached else found_at,
    )


def current_score(current: float, discount: float | None, savings: float | None) -> float:
    discount_score = discount or 0
    savings_score = min((savings or 0) / 4, 35)
    price_score = max(0, 20 - min(current / 50, 20))
    return round(discount_score + savings_score + price_score, 2)


SIZE_SUFFIX_RE = re.compile(r"(?i)^(?:(?:[^/]+?)\s*/\s*)?(?:\d{3}|\d{2,3}\.\d)(?:\s*cm)?$")


def split_size_variant(title: str) -> tuple[str, str | None]:
    if " - " not in title:
        return title, None
    base, suffix = title.rsplit(" - ", 1)
    suffix = clean_text(suffix)
    if not SIZE_SUFFIX_RE.match(suffix):
        return title, None
    return clean_text(base), suffix


def consolidate_size_variants(deals: list[Deal]) -> list[Deal]:
    # Each offer keeps its own price, size, stock and identity.
    return dedupe(deals)



def dedupe(deals: list[Deal]) -> list[Deal]:
    from deal_rules import offer_key
    best = {}
    for deal in deals:
        key = offer_key(deal)
        existing = best.get(key)
        if existing is None or (deal.price_scope == 'exact', deal.stock_status == 'in_stock', not deal.is_cached) > (existing.price_scope == 'exact', existing.stock_status == 'in_stock', not existing.is_cached):
            best[key] = deal
    return list(best.values())



def filter_and_sort(deals: list[Deal], config: dict[str, Any]) -> list[Deal]:
    keywords = config.get("keywords", [])
    excludes = config.get("exclude_keywords", [])
    min_discount = float(config.get("min_discount_percent", 0) or 0)

    filtered = []
    for deal in consolidate_size_variants(dedupe(deals)):
        if not keyword_allowed(deal.title, keywords, excludes):
            continue
        if deal.discount_percent is not None and deal.discount_percent < min_discount:
            continue
        filtered.append(deal)

    from deal_rules import enrich
    prefs = load_preferences(PREFERENCES_CONFIG)
    annotated = [dict(asdict(d), category='clothing' if config.get('json_output') == 'data/clothing_deals.json' else 'ski') for d in filtered]
    enrich(annotated, prefs)
    relevance = {id(d): meta['score'] for d, meta in zip(filtered, annotated)}
    return sorted(filtered, key=lambda d: (stock_sort_key(d.stock_status), -relevance[id(d)], d.current_price))


def scan(config: dict[str, Any]) -> tuple[list[Deal], list[SourceError]]:
    found_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    all_deals: list[Deal] = []
    errors: list[SourceError] = []
    history = load_price_history(resolve_output_path(config.get("price_history_output"), PRICE_HISTORY_OUTPUT))
    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue

        source_name = source.get("name") or source.get("url")
        url = source.get("url")
        if not url:
            continue

        markup = ""
        source_filter_config = merged_filter_config(config, source)
        per_source_limit = int(source_filter_config.get("max_results_per_source", 30) or 30)

        try:
            if source.get("searchspring_json"):
                candidates = searchspring_candidates(
                    fetch(source["searchspring_json"], timeout=30),
                    url,
                    source_name,
                    found_at,
                )
                all_deals.extend(filter_and_sort(candidates, source_filter_config)[:per_source_limit])
                time.sleep(float(source.get("delay_seconds", 1.2)))
                continue

            if source.get("prefer_reader_fallback") and source.get("reader_fallback"):
                markup = fetch_reader_target(source.get("reader_url") or url, timeout=45)
                blocked = block_reason(markup)
                if blocked:
                    all_deals.extend(cached_source_deals(history, source_name, found_at, per_source_limit))
                    errors.append(SourceError(source_name, url, blocked))
                    continue
            else:
                markup = fetch(url)
                blocked = block_reason(markup)
            if blocked:
                candidates = []
                if source.get("shopify_products_json"):
                    candidates.extend(
                        shopify_products_json_candidates(
                            fetch(source["shopify_products_json"], timeout=30),
                            url,
                            source_name,
                            found_at,
                            bool(source.get("ignore_sold_out", True)),
                            list(source.get("shopify_required_tags", [])),
                            list(source.get("shopify_required_variant_terms", [])),
                            source.get("size_min_cm"),
                            source.get("size_max_cm"),
                        )
                    )
                if candidates:
                    all_deals.extend(filter_and_sort(candidates, source_filter_config)[:per_source_limit])
                    time.sleep(float(source.get("delay_seconds", 1.2)))
                    continue
                evo_deals = evo_api_fallback_candidates(url, source, source_name, found_at, per_source_limit)
                if evo_deals:
                    all_deals.extend(filter_and_sort(evo_deals, source_filter_config)[:per_source_limit])
                    time.sleep(float(source.get("delay_seconds", 1.2)))
                    continue
                if not source.get("reader_fallback"):
                    all_deals.extend(cached_source_deals(history, source_name, found_at, per_source_limit))
                    errors.append(SourceError(source_name, url, blocked))
                    continue
                markup = fetch_reader_target(source.get("reader_url") or url, timeout=45)
                blocked = block_reason(markup)
                if blocked:
                    all_deals.extend(cached_source_deals(history, source_name, found_at, per_source_limit))
                    errors.append(SourceError(source_name, url, blocked))
                    continue
            candidates = json_ld_candidates(markup, url, source_name, found_at)
            candidates.extend(remix_candidates(markup, url, source_name, found_at))
            evo_hydrated_candidates: list[Deal] = []
            if "evo.com" in url:
                evo_hydrated_candidates = evo_hydrated_collection_candidates(
                    markup,
                    url,
                    source_name,
                    found_at,
                    per_source_limit,
                )
            if evo_hydrated_candidates:
                candidates.extend(evo_hydrated_candidates)
            else:
                candidates.extend(evo_collection_candidates(markup, url, source_name, found_at))
            if source.get("shopify_products_json"):
                candidates.extend(
                    shopify_products_json_candidates(
                        fetch(source["shopify_products_json"], timeout=30),
                        url,
                        source_name,
                        found_at,
                        bool(source.get("ignore_sold_out", True)),
                        list(source.get("shopify_required_tags", [])),
                        list(source.get("shopify_required_variant_terms", [])),
                        source.get("size_min_cm"),
                        source.get("size_max_cm"),
                    )
                )
            campsaver_candidates = campsaver_grid_candidates(markup, url, source_name, found_at)
            if campsaver_candidates:
                candidates.extend(campsaver_candidates)
            else:
                candidates.extend(link_candidates(markup, url, source_name, found_at))
                candidates.extend(markdown_candidates(markup, url, source_name, found_at))
            candidates.extend(geartrade_search_candidates(markup, url, source_name, found_at))
            if not candidates and source.get("reader_fallback"):
                markup = fetch_reader_target(source.get("reader_url") or url, timeout=45)
                candidates = campsaver_grid_candidates(markup, url, source_name, found_at)
                if not candidates:
                    candidates = markdown_candidates(markup, url, source_name, found_at)
                    candidates.extend(link_candidates(markup, url, source_name, found_at))
                candidates.extend(geartrade_search_candidates(markup, url, source_name, found_at))
            if not candidates:
                errors.append(SourceError(source_name, url, "No products parsed; availability is unverified"))
            all_deals.extend(filter_and_sort(candidates, source_filter_config)[:per_source_limit])
            time.sleep(float(source.get("delay_seconds", 1.2)))
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            try:
                evo_deals = evo_api_fallback_candidates(url, source, source_name, found_at, per_source_limit)
            except (HTTPError, URLError, TimeoutError, OSError):
                evo_deals = []
            if evo_deals:
                all_deals.extend(filter_and_sort(evo_deals, source_filter_config)[:per_source_limit])
                time.sleep(float(source.get("delay_seconds", 1.2)))
                continue
            if source.get("reader_fallback"):
                try:
                    candidates = []
                    if source.get("shopify_products_json"):
                        candidates.extend(
                            shopify_products_json_candidates(
                                fetch(source["shopify_products_json"], timeout=30),
                                url,
                                source_name,
                                found_at,
                                bool(source.get("ignore_sold_out", True)),
                                list(source.get("shopify_required_tags", [])),
                                list(source.get("shopify_required_variant_terms", [])),
                                source.get("size_min_cm"),
                                source.get("size_max_cm"),
                            )
                        )
                    if candidates:
                        all_deals.extend(filter_and_sort(candidates, source_filter_config)[:per_source_limit])
                        time.sleep(float(source.get("delay_seconds", 1.2)))
                        continue
                    markup = fetch_reader_target(source.get("reader_url") or url, timeout=45)
                    blocked = block_reason(markup)
                    if blocked:
                        all_deals.extend(cached_source_deals(history, source_name, found_at, per_source_limit))
                        errors.append(SourceError(source_name, url, blocked))
                        continue
                    candidates = campsaver_grid_candidates(markup, url, source_name, found_at)
                    if not candidates:
                        candidates = markdown_candidates(markup, url, source_name, found_at)
                        candidates.extend(link_candidates(markup, url, source_name, found_at))
                    candidates.extend(geartrade_search_candidates(markup, url, source_name, found_at))
                    all_deals.extend(filter_and_sort(candidates, source_filter_config)[:per_source_limit])
                    time.sleep(float(source.get("delay_seconds", 1.2)))
                    continue
                except (HTTPError, URLError, TimeoutError, OSError) as fallback_error:
                    all_deals.extend(cached_source_deals(history, source_name, found_at, per_source_limit))
                    errors.append(SourceError(source_name, url, f"{error}; reader fallback failed: {fallback_error}"))
                    continue
            all_deals.extend(cached_source_deals(history, source_name, found_at, per_source_limit))
            errors.append(SourceError(source_name, url, str(error)))

    return rank_deals(dedupe(all_deals)), errors


def cached_source_deals(history, source_name, found_at, limit):
    from deal_history import cached_deals
    preferences = load_preferences(PREFERENCES_CONFIG)
    return cached_deals(history, source_name, found_at, limit, preferences.get('freshness', {}).get('hide_cached_after_hours', 72))



def merged_filter_config(config: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    merged = dict(config)
    for key in ("keywords", "exclude_keywords", "min_discount_percent", "max_results_per_source"):
        if key in source:
            if key == "exclude_keywords":
                merged[key] = list(config.get(key, [])) + list(source.get(key, []))
            else:
                merged[key] = source[key]
    return merged


def rank_deals(deals: list[Deal]) -> list[Deal]:
    return sorted(
        deals,
        key=lambda item: (
            stock_sort_key(item.stock_status),
            -(item.score),
            -(item.discount_percent or 0),
            -(item.savings or 0),
        ),
    )


def stock_sort_key(status: str | None) -> int:
    if status == "sold_out":
        return 2
    if status == "availability_unknown":
        return 1
    return 0


def stock_label(status: str | None) -> str | None:
    if status == "in_stock":
        return "In stock"
    if status == "sold_out":
        return "Sold out"
    if status == "availability_unknown":
        return "Availability unknown"
    return None


def price_history_key(deal):
    from deal_rules import offer_key
    return offer_key(deal)



def load_price_history(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"items": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"items": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), dict):
        return {"items": {}}
    sanitize_price_history(payload)
    return payload


def sanitize_price_history(history: dict[str, Any]) -> None:
    items = history.get("items")
    if not isinstance(items, dict):
        return

    stale_keys = [
        key
        for key, item in items.items()
        if isinstance(item, dict)
        and item.get("source") == "Geartrade Stio men's clothing"
        and not is_stio_deal(item)
    ]
    for key in stale_keys:
        del items[key]

    for item in items.values():
        if not isinstance(item, dict) or item.get("source") != "CampSaver backcountry skis":
            continue
        if not campsaver_has_suspicious_cached_price(item):
            continue

        observations = item.get("observations")
        if not isinstance(observations, list):
            continue
        sane_observations = [
            observation
            for observation in observations
            if isinstance(observation, dict) and (money(observation.get("price")) or 0) >= 100
        ]
        if not sane_observations:
            continue

        item["observations"] = sane_observations
        latest = max(sane_observations, key=lambda observation: str(observation.get("date", "")))
        prices = [price for price in [money(observation.get("price")) for observation in sane_observations] if price is not None]
        latest_price = money(latest.get("price"))
        if latest_price is not None:
            item["current_price"] = latest_price
        if prices:
            item["lowest_price"] = min(prices)
            item["highest_price"] = max(prices)


def is_stio_deal(deal: Deal | dict[str, Any]) -> bool:
    title = str(deal["title"] if isinstance(deal, dict) else deal.title)
    url = str(deal["url"] if isinstance(deal, dict) else deal.url)
    return bool(re.search(r"\bstio\b", title, re.I) or re.search(r"/products/stio-", url, re.I))


def campsaver_has_suspicious_cached_price(item: dict[str, Any]) -> bool:
    current = money(item.get("current_price"))
    highest = money(item.get("highest_price"))
    title = str(item.get("title") or "").lower()
    if current is None:
        return False
    return current < 100 and (highest or 0) > 300 and ("as low as" in title or "black diamond impulse" in title)


def latest_prior_observation(item: dict[str, Any], today: str) -> dict[str, Any] | None:
    observations = item.get("observations")
    if not isinstance(observations, list):
        return None
    prior = [
        observation
        for observation in observations
        if isinstance(observation, dict) and str(observation.get("date", "")) < today
    ]
    return max(prior, key=lambda observation: str(observation.get("date", ""))) if prior else None


def annotate_and_update_price_history(deals, history_path, generated_at):
    from deal_history import update
    return update(deals, history_path, generated_at)



def price_trend_label(deal: dict[str, Any]) -> str | None:
    trend = deal.get("price_trend")
    change = deal.get("price_change")
    percent = deal.get("price_change_percent")
    previous = deal.get("previous_price")
    percent_label = f" ({abs(percent):.1f}%)" if isinstance(percent, (int, float)) else ""
    if trend == "down" and change is not None:
        return f"Down ${abs(change):.2f}{percent_label} since prior day"
    if trend == "up" and change is not None:
        return f"Up ${abs(change):.2f}{percent_label} since prior day"
    if trend == "flat" and previous is not None:
        return "Same as prior day"
    if trend == "new":
        return "Newly tracked"
    return None


def write_outputs(deals: list[Deal], errors: list[SourceError], config: dict[str, Any]) -> None:
    json_output = resolve_output_path(config.get("json_output"), JSON_OUTPUT)
    markdown_output = resolve_output_path(config.get("markdown_output"), MD_OUTPUT)
    html_output_path = resolve_output_path(config.get("html_output"), HTML_OUTPUT)
    web_output = resolve_output_path(config.get("web_output"), WEB_OUTPUT)
    history_output = resolve_output_path(config.get("price_history_output"), PRICE_HISTORY_OUTPUT)

    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    html_output_path.parent.mkdir(parents=True, exist_ok=True)
    web_output.parent.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    history = annotate_and_update_price_history(deals, history_output, generated_at)
    changed_deals = [
        deal
        for deal in deals
        if deal.price_trend in {"up", "down"} and deal.price_change is not None
    ]
    payload = {
        "generated_at": generated_at,
        "deal_count": len(deals),
        "sources_checked": len([source for source in config.get("sources", []) if source.get("enabled", True)]),
        "price_history_count": int(history.get("tracked_count") or 0),
        "price_change_count": len(changed_deals),
        "deals": [asdict(deal) for deal in deals],
        "errors": [asdict(error) for error in errors],
    }

    json_output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    markdown_output.write_text(render_markdown(payload, config), encoding="utf-8")
    html_payload, html_config = combined_tracker_payload(payload, config)
    html_output = trim_trailing_whitespace(render_html(html_payload, html_config))
    html_output_path.write_text(html_output, encoding="utf-8")
    web_output.write_text(html_output, encoding="utf-8")


def resolve_output_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def trim_trailing_whitespace(value: str) -> str:
    return "\n".join(line.rstrip() for line in value.splitlines()) + "\n"


def combined_tracker_payload(payload, config):
    from deal_dataset import build_dataset
    if resolve_output_path(config.get('json_output'), JSON_OUTPUT) != JSON_OUTPUT:
        return dict(payload, deals=[tag_deal_for_category(d, 'clothing') for d in payload.get('deals', [])]), config
    combined = build_dataset(payload, load_json_payload(CLOTHING_JSON_OUTPUT), load_preferences(PREFERENCES_CONFIG),
                             load_price_history(PRICE_HISTORY_OUTPUT))
    (DATA_DIR / 'tracker.json').write_text(json.dumps(combined, indent=2) + '\n')
    return combined, dict(config, report_title='Gear Deals')



def load_json_payload(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None


def tag_deal_for_category(deal: dict[str, Any], category: str) -> dict[str, Any]:
    tagged = dict(deal)
    tagged["category"] = category
    tagged.setdefault("stock_status", None)
    tagged.setdefault("image_url", None)
    tagged.setdefault("is_cached", False)
    tagged.setdefault("previous_price", None)
    tagged.setdefault("price_change", None)
    tagged.setdefault("price_change_percent", None)
    tagged.setdefault("price_trend", None)
    tagged.setdefault("first_seen_at", None)
    tagged.setdefault("lowest_price", None)
    tagged.setdefault("highest_price", None)
    return tagged


def recent_disappeared_deals(
    history: dict[str, Any],
    current_keys: set[str],
    error_sources: set[str],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    items = history.get("items", {})
    if not isinstance(items, dict):
        return []

    disappeared = []
    for key, item in items.items():
        if key in current_keys or not isinstance(item, dict):
            continue
        source = str(item.get("source") or "")
        if source in error_sources:
            continue
        title = clean_text(str(item.get("title") or ""))
        url = clean_text(str(item.get("url") or ""))
        current = money(item.get("current_price"))
        last_seen_at = str(item.get("last_seen_at") or "")
        if not title or not url or current is None or not last_seen_at:
            continue
        disappeared.append(
            {
                "title": title,
                "url": url,
                "source": source,
                "current_price": current,
                "last_seen_at": last_seen_at,
            }
        )

    return sorted(disappeared, key=lambda item: item["last_seen_at"], reverse=True)[:limit]


def buy_zone(deal: dict[str, Any]) -> tuple[str, str]:
    price = money(deal.get("current_price")) or 0
    discount = float(deal.get("discount_percent") or 0)
    trend = str(deal.get("price_trend") or "")
    category = str(deal.get("category") or "ski")
    lowest = money(deal.get("lowest_price"))

    if trend == "down" and lowest is not None and price <= lowest:
        return "New low", "zone-new-low"
    if discount >= 70 or (category == "ski" and price <= 250 and discount >= 45):
        return "Buy zone", "zone-buy"
    if discount >= 55 or (category == "clothing" and price <= 50 and discount >= 45):
        return "Strong deal", "zone-strong"
    if trend == "up":
        return "Going up", "zone-watch"
    return "Fair deal", "zone-fair"


def is_lowest_seen(deal):
    return bool(deal.get('is_lowest_seen'))



def is_sweet_spot(deal):
    return bool(deal.get('verified_fit') and deal.get('matches_preferences'))



def deal_verdict(deal):
    return (deal.get('verdict', 'Check details'), 'verdict-buy' if deal.get('act_now_eligible') else 'verdict-look')



def duplicate_key(deal):
    from deal_rules import normalized_product
    return normalized_product(deal)



def cross_store_annotations(deals):
    from deal_rules import comparisons
    return comparisons(deals)



def deal_price_series(history_items: dict[str, Any], deal: dict[str, Any]) -> list[float]:
    item = history_items.get(price_history_key(deal))
    if not isinstance(item, dict):
        return []
    observations = item.get("observations")
    if not isinstance(observations, list):
        return []
    prices = [money(obs.get("price")) for obs in observations if isinstance(obs, dict)]
    return [price for price in prices if price is not None]


def sparkline_svg(prices: list[float], width: int = 88, height: int = 26) -> str:
    if len(prices) < 2:
        return ""
    lo, hi = min(prices), max(prices)
    span = (hi - lo) or 1.0
    pad = 2.5
    step = (width - 2 * pad) / (len(prices) - 1)
    points = " ".join(
        f"{pad + index * step:.1f},{pad + (height - 2 * pad) * (1 - (price - lo) / span):.1f}"
        for index, price in enumerate(prices)
    )
    if hi == lo:
        color = "#9aa6a0"
    elif prices[-1] <= prices[0]:
        color = "#1f6f43"  # trending down = good
    else:
        color = "#b3422f"
    last_x = pad + (len(prices) - 1) * step
    last_y = pad + (height - 2 * pad) * (1 - (prices[-1] - lo) / span)
    return (
        f"<svg class='spark' viewBox='0 0 {width} {height}' width='{width}' height='{height}' role='img'>"
        f"<title>{len(prices)} checks: ${lo:.0f}-${hi:.0f}</title>"
        f"<polyline points='{points}' fill='none' stroke='{color}' stroke-width='1.5' />"
        f"<circle cx='{last_x:.1f}' cy='{last_y:.1f}' r='2' fill='{color}' /></svg>"
    )


def short_seen_label(value: str) -> str:
    if not value:
        return "last run"
    try:
        seen = datetime.fromisoformat(value)
    except ValueError:
        return value[:10]
    return seen.strftime("%b %-d")


def source_health_card(source: str, deals: list[dict[str, Any]], count: int, error: str | None) -> str:
    source_deals = [deal for deal in deals if str(deal.get("source")) == source]
    cached = sum(1 for deal in source_deals if deal.get("is_cached"))
    photos = sum(1 for deal in source_deals if deal.get("image_url"))
    drops = sum(1 for deal in source_deals if deal.get("price_trend") == "down")
    if error:
        status = "Issue"
        status_class = "health-issue"
        detail = error
    elif cached:
        status = "Cached"
        status_class = "health-cached"
        detail = f"{cached} cached listing{'s' if cached != 1 else ''}"
    elif count:
        status = "Live"
        status_class = "health-live"
        detail = f"{count} deals - {photos} photos - {drops} drops"
    else:
        status = "Quiet"
        status_class = "health-quiet"
        detail = "No matching deals this run"

    return f"""
    <div class="health-card {status_class}">
      <strong>{html.escape(source)}</strong>
      <span>{html.escape(status)}</span>
      <p>{html.escape(detail)}</p>
    </div>
    """


def load_preferences(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def preference_terms(preferences: dict[str, Any], key: str) -> list[str]:
    values = preferences.get(key)
    if not isinstance(values, list):
        return []
    return [str(value).strip().lower() for value in values if str(value).strip()]


def preference_numbers(preferences: dict[str, Any], key: str) -> list[int]:
    values = preferences.get(key)
    if not isinstance(values, list):
        return []
    numbers = []
    for value in values:
        try:
            numbers.append(int(value))
        except (TypeError, ValueError):
            continue
    return numbers


def annotate_preferences(deals, preferences):
    from deal_rules import enrich
    enrich(deals, preferences)



def matches_preferred_size(category, sizes, ski_sizes, clothing_sizes):
    from deal_rules import size_match
    return size_match(category, sizes, ski_sizes, clothing_sizes)



def preference_summary(preferences: dict[str, Any], deals: list[dict[str, Any]]) -> dict[str, Any]:
    watch_terms = preference_terms(preferences, "watch_terms")
    muted_terms = preference_terms(preferences, "muted_terms")
    my_ski_sizes = preference_numbers(preferences, "my_ski_sizes")
    family_ski_sizes = preference_numbers(preferences, "family_ski_sizes")
    if not my_ski_sizes and not family_ski_sizes:
        my_ski_sizes = preference_numbers(preferences, "ski_sizes")
    clothing_sizes = preference_terms(preferences, "clothing_sizes")
    return {
        "watch_terms": watch_terms,
        "muted_terms": muted_terms,
        "my_ski_sizes": my_ski_sizes,
        "family_ski_sizes": family_ski_sizes,
        "ski_sizes": sorted(set(my_ski_sizes + family_ski_sizes)),
        "clothing_sizes": clothing_sizes,
        "watchlist_count": sum(1 for deal in deals if deal.get("is_watchlist")),
        "muted_count": sum(1 for deal in deals if deal.get("is_muted")),
        "my_size_match_count": sum(1 for deal in deals if deal.get("matches_my_size")),
        "family_size_match_count": sum(1 for deal in deals if deal.get("matches_family_size")),
        "size_match_count": sum(1 for deal in deals if deal.get("matches_size")),
        "preference_match_count": sum(1 for deal in deals if deal.get("matches_preferences")),
    }


def report_title(config: dict[str, Any]) -> str:
    return str(config.get("report_title") or "Ski Gear Deals")


def empty_message(config: dict[str, Any]) -> str:
    fallback = "No matching deals found. Add or enable more sources in the config."
    return str(config.get("empty_message") or fallback)


def render_markdown(payload: dict[str, Any], config: dict[str, Any]) -> str:
    lines = [
        f"# {report_title(config)}",
        "",
        f"Generated: {payload['generated_at']}",
        f"Deals found: {payload['deal_count']}",
        "",
    ]

    if not payload["deals"]:
        lines.append(empty_message(config))
    else:
        for index, deal in enumerate(payload["deals"][:25], start=1):
            discount = f" ({deal['discount_percent']}% off)" if deal["discount_percent"] else ""
            original = f" was ${deal['original_price']:.2f}" if deal["original_price"] else ""
            trend = price_trend_label(deal)
            status = stock_label(deal.get("stock_status"))
            lines.extend(
                [
                    f"{index}. [{deal['title']}]({deal['url']})",
                    f"   ${deal['current_price']:.2f}{original}{discount} - {deal['source']}",
                    f"   Price trend: {trend}" if trend else "",
                    f"   Sizes: {', '.join(deal['sizes'])}" if deal.get("sizes") else "",
                    f"   Stock: {status}" if status else "",
                    "",
                ]
            )

    if payload["errors"]:
        lines.extend(["", "## Source Errors", ""])
        for error in payload["errors"]:
            lines.append(f"- {error['source']}: {error['error']}")

    return "\n".join(lines).strip() + "\n"


def render_html(payload, config):
    from deal_dashboard import render_dashboard
    return render_dashboard(payload, config)



def brief_panel_html() -> str:
    """Inline the latest Claude morning brief (if one exists) into the report."""
    try:
        brief = (DATA_DIR / "deal_brief.md").read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    if not brief:
        return ""
    try:
        from deal_analyst import markdown_to_html

        body = markdown_to_html(brief)
    except ImportError:
        body = f"<pre>{html.escape(brief)}</pre>"
    return f"""
          <details class="brief-panel" open>
            <summary><strong>Morning brief</strong><span class="meta">Claude's take on today's deals</span></summary>
            <div class="brief-body">{body}</div>
          </details>
    """


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitor configured URLs for ski gear deals.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--rerender",
        action="store_true",
        help="rebuild the HTML reports from the existing JSON data without scraping (used after the brief updates)",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.rerender:
        json_output = resolve_output_path(config.get("json_output"), JSON_OUTPUT)
        payload = load_json_payload(json_output)
        if not payload:
            print(f"No payload at {json_output}; run a scrape first.", file=sys.stderr)
            return 1
        html_output_path = resolve_output_path(config.get("html_output"), HTML_OUTPUT)
        web_output = resolve_output_path(config.get("web_output"), WEB_OUTPUT)
        html_payload, html_config = combined_tracker_payload(payload, config)
        html_output = trim_trailing_whitespace(render_html(html_payload, html_config))
        html_output_path.parent.mkdir(parents=True, exist_ok=True)
        web_output.parent.mkdir(parents=True, exist_ok=True)
        html_output_path.write_text(html_output, encoding="utf-8")
        web_output.write_text(html_output, encoding="utf-8")
        print(f"Wrote {html_output_path}")
        print(f"Wrote {web_output}")
        return 0

    deals, errors = scan(config)
    write_outputs(deals, errors, config)

    json_output = resolve_output_path(config.get("json_output"), JSON_OUTPUT)
    html_output = resolve_output_path(config.get("html_output"), HTML_OUTPUT)
    web_output = resolve_output_path(config.get("web_output"), WEB_OUTPUT)
    markdown_output = resolve_output_path(config.get("markdown_output"), MD_OUTPUT)
    history_output = resolve_output_path(config.get("price_history_output"), PRICE_HISTORY_OUTPUT)

    print(f"Checked {len([s for s in config.get('sources', []) if s.get('enabled', True)])} sources.")
    print(f"Found {len(deals)} matching deals.")
    print(f"Wrote {json_output}")
    print(f"Wrote {html_output}")
    print(f"Wrote {web_output}")
    print(f"Wrote {markdown_output}")
    print(f"Wrote {history_output}")
    if errors:
        print(f"{len(errors)} source(s) had errors.", file=sys.stderr)
    return 0 if deals or not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
