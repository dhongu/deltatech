# Part of Terrabit. See LICENSE file for full copyright and licensing details.

from contextlib import contextmanager
from unittest.mock import patch

FETCH = "odoo.addons.deltatech_web_scan.utils.fetch"

PUBLIC_IP = "93.184.215.14"
DNS = {
    "shop.example": {PUBLIC_IP},
    "other.example": {PUBLIC_IP},
    "localhost": {"127.0.0.1"},
    "internal.example": {"10.1.2.3"},
    "mixed.example": {PUBLIC_IP, "192.168.1.10"},
    "metadata.example": {"169.254.169.254"},
    "v6local.example": {"::1"},
    "mapped.example": {"::ffff:127.0.0.1"},
}


def fake_dns(host, port):
    if host not in DNS:
        raise OSError("unknown host")
    return DNS[host]


class FakeResponse:
    def __init__(self, text="", status=200, location=None, content_type="text/html; charset=utf-8", content=None):
        self.content = content if content is not None else text.encode("utf-8")
        self.status_code = status
        self.headers = {"content-type": content_type}
        if location:
            self.headers["location"] = location
        self.is_redirect = bool(location)
        self.encoding = "utf-8"

    def iter_content(self, size):
        for i in range(0, len(self.content), size):
            yield self.content[i : i + size]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@contextmanager
def fake_web(pages=None, robots=None):
    """Replace DNS and network: ``pages`` maps an address to a ``FakeResponse`` (or a text); an address
    not listed answers 404; ``robots`` maps a site (``https://shop.example``) to its robots.txt

    :return: the list of the addresses requested
    """
    from ..utils.fetch import clear_caches

    calls = []
    pages = dict(pages or {})
    for base, text in (robots or {}).items():
        pages[base + "/robots.txt"] = FakeResponse(text, content_type="text/plain")

    def _get(session, url, **kwargs):
        calls.append(url)
        page = pages.get(url)
        if page is None:
            return FakeResponse("not found", status=404)
        return FakeResponse(page) if isinstance(page, str) else page

    clear_caches()
    with (
        patch(f"{FETCH}._resolve_host_ips", side_effect=fake_dns),
        patch(f"{FETCH}._http_get", side_effect=_get),
        patch(f"{FETCH}.time.sleep"),
    ):
        yield calls
    clear_caches()


PRODUCT_PAGE = """<html><head>
<script type="application/ld+json">
{"@context": "https://schema.org", "@graph": [
  {"@type": "BreadcrumbList", "itemListElement": []},
  {"@type": "Product", "name": "Printer M3100", "sku": "M3100-ADNW", "mpn": "M3100ADNW",
   "gtin13": "5901234123457", "brand": {"@type": "Brand", "name": "Samsung"},
   "image": ["/img/m3100.jpg", {"@type": "ImageObject", "contentUrl": "https://cdn.example/m3100-2.jpg"}],
   "offers": [
     {"@type": "Offer", "price": "1.199,00", "priceCurrency": "ron", "availability": "https://schema.org/OutOfStock"},
     {"@type": "Offer", "price": 1249.5, "priceCurrency": "RON", "availability": "http://schema.org/InStock"}
   ]}
]}
</script>
<meta property="og:image" content="https://shop.example/og.jpg"/>
</head><body><h1>Printer M3100</h1></body></html>"""
