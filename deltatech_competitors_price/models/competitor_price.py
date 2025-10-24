# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import requests
    from lxml import html as lxml_html
except Exception:  # pragma: no cover - optional at runtime
    requests = None
    lxml_html = None

# extruct is optional; use it when available to parse JSON-LD/Microdata
try:  # pragma: no cover - optional at runtime
    import extruct
except Exception:  # pragma: no cover - optional at runtime
    extruct = None


class DeltatechCompetitorPrice(models.Model):
    _name = "deltatech.competitor.price"
    _description = "Competitor Price Tracking"
    _order = "competitor_name, id"

    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product",
        required=True,
        ondelete="cascade",
        index=True,
    )
    competitor_name = fields.Char(string="Competitor", required=True)
    product_url = fields.Char(string="Product URL")

    last_price = fields.Monetary(string="Last Price")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
    )
    last_fetch = fields.Datetime(string="Last Fetch")
    fetch_status = fields.Text(string="Fetch Status")

    auto_fetch = fields.Boolean(string="Auto Fetch", help="Include in scheduled fetch")

    def _extract_price_from_structured_data(self, html_text, base_url=None):
        """
        Use extruct to extract JSON-LD and Microdata and find a product price.
        Returns (price: float|None, currency: str|None)
        """
        if not extruct:
            return None, None
        try:
            data = extruct.extract(html_text, syntaxes=["json-ld", "microdata"], base_url=base_url or "")
        except Exception:
            return None, None

        def as_list(val):
            if val is None:
                return []
            return val if isinstance(val, list) else [val]

        def is_type(obj, wanted):
            t = obj.get("@type") or obj.get("type")
            if not t:
                return False
            if isinstance(t, list):
                return wanted in t
            return t == wanted

        # JSON-LD first (usually richest)
        for item in as_list(data.get("json-ld")):
            # Some pages provide graph
            graph = as_list(item.get("@graph")) if isinstance(item, dict) else []
            nodes = graph or as_list(item)
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                if is_type(node, "Product"):
                    offers = as_list(node.get("offers"))
                    for offer in offers:
                        # Offer or AggregateOffer
                        currency = offer.get("priceCurrency") or node.get("priceCurrency")
                        price = offer.get("price")
                        if price is None and offer.get("@type") == "AggregateOffer":
                            price = offer.get("lowPrice") or offer.get("highPrice")
                        if price is not None:
                            try:
                                return float(str(price).replace(",", ".")), currency
                            except Exception:
                                continue
                    # Sometimes price embedded directly on product
                    if node.get("price"):
                        try:
                            return float(str(node.get("price")).replace(",", ".")), node.get("priceCurrency")
                        except Exception:
                            _logger.error("Error parsing price from JSON-LD")

        # Microdata fallback
        for item in as_list(data.get("microdata")):
            props = item.get("properties") if isinstance(item, dict) else None
            if not props:
                continue
            t = item.get("type")
            if isinstance(t, list):
                is_product = any("Product" in x for x in t)
            else:
                is_product = "Product" in (t or "")
            if not is_product:
                continue
            offers = as_list(props.get("offers"))
            for offer in offers:
                if isinstance(offer, dict):
                    oprops = offer.get("properties") or offer
                    currency = oprops.get("priceCurrency") or props.get("priceCurrency")
                    price = oprops.get("price") or oprops.get("lowPrice") or oprops.get("highPrice")
                    if price is not None:
                        try:
                            return float(str(price).replace(",", ".")), currency
                        except Exception:
                            continue
            # Direct price on product
            price = props.get("price")
            if price is not None:
                try:
                    return float(str(price).replace(",", ".")), props.get("priceCurrency")
                except Exception:
                    _logger.error("Error parsing price from Microdata")

        return None, None

    def _extract_price_from_tree(self, tree):
        # Try common selectors
        candidates = []
        # 1) meta price
        meta_price = tree.xpath("//meta[@property='product:price:amount']/@content")
        if meta_price:
            candidates.extend(meta_price)
        # 2) itemprop price
        itemprop_price = tree.xpath("//*[@itemprop='price']/@content | //*[@itemprop='price']/text()")
        if itemprop_price:
            candidates.extend(itemprop_price)
        # 3) elements with class containing price
        class_price = tree.xpath(
            "//*[contains(translate(@class, 'PRICE', 'price'), 'price')]/@data-price | //*[contains(translate(@class, 'PRICE', 'price'), 'price')]/text()"
        )
        if class_price:
            candidates.extend(class_price)
        # Clean and parse numbers
        for val in candidates:
            if not val:
                continue
            txt = (val if isinstance(val, str) else str(val)).strip()
            # Remove currency symbols and thousands separators, keep decimal separator
            # Replace comma decimal with dot if likely
            cleaned = (
                txt.replace("\xa0", " ")
                .replace("RON", "")
                .replace("lei", "")
                .replace("Lei", "")
                .replace("lei", "")
                .replace("€", "")
                .replace("EUR", "")
                .replace("$", "")
                .strip()
            )
            # Keep digits, dot and comma
            keep = "".join(ch for ch in cleaned if ch.isdigit() or ch in ",.")
            if keep.count(",") == 1 and keep.count(".") == 0:
                keep = keep.replace(",", ".")
            try:
                return float(keep)
            except Exception:
                continue
        return None

    def _do_fetch(self):
        self.ensure_one()
        if not self.product_url:
            raise UserError(_("No product URL on competitor line."))
        if requests is None or lxml_html is None:
            msg = "Missing requests/lxml libraries; cannot fetch."
            self.write(
                {
                    "fetch_status": msg,
                    "last_fetch": fields.Datetime.now(),
                }
            )
            return False
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            resp = requests.get(self.product_url, headers=headers, timeout=15)
            resp.raise_for_status()

            # First, try structured data (JSON-LD / Microdata) if extruct is available
            price = None
            currency_code = None
            try:
                price, currency_code = self._extract_price_from_structured_data(resp.text, base_url=self.product_url)
            except Exception:
                # Do not fail the fetch because of structured parsing
                price, currency_code = None, None

            # Fallback: parse HTML heuristically
            if price is None and lxml_html is not None:
                tree = lxml_html.fromstring(resp.content)
                price = self._extract_price_from_tree(tree)

            if price is None:
                status = _("Price not found on page")
                self.write(
                    {
                        "fetch_status": status,
                        "last_fetch": fields.Datetime.now(),
                    }
                )
                return False

            vals = {
                "last_price": price,
                "last_fetch": fields.Datetime.now(),
                "fetch_status": _("OK"),
            }
            if currency_code:
                Currency = self.env["res.currency"]
                currency = Currency.search([("name", "=", currency_code)], limit=1)
                if currency:
                    vals["currency_id"] = currency.id
            self.write(vals)
            return True
        except Exception as e:
            _logger.exception("Error fetching competitor price")
            self.write(
                {
                    "fetch_status": str(e),
                    "last_fetch": fields.Datetime.now(),
                }
            )
            return False

    def action_fetch_price(self):
        for rec in self:
            rec._do_fetch()
        return True


class ProductTemplate(models.Model):
    _inherit = "product.template"

    competitor_price_ids = fields.One2many(
        "deltatech.competitor.price",
        "product_tmpl_id",
        string="Competitor Prices",
    )

    def action_fetch_competitor_prices(self):
        for tmpl in self:
            tmpl.competitor_price_ids.action_fetch_price()
        return True
