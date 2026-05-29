# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

import base64
import logging
import xml.etree.ElementTree as ET

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL

_logger = logging.getLogger(__name__)
NS = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


class PurchaseUblImportWizard(models.TransientModel):
    _name = "purchase.ubl.import.wizard"
    _description = "Import UBL XML for Vendor Invoice/Receipt"

    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        default="draft",
        readonly=True,
    )

    data_file = fields.Binary(string="XML File", required=True)
    filename = fields.Char(string="Filename")
    order_id = fields.Many2one("purchase.order", string="Purchase Order", readonly=True)
    order_lines_warning = fields.Text(compute="_compute_order_lines_warning")
    total_check_warning = fields.Text(compute="_compute_total_check_warning")

    update_prices = fields.Boolean(string="Update vendor prices", default=True)
    validate_receipt = fields.Boolean(string="Validate receipt from XML", default=False)
    create_bill = fields.Boolean(string="Create vendor bill", default=False)
    create_missing_products = fields.Boolean(string="Create missing products", default=True)

    # Stores the created vendor bill to allow opening it from the wizard
    bill_id = fields.Many2one("account.move", string="Vendor Bill", readonly=True)

    log = fields.Text(readonly=True)
    log_html = fields.Html(readonly=True, sanitize=True)

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    @api.depends("order_id", "order_id.order_line")
    def _compute_order_lines_warning(self):
        for wizard in self:
            if wizard.order_id and wizard.order_id.order_line:
                wizard.order_lines_warning = _(
                    "Purchase order already has lines. XML import will update only the existing order lines; "
                    "new lines from the XML will not be added to the purchase order."
                )
            else:
                wizard.order_lines_warning = False

    @api.depends("order_id", "data_file")
    def _compute_total_check_warning(self):
        for wizard in self:
            wizard.total_check_warning = False
            if not wizard.order_id or not wizard.data_file:
                continue
            try:
                invoice_xml = wizard._parse_xml(base64.b64decode(wizard.data_file))
            except Exception:
                continue
            total_check = wizard._get_order_total_check(wizard.order_id, invoice_xml)
            if total_check and not total_check["matches"]:
                wizard.total_check_warning = wizard._format_total_check_message(total_check)

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

    def _uom_from_ubl(self, unit_code):
        code = (unit_code or "").upper()
        xml_ids = {
            # pieces / units
            "C62": "uom.product_uom_unit",
            "H87": "uom.product_uom_unit",
            "PCE": "uom.product_uom_unit",
            "EA": "uom.product_uom_unit",
            "SET": "uom.product_uom_set",
            # weight
            "KGM": "uom.product_uom_kgm",
            "GRM": "uom.product_uom_gram",
            "TNE": "uom.product_uom_ton",
            # volume
            "LTR": "uom.product_uom_litre",
            "MLT": "uom.product_uom_ml",
            "MTQ": "uom.product_uom_cubic_meter",
            # length / area
            "MTR": "uom.product_uom_meter",
            "CMT": "uom.product_uom_cm",
            "MMT": "uom.product_uom_mm",
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

        rec = self.env.ref("uom.product_uom_unit", raise_if_not_found=True)

        return rec

    def _create_product_from_xml_line(self, supplier, line_vals, currency):
        """Create a storable product based on an XML invoice line and link supplierinfo.
        - supplier: res.partner (vendor)
        - line_vals: dict with keys code, barcode, name, unit_code, price
        - currency: code like RON/EUR
        Returns product.product record.
        """
        Product = self.env["product.product"]
        SupplierInfo = self.env["product.supplierinfo"]

        name = (line_vals.get("name") or line_vals.get("code") or "New Product").strip()
        code = (line_vals.get("code") or "").strip() or False
        barcode = (line_vals.get("barcode") or "").strip() or False
        uom = self._uom_from_ubl(line_vals.get("unit_code"))

        product = Product.create(
            {
                "name": name,
                "is_storable": True,
                "purchase_ok": True,
                "sale_ok": False,
                "barcode": barcode or False,
                "uom_id": uom.id,
            }
        )
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

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ctx = self.env.context or {}
        if ctx.get("active_model") == "purchase.order" and ctx.get("active_id"):
            if "order_id" in fields_list:
                res["order_id"] = ctx.get("active_id")
            Attachment = self.env["ir.attachment"]
            domain = [
                ("res_model", "=", "purchase.order"),
                ("res_id", "=", ctx.get("active_id")),
                "|",
                ("mimetype", "in", ["application/xml", "text/xml"]),
                ("name", "ilike", ".xml"),
            ]
            attachments = Attachment.search(domain, order="id desc")
            for att in attachments:
                if not att.datas:
                    continue
                try:
                    xml_bytes = base64.b64decode(att.datas)
                except Exception:
                    continue
                if self._is_ubl_invoice(xml_bytes):
                    if "data_file" in fields_list:
                        res["data_file"] = att.datas
                    if "filename" in fields_list:
                        res["filename"] = att.name
                    break
        return res

    def _parse_xml(self, content):
        def _to_float(val):
            try:
                return float(str(val).replace(",", ".")) if val is not None else 0.0
            except Exception:
                return 0.0

        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            raise UserError(_("Invalid XML: %s") % e) from e

        # Header
        invoice_id = root.findtext("cbc:ID", namespaces=NS)
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

            name = inv_line.findtext("cac:Item/cbc:Name", namespaces=NS) or inv_line.findtext(
                "cac:Item/cbc:Description", namespaces=NS
            )
            tax_percent = inv_line.findtext("cac:Item/cac:ClassifiedTaxCategory/cbc:Percent", namespaces=NS)
            unit = inv_line.find("cbc:InvoicedQuantity", namespaces=NS)
            unit_code = unit.get("unitCode") if unit is not None else False

            # Extract line-level discount (AllowanceCharge with ChargeIndicator=false)
            allowance_amount = 0.0
            discount_percent = 0.0
            for ac in inv_line.findall("cac:AllowanceCharge", namespaces=NS):
                charge_indicator = (ac.findtext("cbc:ChargeIndicator", namespaces=NS) or "").strip().lower()
                if charge_indicator == "false":
                    ac_amount_text = ac.findtext("cbc:Amount", namespaces=NS)
                    try:
                        allowance_amount += float(str(ac_amount_text).replace(",", ".")) if ac_amount_text else 0.0
                    except Exception as e:
                        _logger.warning("Could not parse AllowanceCharge/Amount '%s': %s", ac_amount_text, e)

            price_f = _to_float(price)
            qty_f = _to_float(qty)
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
                    "discount": discount_percent,
                    "line_total": _to_float(line_total),
                    "tax_percent": _to_float(tax_percent),
                    "unit_code": unit_code,
                }
            )

        return {
            "invoice_id": (invoice_id or "").strip(),
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

    def _get_order_total_check(self, order, invoice_xml):
        if not order:
            return False

        xml_total = invoice_xml.get("payable_amount") or invoice_xml.get("tax_inclusive_amount")
        order_amount = order.amount_total
        label = _("total")

        if not xml_total:
            xml_total = invoice_xml.get("tax_exclusive_amount") or invoice_xml.get("line_extension_amount")
            if not xml_total:
                xml_total = sum(line.get("line_total", 0.0) for line in invoice_xml.get("lines", []))
            order_amount = order.amount_untaxed
            label = _("untaxed total")

        if xml_total is None:
            return False

        difference = order_amount - xml_total
        return {
            "label": label,
            "currency": order.currency_id.name or invoice_xml.get("currency") or "",
            "order_amount": order_amount,
            "xml_amount": xml_total,
            "difference": difference,
            "matches": order.currency_id.is_zero(difference),
        }

    def _format_total_check_message(self, total_check):
        values = {
            "label": total_check["label"],
            "order_amount": f"{total_check['order_amount']:.2f}",
            "xml_amount": f"{total_check['xml_amount']:.2f}",
            "difference": f"{abs(total_check['difference']):.2f}",
            "currency": total_check["currency"],
        }
        if total_check["matches"]:
            return (
                _(
                    "Total check OK: purchase order %(label)s %(order_amount)s %(currency)s matches XML %(label)s "
                    "%(xml_amount)s %(currency)s."
                )
                % values
            )
        return (
            _(
                "Warning: purchase order %(label)s %(order_amount)s %(currency)s differs from XML %(label)s "
                "%(xml_amount)s %(currency)s (difference %(difference)s %(currency)s)."
            )
            % values
        )

    def _find_supplier_partner(self, supplier_vat, supplier_name):
        Partner = self.env["res.partner"]
        supplier_vat = (supplier_vat or "").strip()
        supplier_name = (supplier_name or "").strip()

        partner = False
        if supplier_vat:
            partner = Partner.search(
                [("supplier_rank", ">", 0), ("vat", "=ilike", supplier_vat)],
                limit=1,
            )
            if not partner and " " in supplier_vat:
                partner = Partner.search(
                    [("supplier_rank", ">", 0), ("vat", "=ilike", supplier_vat.replace(" ", ""))],
                    limit=1,
                )

        if not partner and supplier_name:
            partner = Partner.search(
                [("supplier_rank", ">", 0), ("name", "=ilike", supplier_name)],
                limit=1,
            )

        return partner

    def _find_order_from_xml(self, order_ref, partner=False):
        PurchaseOrder = self.env["purchase.order"]
        order_ref = (order_ref or "").strip()
        if not order_ref:
            return False

        search_variants = []
        if partner:
            search_variants.extend(
                [
                    [("partner_id", "=", partner.id), ("state", "!=", "cancel"), ("name", "=", order_ref)],
                    [("partner_id", "=", partner.id), ("state", "!=", "cancel"), ("partner_ref", "=", order_ref)],
                ]
            )
        search_variants.extend(
            [
                [("state", "!=", "cancel"), ("name", "=", order_ref)],
                [("state", "!=", "cancel"), ("partner_ref", "=", order_ref)],
            ]
        )

        for domain in search_variants:
            order = PurchaseOrder.search(domain, limit=1, order="id desc")
            if order:
                return order
        return False

    def _resolve_order_and_partner(self, invoice_xml):
        order = self.order_id.exists()
        if not order and self.env.context.get("active_model") == "purchase.order" and self.env.context.get("active_id"):
            order = self.env["purchase.order"].browse(self.env.context.get("active_id")).exists()

        supplier_vat = invoice_xml.get("supplier_vat")
        supplier_name = invoice_xml.get("supplier_name")
        xml_partner = self._find_supplier_partner(supplier_vat, supplier_name)

        if not order:
            order = self._find_order_from_xml(invoice_xml.get("order_ref"), xml_partner)

        partner = order.partner_id if order else xml_partner
        vat_mismatch_warning = bool(order and supplier_vat and partner.vat and supplier_vat != partner.vat)

        if not partner:
            raise UserError(
                _(
                    "No vendor found for supplier VAT '%(vat)s' / name '%(name)s'. "
                    "Launch the import from a purchase order or create the vendor first."
                )
                % {"vat": supplier_vat or "-", "name": supplier_name or "-"}
            )

        return order, partner, vat_mismatch_warning

    def _match_product(self, supplier, code, name, barcode=None):
        Product = self.env["product.product"]
        SupplierInfo = self.env["product.supplierinfo"]
        product = False
        code = (code or "").strip()
        barcode = (barcode or "").strip()

        # Try explicit barcode from XML first
        if barcode:
            product = Product.search([("barcode", "=", barcode)], limit=1)

        if not product and supplier and code:
            domain = [("partner_id", "=", supplier.id), ("product_code", "=ilike", code)]
            sinfo = SupplierInfo.search(domain, limit=1)
            if sinfo:
                if sinfo.product_id:
                    product = sinfo.product_id
                else:
                    product = sinfo.product_tmpl_id.product_variant_id

        if not product and supplier and name:
            domain = [("partner_id", "=", supplier.id), ("product_name", "=ilike", name)]
            sinfo = SupplierInfo.search(domain, limit=1)
            if sinfo:
                if sinfo.product_id:
                    product = sinfo.product_id
                else:
                    product = sinfo.product_tmpl_id.product_variant_id

        if not product and code:
            product = Product.search([("default_code", "=ilike", code)], limit=1)

        # Fallback: sometimes supplier code is actually barcode digits
        if not product and code and code.isdigit():
            product = Product.search([("barcode", "=", code)], limit=1)
        if not product and name:
            products = Product.search([("name", "=ilike", name)], limit=2)
            if len(products) == 1:
                product = products[0]

        if not product and name:
            name_without_spaces = name.replace(" ", "")
            lang = self.env.context.get("lang") or self.env.user.lang
            self.env.cr.execute(
                SQL(
                    "SELECT id FROM product_template"
                    " WHERE name ->> %(lang)s IS NOT NULL"
                    " AND REPLACE(name ->> %(lang)s, ' ', '') = %(name)s"
                    " LIMIT 1",
                    lang=lang,
                    name=name_without_spaces,
                )
            )
            product_id = self.env.cr.fetchone()
            if product_id:
                product_template = self.env["product.template"].browse(product_id[0])
                product = product_template.product_variant_id

        return product

    def _match_product_on_order(self, order, partner, code, name, barcode=None):
        """
        Restrict product matching to products present on the given purchase order.
        Matching priority within the order:
        1) Product barcode (from XML StandardItemIdentification)
        2) Supplier code (product.supplierinfo.product_code) for the order's vendor
        3) Product default_code
        4) Product barcode (when code itself is numeric)
        5) Product name exact match
        """
        if not order:
            return False
        code = (code or "").strip()
        barcode = (barcode or "").strip()
        # Build quick access lists
        order_lines = order.order_line

        # 1) barcode from XML within order lines
        if barcode:
            for line in order_lines:
                if (line.product_id.barcode or "").strip() == barcode:
                    return line.product_id

        # 2) Supplier code for this vendor
        if partner and code:
            for line in order_lines:
                tmpl = line.product_id.product_tmpl_id
                for sinfo in tmpl.seller_ids:
                    if sinfo.partner_id.id == partner.id and (sinfo.product_code or "").strip() == code:
                        return line.product_id
        # 3) default_code within order lines
        if code:
            for line in order_lines:
                if (line.product_id.default_code or "").strip() == code:
                    return line.product_id

        # 4) barcode when code is numeric
        if code and code.isdigit():
            for line in order_lines:
                if (line.product_id.barcode or "").strip() == code:
                    return line.product_id
        # 5) product name exact match
        if name:
            for line in order_lines:
                if (line.product_id.name or "").strip() == (name or "").strip():
                    return line.product_id
        return False

    def _update_supplier_price(self, supplier, product, code, price, currency):
        SupplierInfo = self.env["product.supplierinfo"]
        sinfo = SupplierInfo.search(
            [
                ("partner_id", "=", supplier.id),
                ("product_tmpl_id", "=", product.product_tmpl_id.id),
            ],
            limit=1,
        )
        values = {
            "partner_id": supplier.id,
            "product_tmpl_id": product.product_tmpl_id.id,
            "product_id": product.id,
            "product_code": code,
            "price": price,
            "currency_id": self._resolve_currency(currency).id,
            "delay": 1,
        }
        if sinfo:
            sinfo.write(values)
        else:
            SupplierInfo.create(values)

    def _find_receipt(self, order):
        Picking = self.env["stock.picking"]
        domain = [
            ("purchase_id", "=", order.id),
            ("state", "in", ["assigned", "confirmed", "waiting"]),
        ]

        pickings = Picking.search(domain, limit=1, order="id desc")
        return pickings

    def _validate_receipt_quantities(self, picking, line_map, order=False):
        # line_map: product_id -> qty
        if not picking:
            return False
        # When an order context is provided, follow the same logic as receipt_to_stock
        if order:
            # Ensure picking is assignable/assigned
            if picking.state == "confirmed":
                picking.action_assign()
                if picking.state != "assigned":
                    # Same message as in deltatech_fast_purchase for consistency
                    raise UserError(_("The stock transfer cannot be validated!"))
            if picking.state == "assigned":
                # Update header fields to mirror receipt_to_stock
                field_notice = False
                if "notice" in self.env["stock.picking"]._fields:
                    field_notice = "notice"
                if "l10n_ro_notice" in self.env["stock.picking"]._fields:
                    field_notice = "l10n_ro_notice"

                picking.write(
                    {
                        field_notice: False,
                        "origin": order.partner_ref or order.name,
                    }
                )
                # Set done quantities from XML map only for matched products
                for move in picking.move_ids:
                    qty = line_map.get(move.product_id.id, 0.0)
                    if qty and qty > 0:
                        if move.move_line_ids:
                            for ml in move.move_line_ids:
                                ml.qty_done = qty
                        else:
                            move._set_quantity_done(qty)
                # Mark moves as picked and validate with forced period date from PO
                picking.move_ids.picked = True
                picking.with_context(force_period_date=order.date_order)._action_done()
                return True
        # Fallback: original behavior using button_validate with backorder wizard handling
        for move in picking.move_ids_without_package:
            qty = line_map.get(move.product_id.id, 0.0)
            if qty > 0:
                for ml in move.move_line_ids:
                    ml.qty_done = qty if qty and qty > 0 else 0.0
                if not move.move_line_ids:
                    move._set_quantity_done(qty)
        action = picking.button_validate()
        if isinstance(action, dict) and action.get("res_model") == "stock.backorder.confirmation":
            wiz = self.env[action["res_model"]].browse(action.get("res_id"))
            wiz.with_context(skip_backorder=True).process()
        return True

    def _classify_message(self, msg):
        m = msg.lower()
        if any(k in m for k in ("not created", "unmatched")):
            return "danger"
        if any(k in m for k in ("warning", "differs", "mismatch", "already exists", "skipped", "no receipt found")):
            return "warning"
        if any(k in m for k in ("total check ok", "updated", "added", "created", "receipt updated")):
            return "success"
        return "info"

    def _build_log_html(self, messages):
        def _esc(s):
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        icons = {
            "success": "fa-check-circle",
            "warning": "fa-exclamation-triangle",
            "danger": "fa-times-circle",
            "info": "fa-info-circle",
        }
        parts = ["<div>"]
        for msg in messages:
            level = self._classify_message(msg)
            icon = icons[level]
            lines = msg.split("\n")
            parts.append(
                f'<p class="mb-1 text-{level}"><i class="fa {icon} me-1"></i><strong>{_esc(lines[0])}</strong></p>'
            )
            for sub in lines[1:]:
                if sub.strip():
                    parts.append(f'<p class="mb-0 ms-3 text-muted">{_esc(sub)}</p>')
        parts.append("</div>")
        return "".join(parts)

    def _find_duplicate_bill(self, partner, invoice_ref):
        """Return an existing non-cancelled vendor bill with the same ref for this partner."""
        if not invoice_ref or not partner:
            return False
        return self.env["account.move"].search(
            [
                ("move_type", "=", "in_invoice"),
                ("partner_id", "=", partner.id),
                ("ref", "=", invoice_ref),
                ("state", "!=", "cancel"),
            ],
            limit=1,
        )

    def _apply_xml_taxes_to_bill(self, bill, mapped_lines):
        """Override bill line taxes with the tax percentage declared in the XML."""
        product_tax_pct = {}
        for ml in mapped_lines:
            product = ml.get("product")
            tax_pct = ml.get("tax_percent")
            if product and tax_pct:
                product_tax_pct[product.id] = float(tax_pct)

        if not product_tax_pct:
            return

        for line in bill.invoice_line_ids:
            if not line.product_id or line.product_id.id not in product_tax_pct:
                continue
            pct = product_tax_pct[line.product_id.id]
            tax = self.env["account.tax"].search(
                [
                    ("type_tax_use", "=", "purchase"),
                    ("amount_type", "=", "percent"),
                    ("amount", "=", pct),
                    ("company_id", "=", self.env.company.id),
                    ("active", "=", True),
                ],
                limit=1,
            )
            if tax and tax.ids != line.tax_ids.ids:
                line.tax_ids = [(6, 0, [tax.id])]

    def _create_vendor_bill(self, xml_invoice, order, mapped_lines=None):
        old_invoice = order.invoice_ids
        order.action_create_invoice()
        new_invoice = order.invoice_ids - old_invoice
        if new_invoice:
            origin = xml_invoice.get("order_ref")
            invoice_date = xml_invoice.get("issue_date")
            ref = xml_invoice.get("invoice_id")
            due_date = xml_invoice.get("due_date")

            new_invoice.write(
                {"invoice_origin": origin, "invoice_date": invoice_date, "ref": ref, "invoice_date_due": due_date}
            )
            if mapped_lines:
                self._apply_xml_taxes_to_bill(new_invoice, mapped_lines)

        return new_invoice

    def action_import(self):
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please select an XML file."))
        content = base64.b64decode(self.data_file)
        invoice_xml = self._parse_xml(content)

        supplier_vat = invoice_xml.get("supplier_vat")
        order, partner, vat_mismatch_warning = self._resolve_order_and_partner(invoice_xml)

        mapped_lines = []
        updated = []
        not_found = []
        created = []
        for ln in invoice_xml["lines"]:
            # If order has lines, restrict match to the order; otherwise match globally
            if order and order.order_line:
                product = self._match_product_on_order(
                    order, partner, ln.get("code"), ln.get("name"), ln.get("barcode")
                )
            else:
                product = self._match_product(partner, ln.get("code"), ln.get("name"), ln.get("barcode"))
            # Optionally create missing product
            if not product and self.create_missing_products:
                product = self._create_product_from_xml_line(partner, ln, invoice_xml.get("currency"))
                created.append(product.display_name)
            elif not product:
                not_found.append(ln.get("code") or ln.get("name") or "/")
            ln_map = {**ln, "product": product}
            mapped_lines.append(ln_map)
            if self.update_prices and product:
                self._update_supplier_price(
                    partner, product, ln.get("code"), ln.get("price", 0.0), invoice_xml.get("currency")
                )
                updated.append(f"{product.display_name}: {ln.get('price')} {invoice_xml.get('currency')}")

        # If the purchase order has no lines, add products from the XML as order lines
        added_count = 0
        if order and not order.order_line:
            POL = self.env["purchase.order.line"]
            for ml in mapped_lines:
                product = ml.get("product")
                if not product:
                    continue
                vals = {
                    "order_id": order.id,
                    "product_id": product.id,
                    "name": ml.get("name") or product.display_name,
                    "product_qty": ml.get("qty", 0.0) or 0.0,
                    "price_unit": ml.get("price", 0.0) or 0.0,
                    "product_uom_id": product.uom_id.id,
                    "date_planned": fields.Datetime.now(),
                }
                if ml.get("discount") and "discount" in self.env["purchase.order.line"]._fields:
                    vals["discount"] = ml.get("discount")
                POL.create(vals)
                added_count += 1

        # If the purchase order already has lines, update their quantities and prices from XML
        updated_lines_count = 0
        if order and order.order_line:
            # Build a product->list of xml lines map to support duplicates
            xml_map = {}
            for ml in mapped_lines:
                product = ml.get("product")
                if not product:
                    continue
                xml_map.setdefault(product.id, []).append(ml)
            # Iterate existing order lines and update when a matching XML line exists
            for line in order.order_line:
                lines_for_prod = xml_map.get(line.product_id.id)
                if not lines_for_prod:
                    continue
                xml_ln = lines_for_prod.pop(0)
                vals = {}
                qty = xml_ln.get("qty")
                if qty is not None:
                    vals["product_qty"] = qty
                price = xml_ln.get("price")
                if price is not None:
                    vals["price_unit"] = price
                discount = xml_ln.get("discount")
                if discount is not None and "discount" in self.env["purchase.order.line"]._fields:
                    vals["discount"] = discount
                # Optionally update description with XML name/code when empty
                if not line.name and (xml_ln.get("name") or xml_ln.get("code")):
                    vals["name"] = xml_ln.get("name") or xml_ln.get("code")
                if vals:
                    line.write(vals)
                    updated_lines_count += 1

        # Validate receipt
        pick_log = ""
        if self.validate_receipt:
            if order:
                picking = self._find_receipt(order)
                if picking:
                    line_map = {ml.get("product").id: ml.get("qty", 0.0) for ml in mapped_lines if ml.get("product")}
                    self._validate_receipt_quantities(picking, line_map, order=order)
                    pick_log = _("Receipt updated: %s") % picking.name
                else:
                    pick_log = _("No receipt found to validate.")
            else:
                pick_log = _("Receipt validation skipped: no purchase order was resolved from the context or XML.")

        bill = False
        bill_log = ""
        duplicate_bill = False
        if self.create_bill:
            if order:
                invoice_ref = invoice_xml.get("invoice_id")
                duplicate_bill = self._find_duplicate_bill(partner, invoice_ref)
                if duplicate_bill:
                    self.bill_id = duplicate_bill.id
                else:
                    try:
                        bill = self._create_vendor_bill(invoice_xml, order, mapped_lines=mapped_lines)
                        self.bill_id = bill and bill.id or False
                    except UserError as e:
                        bill_log = _("Vendor bill not created: %s") % str(e)
            else:
                bill_log = _("Vendor bill creation skipped: no purchase order was resolved from the context or XML.")

        # Build messages
        messages = []

        messages.append(_("Vendor: %(name)s (%(vat)s)") % {"name": partner.display_name, "vat": partner.vat or "-"})
        messages.append(
            _("Order: %(order)s | XML Reference: %(ref)s")
            % {"order": (order.name if order else "-"), "ref": (invoice_xml.get("order_ref") or "-")}
        )
        total_check = self._get_order_total_check(order, invoice_xml)
        if total_check:
            messages.append(self._format_total_check_message(total_check))
        if vat_mismatch_warning:
            messages.append(
                _(
                    "Warning: Supplier VAT in XML (%(xml_vat)s) differs from order supplier (%(po_vat)s). Proceeded with order's vendor."
                )
                % {"xml_vat": supplier_vat or "-", "po_vat": partner.vat or "-"}
            )
        if updated:
            messages.append(_("Updated prices:\n") + "\n".join(updated))
        if created:
            messages.append(_("Created products:\n") + "\n".join(created))
        if order and "updated_lines_count" in locals() and updated_lines_count:
            messages.append(_("Updated %s purchase order lines from XML.") % updated_lines_count)
        if order and added_count:
            messages.append(_("Added %s lines to the purchase order from XML.") % added_count)
        if order and not_found:
            messages.append(_("Unmatched lines in the order: %s") % ", ".join(not_found))
        elif not_found:
            messages.append(_("Unmatched products in XML: %s") % ", ".join(not_found))
        if pick_log:
            messages.append(pick_log)
        if duplicate_bill:
            messages.append(
                _("Vendor bill already exists for this invoice reference (%s). No new bill was created.")
                % (duplicate_bill.ref or duplicate_bill.name)
            )
        elif bill:
            messages.append(_("Vendor bill created: %s") % (bill.ref or ""))
        elif bill_log:
            messages.append(bill_log)

        self.log = "\n".join(messages)
        self.log_html = self._build_log_html(messages)
        self.state = "done"

        action = {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
        return action

    def action_view_vendor_bill(self):
        self.ensure_one()
        order = self.order_id.exists()
        if not order:
            ctx = self.env.context or {}
            if ctx.get("active_model") == "purchase.order" and ctx.get("active_id"):
                order = self.env["purchase.order"].browse(ctx.get("active_id")).exists()
        if not order:
            return {"type": "ir.actions.act_window_close"}
        invoices = self.bill_id if self.bill_id else False
        return order.action_view_invoice(invoices=invoices)
