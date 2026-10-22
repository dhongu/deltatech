# Part of Terrabit. See LICENSE file for full copyright and licensing details.
"""Scanning of one product page: reading, extraction and checks, without the database.

The outcome says what was found and how much it can be trusted; the module that uses it decides what to
write. The states:

- ``ok``: a price was found and passed the checks;
- ``suspect``: the price changed more than allowed since the previous reading, or it was read by AI;
- ``mismatch``: the page declares a barcode or a code different from the one expected;
- ``not_found``: the page has no price (or is gone);
- ``blocked``: robots.txt, protection against robots, too many requests;
- ``error``: the page could not be read.
"""

from collections import OrderedDict

from .codes import is_valid_gtin, normalize_gtin, parse_price, same_code, same_gtin
from .extract import best_offer, extract_by_selectors, extract_price_heuristic, extract_structured
from .fetch import domain_of, fetch

SELECTOR_TARGETS_FLOAT = ("price", "list_price", "purchase_price", "qty_available")


def _empty_product(url):
    keys = ("name", "description", "brand", "sku", "mpn", "gtin")
    return dict(dict.fromkeys(keys, ""), gtins=[], url=url, images=[], offers=[], weight=None)


def _check_identity(product, expected):
    """:return: the reason why the page shows another product than the one expected, or None"""
    expected = expected or {}
    gtin = normalize_gtin(expected.get("gtin"))
    page_gtins = [g for g in product.get("gtins") or [] if is_valid_gtin(g)]
    if gtin and page_gtins:
        if not any(same_gtin(gtin, g) for g in page_gtins):
            return f"barcode {page_gtins[0]} on the page, {gtin} expected"
        return None  # the same barcode: the codes do not matter any more
    code = expected.get("code")
    page_codes = [c for c in (product.get("sku"), product.get("mpn")) if c]
    if code and page_codes and not any(same_code(code, c, expected.get("strip_zeros")) for c in page_codes):
        return f"code {page_codes[0]} on the page, {code} expected"
    return None


def _merge_selectors(product, values):
    """Complete the structured data with the values read by the selectors"""
    for target, value in values.items():
        if target in SELECTOR_TARGETS_FLOAT:
            values[target] = parse_price(value)
    if values.get("price"):
        product["offers"] = [
            {
                "price": values["price"],
                "currency": (values.get("currency") or "").upper(),
                "availability": values.get("availability") or "unknown",
            }
        ]
    for key in ("name", "description", "brand", "sku", "mpn"):
        if values.get(key) and not product.get(key):
            product[key] = values[key]
    if values.get("gtin"):
        gtin = normalize_gtin(values["gtin"])
        if gtin and gtin not in product["gtins"]:
            product["gtins"].append(gtin)
            product["gtin"] = product.get("gtin") or (gtin if is_valid_gtin(gtin) else "")
    if values.get("image") and values["image"] not in product["images"]:
        product["images"].insert(0, values["image"])
    product["values"] = values


def scan_page(
    url,
    session=None,
    user_agent=None,
    respect_robots=True,
    delay=0,
    selectors=None,
    expected=None,
    previous_price=None,
    suspect_change_percent=None,
    allow_heuristic=True,
):
    """Read a product page and say what it shows

    :param selectors: the selectors of ``extract_by_selectors``, for the pages without schema.org data;
        their values complete the structured data, and their price replaces it
    :param expected: ``{"gtin": ..., "code": ..., "strip_zeros": bool}`` of the product the page should show
    :param previous_price: the price of the previous reading, for the check of the jump
    :param suspect_change_percent: the jump of price, in percent, from which the price is ``suspect``
    :return: a dictionary: ``state``, ``detail`` (technical, in English), ``source`` (``structured``,
        ``selector``, ``heuristic``), ``product`` (as ``extract_structured``, or None), ``offer``
        (the one retained, or None), ``url`` (the final address, after redirects), ``fetch`` (the ``FetchResult``)
    """
    outcome = {"state": "error", "detail": "", "source": False, "product": None, "offer": None, "url": url}
    result = fetch(url, session=session, user_agent=user_agent, respect_robots=respect_robots, delay=delay)
    outcome.update(fetch=result, url=result.url)
    if not result.ok:
        state = result.state if result.state in ("not_found", "blocked") else "error"
        outcome.update(state=state, detail=result.detail)
        return outcome

    html = result.text
    products = extract_structured(html, result.url)
    product = products[0] if products else _empty_product(result.url)
    source = "structured" if product["offers"] else False
    if selectors:
        values = extract_by_selectors(html, selectors, result.url)
        if values:
            _merge_selectors(product, values)
            if values.get("price"):
                source = "selector"
    if not product["offers"] and allow_heuristic:
        price = extract_price_heuristic(html)
        if price:
            product["offers"] = [{"price": price, "currency": "", "availability": "unknown"}]
            source = "heuristic"
    outcome.update(product=product, source=source)

    mismatch = _check_identity(product, expected)
    if mismatch:
        outcome.update(state="mismatch", detail=mismatch)
        return outcome
    offer = best_offer(product)
    outcome["offer"] = offer
    if not offer:
        outcome.update(state="not_found", detail="no price on the page")
        return outcome
    if previous_price and suspect_change_percent:
        change = abs(offer["price"] - previous_price) / previous_price * 100
        if change > suspect_change_percent:
            outcome.update(state="suspect", detail=f"price {previous_price} -> {offer['price']} ({change:.0f}%)")
            return outcome
    outcome["state"] = "ok"
    return outcome


def history_needs_new_interval(last_values, new_values, keys):
    """:return: True when a new interval of history must be opened (no previous one, or one of the
    compared values changed); False when the last interval is only extended"""
    if not last_values:
        return True
    for key in keys:
        old, new = last_values.get(key), new_values.get(key)
        if isinstance(old, float) or isinstance(new, float):
            if round(float(old or 0.0), 6) != round(float(new or 0.0), 6):
                return True
        elif (old or False) != (new or False):
            return True
    return False


def group_by_domain(items, url_getter):
    """:return: the items grouped by the domain of their address, in the order of their first appearance"""
    groups = OrderedDict()
    for item in items:
        groups.setdefault(domain_of(url_getter(item)), []).append(item)
    return groups
