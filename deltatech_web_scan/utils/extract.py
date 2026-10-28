# Part of Terrabit. See LICENSE file for full copyright and licensing details.
"""What a product page declares: schema.org ``Product`` (JSON-LD and Microdata), Open Graph images,
values found by configured selectors, and the price found by the usual HTML patterns, as a last resort."""

import json
import logging
import re
from urllib.parse import urljoin, urlsplit

from lxml import etree
from lxml import html as lxml_html

from .codes import is_valid_gtin, normalize_gtin, parse_price

_logger = logging.getLogger(__name__)

try:
    import extruct
except ImportError:  # pragma: no cover - declared in the manifest; without it only JSON-LD is read
    extruct = None

try:
    from lxml.cssselect import CSSSelector
except ImportError:  # pragma: no cover - cssselect is optional
    CSSSelector = None

GTIN_KEYS = ("gtin13", "gtin", "gtin12", "gtin14", "gtin8", "ean")
MAX_IMAGES = 8
AVAILABILITY = {
    "instock": "in_stock",
    "instoreonly": "in_stock",
    "onlineonly": "in_stock",
    "limitedavailability": "limited",
    "outofstock": "out_of_stock",
    "soldout": "out_of_stock",
    "preorder": "preorder",
    "presale": "preorder",
    "backorder": "preorder",
    "madetoorder": "preorder",
    "discontinued": "discontinued",
}
SELECTOR_TYPES = ("xpath", "css", "regex", "jsonld_path")
NOISE_TAGS = ("script", "style", "svg", "noscript", "template", "iframe")
# the classes of an old price: "old-price", "price_before", "pret-vechi"...
OLD_PRICE_RE = re.compile(r"(^|[\s_-])(old|strike|striked|was|before|regular|vechi|initial)([\s_-]|$)", re.I)


def _html_tree(page_html):
    try:
        return lxml_html.fromstring(page_html)
    except (ValueError, etree.ParserError):
        return None


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _types(node):
    types = node.get("@type") or node.get("type")
    names = []
    for value in _as_list(types):
        if isinstance(value, str):
            names.append(value.rstrip("/").rsplit("/", 1)[-1])
    return names


def _text(value):
    if isinstance(value, dict):
        value = value.get("name") or value.get("value") or value.get("@value")
    if isinstance(value, list):
        value = value[0] if value else None
    return str(value).strip() if isinstance(value, str | int | float) and str(value).strip() else ""


def _from_microdata(item):
    """:return: a Microdata item of extruct written like JSON-LD"""
    if not isinstance(item, dict):
        return item
    if "properties" not in item:
        return item
    node = {"@type": item.get("type")}
    for key, value in item["properties"].items():
        node[key] = [_from_microdata(v) for v in value] if isinstance(value, list) else _from_microdata(value)
    return node


def _products(node):
    """:return: the schema.org Product objects of a JSON-LD value, in the order of the page"""
    products = []
    if isinstance(node, list):
        for item in node:
            products += _products(item)
    elif isinstance(node, dict):
        types = _types(node)
        if "Product" in types or "ProductGroup" in types or "IndividualProduct" in types:
            products.append(node)
        for key in ("@graph", "hasVariant", "mainEntity", "itemListElement", "item"):
            if key in node:
                products += _products(node[key])
    return products


def _json_ld(tree):
    data = []
    for script in tree.xpath("//script[@type='application/ld+json']"):
        try:
            data.append(json.loads(script.text_content() or "null", strict=False))
        except ValueError:
            continue
    return data


def _availability(value):
    value = _text(value)
    key = value.rstrip("/").rsplit("/", 1)[-1].replace("_", "").replace(" ", "").lower()
    return AVAILABILITY.get(key, "unknown")


def _offers(product):
    offers = []
    for offer in _as_list(product.get("offers")):
        if not isinstance(offer, dict):
            continue
        currency = _text(offer.get("priceCurrency")) or _text(product.get("priceCurrency"))
        availability = _availability(offer.get("availability"))
        price = offer.get("price")
        if price is None and isinstance(offer.get("priceSpecification"), dict | list):
            spec = _as_list(offer["priceSpecification"])[0]
            price = spec.get("price") if isinstance(spec, dict) else None
            currency = currency or (_text(spec.get("priceCurrency")) if isinstance(spec, dict) else "")
        if price is None and "AggregateOffer" in _types(offer):
            price = offer.get("lowPrice")
        price = parse_price(_text(price) if not isinstance(price, int | float) else price, structured=True)
        if price is not None and price > 0:
            offers.append({"price": price, "currency": currency.upper(), "availability": availability})
        # an AggregateOffer may list its offers
        if "AggregateOffer" in _types(offer) and offer.get("offers"):
            offers += _offers({"offers": offer["offers"], "priceCurrency": currency})
    if not offers and product.get("price") is not None:
        price = parse_price(_text(product["price"]), structured=True)
        if price:
            offers.append(
                {"price": price, "currency": _text(product.get("priceCurrency")).upper(), "availability": "unknown"}
            )
    return offers


def _images(product, page_url):
    images = []
    for item in _as_list(product.get("image")):
        if isinstance(item, dict):
            item = item.get("contentUrl") or item.get("url")
        if isinstance(item, str) and item.strip():
            url = urljoin(page_url, item.strip())
            if urlsplit(url).scheme in ("http", "https") and url not in images:
                images.append(url)
    return images


def _product(node, page_url):
    """:return: the data of a schema.org Product useful to a catalogue"""
    gtins = []
    for key in GTIN_KEYS:
        code = normalize_gtin(_text(node.get(key)))
        if code and code not in gtins:
            gtins.append(code)
    weight = node.get("weight")
    if isinstance(weight, dict):
        weight = (weight.get("value"), weight.get("unitCode") or weight.get("unitText"))
    elif weight is not None:
        weight = (weight, None)
    return {
        "name": _text(node.get("name")),
        "description": _text(node.get("description")),
        "brand": _text(node.get("brand")),
        "sku": _text(node.get("sku")),
        "mpn": _text(node.get("mpn")),
        "gtins": gtins,
        "gtin": next((g for g in gtins if is_valid_gtin(g)), ""),
        "url": urljoin(page_url, _text(node.get("url"))) if _text(node.get("url")) else page_url,
        "images": _images(node, page_url),
        "offers": _offers(node),
        "weight": weight,
    }


def extract_structured(page_html, page_url=""):
    """:return: the products declared by the page with schema.org (JSON-LD, then Microdata), as dictionaries:
    ``name``, ``description``, ``brand``, ``sku``, ``mpn``, ``gtins``, ``gtin`` (the first valid one),
    ``url``, ``images``, ``offers`` (``price``, ``currency``, ``availability``), ``weight``"""
    nodes = []
    if extruct is not None:
        try:
            data = extruct.extract(
                page_html, base_url=page_url or None, syntaxes=["json-ld", "microdata"], uniform=False
            )
        except Exception:  # noqa: BLE001 - a broken page must not stop the reading
            _logger.debug("extruct could not read %s", page_url, exc_info=True)
            data = {}
        nodes += _products(data.get("json-ld") or [])
        nodes += _products([_from_microdata(item) for item in data.get("microdata") or []])
    if not nodes:
        tree = _html_tree(page_html)
        if tree is not None:
            nodes = _products(_json_ld(tree))
    return [_product(node, page_url) for node in nodes]


def best_offer(product, prefer_in_stock=True):
    """:return: the offer with the lowest price, among those in stock when there are some, or None"""
    offers = (product or {}).get("offers") or []
    if prefer_in_stock:
        in_stock = [o for o in offers if o["availability"] in ("in_stock", "limited")]
        offers = in_stock or offers
    return min(offers, key=lambda o: o["price"]) if offers else None


def extract_images(page_html, page_url):
    """:return: the absolute addresses of the images the page declares: schema.org first, then Open Graph,
    Twitter card and ``image_src``"""
    tree = _html_tree(page_html)
    if tree is None:
        return []
    urls = [url for product in extract_structured(page_html, page_url) for url in product["images"]]
    urls += tree.xpath(
        "//meta[@property='og:image:secure_url' or @property='og:image' or @name='twitter:image']/@content"
    )
    urls += tree.xpath("//link[@rel='image_src']/@href")
    result = []
    for url in urls:
        url = urljoin(page_url, url.strip())
        if urlsplit(url).scheme in ("http", "https") and url not in result:
            result.append(url)
    return result[:MAX_IMAGES]


def _node_value(node, attribute):
    if isinstance(node, str):
        return node.strip()
    if attribute:
        return (node.get(attribute) or "").strip()
    return " ".join(node.text_content().split())


def _jsonld_path(products, path):
    """:return: the value at a dotted path (``offers.price``, ``offers.0.price``) of the first JSON-LD product"""
    value = products[0] if products else None
    for key in path.split("."):
        if isinstance(value, list):
            if key.isdigit():
                value = value[int(key)] if int(key) < len(value) else None
                continue
            value = value[0] if value else None
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return _text(value)


def extract_by_selectors(page_html, selectors, page_url=""):
    """:return: ``{target: value}`` read with the configured selectors

    :param selectors: dictionaries with ``target``, ``type`` (``xpath``, ``css``, ``regex``,
        ``jsonld_path``), ``expression``, optionally ``attribute`` (else the text of the node) and
        ``value_map`` (``{text found: value}``); the first selector of a target that gives a value wins
    """
    tree = _html_tree(page_html)
    raw_products = None
    result = {}
    for selector in selectors or []:
        target, kind, expression = selector.get("target"), selector.get("type"), selector.get("expression")
        if not target or not expression or target in result:
            continue
        values = []
        try:
            if kind == "xpath" and tree is not None:
                values = tree.xpath(expression)
            elif kind == "css" and tree is not None:
                if CSSSelector is None:
                    raise ValueError("the Python library cssselect is needed for CSS selectors")
                values = CSSSelector(expression)(tree)
            elif kind == "regex":
                match = re.search(expression, page_html, re.S)
                values = [match.group(1) if match and match.groups() else match.group(0)] if match else []
            elif kind == "jsonld_path":
                if raw_products is None:
                    raw_products = _products(_json_ld(tree)) if tree is not None else []
                value = _jsonld_path(raw_products, expression)
                values = [value] if value else []
        except (etree.XPathError, re.error, ValueError) as e:
            _logger.info("Selector %s %r failed: %s", kind, expression, e)
            continue
        values = values if isinstance(values, list) else [values]
        for node in values:
            value = _node_value(node, selector.get("attribute")) if not isinstance(node, int | float) else str(node)
            if not value:
                continue
            value_map = selector.get("value_map") or {}
            if value_map:
                value = next((v for k, v in value_map.items() if k.lower() in value.lower()), value)
            if target in ("image",) and page_url:
                value = urljoin(page_url, value)
            result[target] = value
            break
    return result


def _is_old_price(node):
    """:return: True for a node of an old, struck through price (or inside one)"""
    if node is None or not isinstance(node.tag, str):
        return False
    if node.xpath("ancestor-or-self::del | ancestor-or-self::s | ancestor-or-self::strike"):
        return True
    return any(OLD_PRICE_RE.search(cls or "") for cls in node.xpath("ancestor-or-self::*/@class"))


def extract_price_heuristic(page_html):
    """:return: the price found by the usual HTML patterns (meta ``product:price:amount``, ``itemprop=price``,
    an element whose class says price), or None; the old, struck through prices are left out"""
    tree = _html_tree(page_html)
    if tree is None:
        return None
    candidates = tree.xpath("//meta[@property='product:price:amount' or @property='og:price:amount']/@content")
    candidates += tree.xpath("//*[@itemprop='price']/@content")
    for node in tree.xpath("//*[@itemprop='price'] | //*[contains(translate(@class, 'PRICE', 'price'), 'price')]"):
        if _is_old_price(node):
            continue
        texts = [t for t in node.xpath(".//text()") if not _is_old_price(t.getparent())]
        candidates.append(node.get("data-price") or " ".join(texts))
    for candidate in candidates:
        price = parse_price(candidate)
        if price:
            return price
    return None


def page_text(page_html, limit=None):
    """:return: the visible text of the page, without scripts, styles, SVG and comments, the spaces collapsed"""
    tree = _html_tree(page_html)
    if tree is None:
        return ""
    for node in tree.xpath("//" + " | //".join(NOISE_TAGS) + " | //comment()"):
        if node.getparent() is not None:
            node.drop_tree()
    text = " ".join(" ".join(tree.itertext()).split())
    return text[:limit] if limit else text
