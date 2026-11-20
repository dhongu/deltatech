# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

import logging
import re
import xml.etree.ElementTree as ET

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import SQL

_logger = logging.getLogger(__name__)
NS = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


class AccountUblImportMixin(models.AbstractModel):
    """UBL invoice reading and matching shared by the import wizards: the purchase order
    wizard (deltatech_purchase_ubl) and the vendor bill review. It holds no state, no view
    and no behavior of its own; it only depends on account."""

    _name = "account.ubl.import.mixin"
    _description = "UBL invoice parsing and product matching"

    # ------------------------------------------------------------
    # Units, currency, products
    # ------------------------------------------------------------
    def _resolve_currency(self, code):
        """Resolve a currency by ISO code or fall back to the company currency.
        Always returns a valid res.currency record.
        """
        Currency = self.env["res.currency"]
        name = (code or "").upper()
        cur = Currency.search([("name", "=", name)], limit=1)
        if not cur:
            # Fallback to company currency to avoid null constraint errors
            cur = self.env.company.currency_id
        return cur

    _SET_UNIT_CODES = ("SET",)
    _SET_UNIT_NAMES = ("Set", "Sets", "Seturi")

    def _uom_from_code(self, unit_code, fallback=True):
        """Resolve a uom.uom record from a unit code/text found in the source document.
        Covers both UBL unitCode enum values (C62, KGM, ...) and common Romanian
        text units used on vendor-specific PDF layouts (Buc, Kg, L, ...).
        With fallback=False an empty or unknown code returns an empty recordset
        instead of Units, so callers can tell "unknown unit" from "pieces".
        """
        code = (unit_code or "").strip().upper()
        xml_ids = {
            # pieces / units
            "C62": "uom.product_uom_unit",
            "H87": "uom.product_uom_unit",
            "PCE": "uom.product_uom_unit",
            "EA": "uom.product_uom_unit",
            "BUC": "uom.product_uom_unit",
            "DZN": "uom.product_uom_dozen",
            # weight
            "KGM": "uom.product_uom_kgm",
            "KG": "uom.product_uom_kgm",
            "GRM": "uom.product_uom_gram",
            "G": "uom.product_uom_gram",
            "TNE": "uom.product_uom_ton",
            # volume
            "LTR": "uom.product_uom_litre",
            "L": "uom.product_uom_litre",
            "MLT": "uom.product_uom_milliliter",
            "MTQ": "uom.product_uom_cubic_meter",
            # length / area
            "MTR": "uom.product_uom_meter",
            "M": "uom.product_uom_meter",
            "CMT": "uom.product_uom_cm",
            "MMT": "uom.product_uom_millimeter",
            "MTK": "uom.product_uom_square_meter",
            # time
            "HUR": "uom.product_uom_hour",
            "DAY": "uom.product_uom_day",
        }
        xid = xml_ids.get(code)
        if xid:
            rec = self.env.ref(xid, raise_if_not_found=False)
            if rec:
                return rec
        if code in self._SET_UNIT_CODES:
            # Odoo has no standard "set" unit: use one defined in the database, if any
            Uom = self.env["uom.uom"]
            for name in self._SET_UNIT_NAMES:
                rec = Uom.search([("name", "=ilike", name)], limit=1)
                if rec:
                    return rec

        if not fallback:
            return self.env["uom.uom"]
        return self.env.ref("uom.product_uom_unit", raise_if_not_found=True)

    def _source_uom(self, src_ln):
        """Unit of a source line, or an empty recordset when the code is missing/unknown
        (the quantity and price are then assumed to be in the destination unit)."""
        return self._uom_from_code(src_ln.get("unit_code"), fallback=False)

    def _source_uom_compatible(self, src_uom, target_uom):
        return bool(src_uom and target_uom and src_uom._has_common_reference(target_uom))

    def _convert_source_line(self, src_ln, target_uom, uom_warnings=None):
        """Return (qty, price) of a source line expressed in target_uom.

        The source quantity/price are in the unit of the source document (UBL unitCode);
        they are converted when that unit is known and shares a reference with target_uom.
        An unknown unit keeps the values as they are; an incompatible unit keeps them too
        and records a warning, since no meaningful conversion exists.
        """
        qty = src_ln.get("qty")
        price = src_ln.get("price")
        src_uom = self._source_uom(src_ln)
        unit_code = (src_ln.get("unit_code") or "").strip()
        if not src_uom and unit_code and target_uom and uom_warnings is not None:
            uom_warnings.append(
                self.env._(
                    "Warning: unit %(code)s of source line %(line)s is not known; "
                    "quantity and price were taken as %(target)s.",
                    code=unit_code,
                    line=src_ln.get("code") or src_ln.get("name") or "/",
                    target=target_uom.name,
                )
            )
        if not src_uom or not target_uom or src_uom == target_uom:
            return qty, price
        if not self._source_uom_compatible(src_uom, target_uom):
            if uom_warnings is not None:
                uom_warnings.append(
                    self.env._(
                        "Warning: unit %(src)s of source line %(line)s is not compatible with %(target)s; "
                        "quantity and price were kept unconverted.",
                        src=src_uom.name,
                        line=src_ln.get("code") or src_ln.get("name") or "/",
                        target=target_uom.name,
                    )
                )
            return qty, price
        if qty:
            qty = src_uom._compute_quantity(qty, target_uom, rounding_method="HALF-UP")
        if price:
            price = src_uom._compute_price(price, target_uom)
        return qty, price

    def _prepare_product_from_xml_line(self, line_vals):
        """Values of the product created for an unmatched invoice line. A goods product
        here; the purchase flow, which has stock, makes it storable."""
        name = (line_vals.get("name") or line_vals.get("code") or "New Product").strip()
        barcode = (line_vals.get("barcode") or "").strip() or False
        uom = self._uom_from_code(line_vals.get("unit_code"))
        return {
            "name": name,
            "type": "consu",
            "purchase_ok": True,
            "sale_ok": False,
            "barcode": barcode,
            "uom_id": uom.id,
        }

    def _create_product_from_xml_line(self, supplier, line_vals, currency):
        """Create a product based on an invoice line and link supplierinfo.
        - supplier: res.partner (vendor)
        - line_vals: dict with keys code, barcode, name, unit_code, price
        - currency: code like RON/EUR
        Returns product.product record.
        """
        SupplierInfo = self.env["product.supplierinfo"]
        code = (line_vals.get("code") or "").strip() or False
        product = self.env["product.product"].create(self._prepare_product_from_xml_line(line_vals))
        # Create supplierinfo with provided vendor code and price
        cur = self._resolve_currency(currency)
        SupplierInfo.create(
            {
                "partner_id": supplier.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": code or False,
                "price": line_vals.get("price") or 0.0,
                "currency_id": cur.id,
                "delay": 1,
            }
        )
        return product

    @api.model
    def _normalize_vat(self, vat):
        """Comparable form of a VAT number: upper case, letters and digits only, and a Romanian
        CUI without its RO prefix, since "12345678", "RO12345678" and "ro 12345678" are the
        same company. Other countries keep their prefix."""
        vat = re.sub(r"[^0-9A-Z]", "", (vat or "").upper())
        if vat.startswith("RO") and vat[2:].isdigit():
            vat = vat[2:]
        return vat

    def _find_supplier_partner(self, supplier_vat, supplier_name):
        Partner = self.env["res.partner"]
        supplier_name = (supplier_name or "").strip()

        partner = False
        vat_key = self._normalize_vat(supplier_vat)
        if vat_key:
            candidates = Partner.search([("supplier_rank", ">", 0), ("vat", "ilike", vat_key)], limit=50)
            partner = candidates.filtered(lambda p: self._normalize_vat(p.vat) == vat_key)[:1]

        if not partner and supplier_name:
            partner = Partner.search(
                [("supplier_rank", ">", 0), ("name", "=ilike", supplier_name)],
                limit=1,
            )

        return partner

    def _match_product(self, supplier, code, name, barcode=None):
        return self._match_product_detailed(supplier, code, name, barcode=barcode)[0]

    def _match_product_detailed(self, supplier, code, name, barcode=None):
        """Same matching as _match_product, but also reports HOW the product was found:
        ("code" - supplier code/internal reference, "barcode", "name", or False when no
        match). The match type feeds the wizard preview, where code/barcode matches are
        trustworthy (green), name matches deserve a human look (yellow) and unmatched
        lines would spawn a new product (red)."""
        Product = self.env["product.product"]
        SupplierInfo = self.env["product.supplierinfo"]
        code = (code or "").strip()
        barcode = (barcode or "").strip()

        # Try explicit barcode from source document first
        if barcode:
            product = Product.search([("barcode", "=", barcode)], limit=1)
            if product:
                return product, "barcode"

        if supplier and code:
            domain = [("partner_id", "=", supplier.id), ("product_code", "=ilike", code)]
            sinfo = SupplierInfo.search(domain, limit=1)
            if sinfo:
                product = sinfo.product_id or sinfo.product_tmpl_id.product_variant_id
                if product:
                    return product, "code"

        if supplier and name:
            domain = [("partner_id", "=", supplier.id), ("product_name", "=ilike", name)]
            sinfo = SupplierInfo.search(domain, limit=1)
            if sinfo:
                product = sinfo.product_id or sinfo.product_tmpl_id.product_variant_id
                if product:
                    return product, "name"

        if code:
            product = Product.search([("default_code", "=ilike", code)], limit=1)
            if product:
                return product, "code"

        # Fallback: sometimes supplier code is actually barcode digits
        if code and code.isdigit():
            product = Product.search([("barcode", "=", code)], limit=1)
            if product:
                return product, "barcode"
        if name:
            products = Product.search([("name", "=ilike", name)], limit=2)
            if len(products) == 1:
                return products[0], "name"

        if name:
            product_template = self._match_template_by_name_without_spaces(name)
            if product_template:
                return product_template.product_variant_id, "name"

        return Product.browse(), False

    def _match_template_by_name_without_spaces(self, name):
        """The product template whose name equals ``name`` once spaces and case are left
        out (UBL-010), or an empty recordset when there is none or more than one.

        The name is read in the user's language, falling back to English: a product
        created in English has no translation in the user's language. The candidates
        go through the ORM, which leaves out archived products and those of other
        companies."""
        lang = self.env.context.get("lang") or self.env.user.lang or "en_US"
        self.env.cr.execute(
            SQL(
                "SELECT id FROM product_template"
                " WHERE lower(replace(COALESCE(name ->> %(lang)s, name ->> 'en_US'), ' ', '')) = %(name)s"
                " LIMIT 10",
                lang=lang,
                name=name.replace(" ", "").lower(),
            )
        )
        template_ids = [row[0] for row in self.env.cr.fetchall()]
        if not template_ids:
            return self.env["product.template"]
        templates = self.env["product.template"].search([("id", "in", template_ids)], limit=2)
        return templates if len(templates) == 1 else self.env["product.template"]

    def _update_supplier_price(self, supplier, product, code, price, currency, uom=False, company=None):
        """uom: unit of the source price. The price is converted to the unit of the
        existing vendor pricelist row; a new row is created in the source unit.

        Only a row of this variant (or, for a single-variant product, a row of the
        template) in this company or shared between companies is updated: a row of
        another variant or of another company is never repurposed."""
        SupplierInfo = self.env["product.supplierinfo"]
        company = company or self.env.company
        if product.product_tmpl_id.product_variant_count > 1:
            variant_domain = [("product_id", "=", product.id)]
        else:
            variant_domain = [("product_id", "in", [product.id, False])]
        sinfo = SupplierInfo.search(
            [
                ("partner_id", "=", supplier.id),
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
                ("company_id", "in", [company.id, False]),
                *variant_domain,
            ],
            order="product_id, company_id, sequence, min_qty, id",
            limit=1,
        )
        uom_vals = {}
        if uom:
            target_uom = sinfo.product_uom_id if sinfo else product.uom_id
            if self._source_uom_compatible(uom, target_uom):
                if sinfo:
                    price = uom._compute_price(price, target_uom) if price else price
                else:
                    uom_vals["product_uom_id"] = uom.id
        values = {
            "partner_id": supplier.id,
            "product_tmpl_id": product.product_tmpl_id.id,
            "product_id": product.id,
            "price": price,
            "currency_id": self._resolve_currency(currency).id,
            **uom_vals,
        }
        # a source line without a supplier code must not erase the code already on the row
        if code:
            values["product_code"] = code
        if sinfo:
            sinfo.write(values)
        else:
            values["company_id"] = company.id
            SupplierInfo.create(values)

    # Colored emoji keep the level visible wherever the log ends up: the chatter, the note of the
    # review activity, the plain-text log.
    _LOG_ICONS = {"success": "✅", "warning": "⚠️", "danger": "❌", "info": "ℹ️"}

    def _classify_message(self, msg):
        """Level of a message given as plain text, guessed from its English wording.

        Only a fallback for callers that still pass plain strings: once translated, the text
        no longer holds these words, so the log builders here pass (level, text) pairs."""
        m = msg.lower()
        if any(k in m for k in ("not created", "unmatched")):
            return "danger"
        if any(k in m for k in ("warning", "differs", "mismatch", "already exists", "skipped", "no receipt found")):
            return "warning"
        if any(k in m for k in ("total check ok", "updated", "added", "created", "receipt updated")):
            return "success"
        return "info"

    def _log_entries(self, messages):
        """(level, text) pairs from messages given as pairs or as plain strings."""
        return [msg if isinstance(msg, tuple) else (self._classify_message(msg), msg) for msg in messages]

    def _build_log_text(self, messages):
        return "\n".join(f"{self._LOG_ICONS[level]} {text}" for level, text in self._log_entries(messages))

    def _build_log_html(self, messages):
        def _esc(s):
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        parts = ["<div>"]
        for level, msg in self._log_entries(messages):
            lines = msg.split("\n")
            parts.append(
                f'<p class="mb-1 text-{level}"><span class="me-1">{self._LOG_ICONS[level]}</span>'
                f"<strong>{_esc(lines[0])}</strong></p>"
            )
            for sub in lines[1:]:
                if sub.strip():
                    parts.append(f'<p class="mb-0 ms-3 text-muted">{_esc(sub)}</p>')
        parts.append("</div>")
        return "".join(parts)

    def _find_duplicate_bill(self, partner, invoice_ref, company=None):
        """Return an existing non-cancelled vendor bill with the same ref for this partner
        in the given company (the current company by default)."""
        if not invoice_ref or not partner:
            return False
        company = company or self.env.company
        return self.env["account.move"].search(
            [
                ("move_type", "=", "in_invoice"),
                ("company_id", "=", company.id),
                ("partner_id", "=", partner.id),
                ("ref", "=", invoice_ref),
                ("state", "!=", "cancel"),
            ],
            limit=1,
        )

    # source categories for which a 0% rate is applied as such: zero rated (Z), exempt (E),
    # outside the scope of VAT, e.g. a supplier not registered for VAT (O), and export (G).
    # For reverse charge (AE), intra-community supply (K) and unknown categories the buyer
    # self-assesses the VAT through the fiscal position, so the existing taxes are kept.
    _ZERO_RATE_TAX_CATEGORIES = ("Z", "E", "O", "G")

    def _source_tax_percent(self, source_line):
        """Tax rate declared by a source line, or None when it must not override the bill.

        A 0 rate counts only with an explicit zero-rated/exempt category: the PDF parsers
        report 0 when they could not read the rate.
        """
        tax_pct = source_line.get("tax_percent")
        if tax_pct is None:
            return None
        tax_pct = float(tax_pct)
        if tax_pct:
            return tax_pct
        if (source_line.get("tax_category") or "").upper() in self._ZERO_RATE_TAX_CATEGORIES:
            return 0.0
        return None

    def _source_tax_percent_to_check(self, invoice_data, source_line):
        """Tax rate of a source line to compare with the order line, or None when unknown.

        A 0 rate counts with a zero-rated, reverse charge or intra-community category, or when
        the reader of the document vouches for the rates it read (``tax_percent_read``): the
        vendor-specific PDF parsers report 0 when they could not read the rate."""
        tax_pct = source_line.get("tax_percent")
        if tax_pct is None:
            return None
        tax_pct = float(tax_pct)
        category = (source_line.get("tax_category") or "").upper()
        if tax_pct or invoice_data.get("tax_percent_read") or category in self._ZERO_RATE_TAX_CATEGORIES + ("K", "AE"):
            return tax_pct
        return None

    # ------------------------------------------------------------
    # UBL XML reading
    # ------------------------------------------------------------
    def _uom_from_ubl(self, unit_code):
        return self._uom_from_code(unit_code)

    def _barcode_from_description(self, description):
        """Fallback for suppliers (e.g. PPG, tichet #9287) that put the EAN in the
        free-text Item/Description instead of StandardItemIdentification. Accepts ONLY
        a digit string of EAN-8/12/13/14 length WITH a valid check digit - anything
        looser would misread a supplier's genuine free-text description (lot number,
        internal note, ...) as a barcode and silently mismatch the product.
        """
        candidate = (description or "").strip()
        if not candidate.isdigit() or len(candidate) not in (8, 12, 13, 14):
            return None
        digits = [int(d) for d in candidate]
        check_digit = digits[-1]
        body = digits[:-1][::-1]
        total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(body))
        return candidate if (10 - total % 10) % 10 == check_digit else None

    def _is_ubl_invoice(self, content: bytes) -> bool:
        """Quickly check if provided XML bytes look like an UBL Invoice.
        We validate the root namespace equals the UBL Invoice namespace or that
        common UBL elements exist. Returns False on any parse error.
        """
        try:
            root = ET.fromstring(content)
        except ET.ParseError:
            return False
        # Extract namespace from the root tag: looks like {namespace}Invoice
        if root.tag.startswith("{") and "}" in root.tag:
            ns = root.tag.split("}", 1)[0].lstrip("{")
            if ns == NS.get("inv"):
                return True
        # Fallback: look for a couple of UBL-specific elements
        try:
            inv_id = root.findtext("cbc:ID", namespaces=NS)
            currency = root.findtext("cbc:DocumentCurrencyCode", namespaces=NS)
            if inv_id or currency:
                return True
        except Exception:
            return False
        return False

    def _normalize_price_base(self, price, base_el, unit_code, qty=0.0, line_total=0.0, adjust=0.0):
        """Return (unit price, base quantity, base ignored) for a UBL cac:Price.

        PriceAmount is the price of cbc:BaseQuantity units (default 1), expressed in the unit of
        BaseQuantity (unitCode), which can differ from the unit of InvoicedQuantity. The price is
        brought to one unit of the invoiced quantity. A missing, zero, negative or unreadable base
        is taken as 1.

        Many invoicing programs fill BaseQuantity wrongly (typically with the line quantity while
        PriceAmount is already a unit price). When the line total is known, the reading that
        reproduces it wins: qty x price (+ charges - allowances) must give LineExtensionAmount.
        If only the price without the base does, the base is ignored (third value True).
        `adjust` is charges minus allowances of the line.
        """
        if base_el is None or not price:
            return price, 1.0, False
        try:
            base = float(str(base_el.text).replace(",", "."))
        except (TypeError, ValueError):
            base = 0.0
        if base <= 0:
            _logger.warning("Ignoring invalid UBL BaseQuantity '%s'", base_el.text)
            return price, 1.0, False
        normalized = price / base
        base_uom = self._uom_from_code(base_el.get("unitCode"), fallback=False)
        line_uom = self._uom_from_code(unit_code, fallback=False)
        if base_uom and line_uom and base_uom != line_uom and self._source_uom_compatible(base_uom, line_uom):
            normalized = base_uom._compute_price(normalized, line_uom)
        if base != 1.0 and qty and line_total:
            tolerance = 0.02 + abs(line_total) * 0.001

            def _matches(unit_price):
                return abs(qty * unit_price + adjust - line_total) <= tolerance

            if not _matches(normalized) and _matches(price):
                return price, 1.0, True
        return normalized, base, False

    def _parse_xml(self, content):
        def _to_float(val):
            try:
                return float(str(val).replace(",", ".")) if val is not None else 0.0
            except Exception:
                return 0.0

        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            raise UserError(self.env._("Invalid XML: %s", e)) from e

        # Header
        invoice_id = root.findtext("cbc:ID", namespaces=NS)
        # A credit note comes either as a CreditNote document or as an Invoice with type code 381
        type_code = (
            root.findtext("cbc:InvoiceTypeCode", namespaces=NS)
            or root.findtext("cbc:CreditNoteTypeCode", namespaces=NS)
            or ""
        ).strip()
        is_credit_note = root.tag.rsplit("}", 1)[-1] == "CreditNote" or type_code == "381"
        issue_date = root.findtext("cbc:IssueDate", namespaces=NS)
        due_date = root.findtext("cbc:DueDate", namespaces=NS)
        currency = root.findtext("cbc:DocumentCurrencyCode", namespaces=NS) or "RON"
        order_ref = root.findtext("cac:OrderReference/cbc:ID", namespaces=NS)
        monetary_total = root.find("cac:LegalMonetaryTotal", namespaces=NS)
        tax_amount = sum(
            _to_float(tax_total.findtext("cbc:TaxAmount", namespaces=NS))
            for tax_total in root.findall("cac:TaxTotal", namespaces=NS)
        )

        # Supplier
        supplier_vat = root.findtext(
            "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID", namespaces=NS
        ) or root.findtext(
            # a supplier not registered for VAT has no PartyTaxScheme: its CUI is the legal entity id
            "cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID",
            namespaces=NS,
        )
        supplier_name = root.findtext(
            "cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName", namespaces=NS
        )

        # Lines
        lines = []
        for inv_line in root.findall("cac:InvoiceLine", namespaces=NS):
            qty = inv_line.findtext("cbc:InvoicedQuantity", namespaces=NS)
            price = inv_line.findtext("cac:Price/cbc:PriceAmount", namespaces=NS)
            line_total = inv_line.findtext("cbc:LineExtensionAmount", namespaces=NS)
            item_code = inv_line.findtext(
                "cac:Item/cac:SellersItemIdentification/cbc:ID", namespaces=NS
            ) or inv_line.findtext("cac:SellersItemIdentification/cbc:ID", namespaces=NS)
            # Extract barcode from StandardItemIdentification, schemeID="0160" (GS1/EAN)
            std_id_el = inv_line.find("cac:Item/cac:StandardItemIdentification/cbc:ID", namespaces=NS)
            barcode_val = None
            if std_id_el is not None:
                scheme_id = std_id_el.get("schemeID") if hasattr(std_id_el, "get") else None
                # Prefer when schemeID is 0160, but accept any value present in this tag if scheme missing
                if not scheme_id or scheme_id == "0160":
                    barcode_val = std_id_el.text
            if not barcode_val:
                # Some suppliers (e.g. PPG, tichet #9287) put the EAN in the free-text
                # Description instead of StandardItemIdentification. Only accept it when
                # it's a checksum-valid EAN, so a supplier that puts real free text there
                # doesn't get misread as a barcode.
                barcode_val = self._barcode_from_description(
                    inv_line.findtext("cac:Item/cbc:Description", namespaces=NS)
                )

            name = inv_line.findtext("cac:Item/cbc:Name", namespaces=NS) or inv_line.findtext(
                "cac:Item/cbc:Description", namespaces=NS
            )
            tax_percent = inv_line.findtext("cac:Item/cac:ClassifiedTaxCategory/cbc:Percent", namespaces=NS)
            # UNCL5305 category (S, Z, E, AE, K, G, O): tells an explicit 0% apart from reverse charge
            tax_category = inv_line.findtext("cac:Item/cac:ClassifiedTaxCategory/cbc:ID", namespaces=NS)
            unit = inv_line.find("cbc:InvoicedQuantity", namespaces=NS)
            unit_code = unit.get("unitCode") if unit is not None else False

            # Extract line-level discount (AllowanceCharge with ChargeIndicator=false)
            allowance_amount = 0.0
            charge_amount = 0.0
            discount_percent = 0.0
            for ac in inv_line.findall("cac:AllowanceCharge", namespaces=NS):
                charge_indicator = (ac.findtext("cbc:ChargeIndicator", namespaces=NS) or "").strip().lower()
                if charge_indicator == "true":
                    try:
                        charge_amount += float(str(ac.findtext("cbc:Amount", namespaces=NS)).replace(",", "."))
                    except ValueError as e:
                        _logger.warning("Could not parse AllowanceCharge/Amount of a charge: %s", e)
                if charge_indicator == "false":
                    ac_amount_text = ac.findtext("cbc:Amount", namespaces=NS)
                    try:
                        allowance_amount += float(str(ac_amount_text).replace(",", ".")) if ac_amount_text else 0.0
                    except Exception as e:
                        _logger.warning("Could not parse AllowanceCharge/Amount '%s': %s", ac_amount_text, e)

            price_f = _to_float(price)
            qty_f = _to_float(qty)
            price_f, base_qty, base_ignored = self._normalize_price_base(
                price_f,
                inv_line.find("cac:Price/cbc:BaseQuantity", namespaces=NS),
                unit_code,
                qty=qty_f,
                line_total=_to_float(line_total),
                adjust=charge_amount - allowance_amount,
            )
            if allowance_amount and price_f and qty_f:
                gross_total = price_f * qty_f
                discount_percent = round(allowance_amount / gross_total * 100, 2)

            lines.append(
                {
                    "code": (item_code or "").strip(),
                    "barcode": (barcode_val or "").strip(),
                    "name": (name or "").strip(),
                    "qty": qty_f,
                    "price": price_f,
                    "price_base_qty": base_qty,
                    "price_base_ignored": base_ignored,
                    "discount": discount_percent,
                    "line_total": _to_float(line_total),
                    "tax_percent": _to_float(tax_percent),
                    "tax_category": (tax_category or "").strip().upper(),
                    "unit_code": unit_code,
                }
            )

        return {
            "invoice_id": (invoice_id or "").strip(),
            "document_type": "credit_note" if is_credit_note else "invoice",
            "issue_date": issue_date,
            "due_date": due_date,
            "currency": currency,
            "order_ref": (order_ref or "").strip(),
            "line_extension_amount": _to_float(
                monetary_total is not None and monetary_total.findtext("cbc:LineExtensionAmount", namespaces=NS) or None
            ),
            "tax_exclusive_amount": _to_float(
                monetary_total is not None and monetary_total.findtext("cbc:TaxExclusiveAmount", namespaces=NS) or None
            ),
            "tax_inclusive_amount": _to_float(
                monetary_total is not None and monetary_total.findtext("cbc:TaxInclusiveAmount", namespaces=NS) or None
            ),
            "payable_amount": _to_float(
                monetary_total is not None and monetary_total.findtext("cbc:PayableAmount", namespaces=NS) or None
            ),
            "tax_amount": tax_amount,
            "supplier_vat": (supplier_vat or "").strip(),
            "supplier_name": (supplier_name or "").strip(),
            "lines": lines,
        }
