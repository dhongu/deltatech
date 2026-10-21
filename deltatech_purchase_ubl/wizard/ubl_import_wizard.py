# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

import base64
import logging
import xml.etree.ElementTree as ET

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
NS = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


class PurchaseUblImportWizard(models.TransientModel):
    _name = "purchase.ubl.import.wizard"
    _inherit = "purchase.invoice.import.mixin"
    _description = "Import UBL XML for Vendor Invoice/Receipt"

    data_file = fields.Binary(string="XML File", required=True)
    filename = fields.Char(string="Filename")
    total_check_warning = fields.Text(compute="_compute_total_check_warning")
    line_ids = fields.One2many("purchase.ubl.import.wizard.line", "wizard_id", string="Preview Lines")

    @api.depends("filename")
    def _compute_display_name(self):
        # without it the title of the window is the technical "purchase.ubl.import.wizard,<id>"
        for wizard in self:
            title = self.env._("Import Invoice")
            wizard.display_name = f"{title}: {wizard.filename}" if wizard.filename else title

    # ------------------------------------------------------------
    # Helpers specific to the UBL XML format
    # ------------------------------------------------------------
    @api.depends("order_id", "data_file")
    def _compute_total_check_warning(self):
        for wizard in self:
            wizard.total_check_warning = False
            if not wizard.order_id or not wizard.data_file:
                continue
            try:
                invoice_xml = wizard._parse_source(base64.b64decode(wizard.data_file))
            except Exception:
                continue
            differences = [
                wizard._format_total_check_message(check)
                for check in wizard._get_order_total_checks(wizard.order_id, invoice_xml)
                if not check["matches"]
            ]
            wizard.total_check_warning = "\n".join(differences) or False

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

    def _parse_source(self, content):
        """Invoice data of the uploaded file, shaped as `_process_invoice_data` expects.

        UBL XML here; an extension reads other formats (e.g. a PDF) by overriding it."""
        return self._parse_xml(content)

    def _parse_xml(self, content):
        def _to_float(val):
            try:
                return float(str(val).replace(",", ".")) if val is not None else 0.0
            except Exception:
                return 0.0

        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            raise UserError(self.env._("Invalid XML: %s") % e) from e

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

    def action_import(self):
        """Direct, headless import — kept for automated callers
        (purchase.order._process_attachments_for_post). Interactive users go through
        action_preview + action_confirm_import instead, where they can review and fix
        the product mapping before anything is written."""
        self.ensure_one()
        if not self.data_file:
            raise UserError(self.env._("Please select an XML file."))
        content = base64.b64decode(self.data_file)
        invoice_xml = self._parse_source(content)
        return self._process_invoice_data(invoice_xml)

    def action_preview(self):
        """Parse the XML and show the mapping preview: one line per invoice line, with
        the product the matcher found and how it found it (code/barcode = green, name =
        yellow, nothing = red → a new product would be created). The user can override
        the product on any line before confirming the import."""
        self.ensure_one()
        if not self.data_file:
            raise UserError(self.env._("Please select an XML file."))
        content = base64.b64decode(self.data_file)
        invoice_data = self._parse_source(content)
        if invoice_data.get("document_type") == "credit_note":
            # nothing to map: show the credit note warning instead of a preview
            return self._process_invoice_data(invoice_data)
        order, partner, _warning = self._resolve_order_and_partner(invoice_data)

        line_vals = []
        for index, ln in enumerate(invoice_data["lines"]):
            if order and order.order_line:
                product, match_type = self._match_product_on_order_detailed(
                    order, partner, ln.get("code"), ln.get("name"), ln.get("barcode")
                )
            else:
                product, match_type = self._match_product_detailed(
                    partner, ln.get("code"), ln.get("name"), ln.get("barcode")
                )
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "sequence": index,
                        "code": ln.get("code"),
                        "barcode": ln.get("barcode"),
                        "name": ln.get("name"),
                        "qty": ln.get("qty", 0.0),
                        "price": ln.get("price", 0.0),
                        "product_id": product.id if product else False,
                        "matched_product_id": product.id if product else False,
                        "match_type": match_type or "none",
                    },
                )
            )
        self.write({"line_ids": [(5, 0, 0)] + line_vals, "state": "preview"})
        return self._reopen()

    def action_confirm_import(self):
        """Run the import using the product mapping reviewed/adjusted in the preview."""
        self.ensure_one()
        if not self.data_file:
            raise UserError(self.env._("Please select an XML file."))
        content = base64.b64decode(self.data_file)
        invoice_data = self._parse_source(content)
        product_map = {
            line.sequence: line.product_id if line.line_action == "product" else line.product_id.browse()
            for line in self.line_ids
        }
        create_indexes = {line.sequence for line in self.line_ids if line.line_action == "create"}
        return self._process_invoice_data(invoice_data, product_map=product_map, create_indexes=create_indexes)

    def action_preview_or_import(self):
        """Import straight away when there is nothing for a person to decide: every line
        matched by vendor code or barcode, and the order total equals the invoice total
        after the import. Otherwise (or when the totals differ) the import is rolled back
        and the preview opens, where the user reviews each line."""
        self.ensure_one()
        action = self.action_preview()
        if self.state != "preview" or not self.order_id:
            return action
        if not self.line_ids or any(line.match_type not in ("code", "barcode") for line in self.line_ids):
            return action
        invoice_data = self._parse_source(base64.b64decode(self.data_file))
        product_map = {line.sequence: line.product_id for line in self.line_ids}
        try:
            with self.env.cr.savepoint():
                self._process_invoice_data(invoice_data, product_map=product_map, create_indexes=set())
                self.env.flush_all()
                total_check = self._get_order_total_check(self.order_id, invoice_data)
                if not (total_check and total_check["matches"]):
                    raise _NeedsReview()
        except _NeedsReview:
            self.env.invalidate_all()
            return action
        order = self.order_id
        if self.log_html:
            order.message_post(body=self.log_html)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Invoice imported"),
                "message": self.env._(
                    "All lines of invoice %(invoice)s were matched and the total matches purchase order %(order)s.",
                    invoice=invoice_data.get("invoice_id") or "-",
                    order=order.name,
                ),
                "type": "success",
                "sticky": False,
                "next": self.action_open_order(),
            },
        }

    def action_open_order(self):
        self.ensure_one()
        # `views` is required: as the `next` action of the notification, this dict reaches the
        # web client as it is, without the server-side clean-up a button's result goes through
        return {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "res_id": self.order_id.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "current",
        }

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Import Invoice"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }


class _NeedsReview(Exception):
    """Rolls back an import that a person has to review in the preview."""


class PurchaseUblImportWizardLine(models.TransientModel):
    _name = "purchase.ubl.import.wizard.line"
    _description = "UBL Import Preview Line"
    _order = "sequence, id"

    wizard_id = fields.Many2one("purchase.ubl.import.wizard", required=True, ondelete="cascade")
    sequence = fields.Integer()
    code = fields.Char(string="Supplier Code", readonly=True)
    barcode = fields.Char(string="Barcode", readonly=True)
    name = fields.Char(string="Vendor Description", readonly=True)
    qty = fields.Float(string="Quantity", readonly=True)
    price = fields.Float(string="Unit Price", readonly=True)
    product_id = fields.Many2one("product.product", string="Product")
    # The product the matcher proposed, kept to tell a manual override apart from the
    # automatic match when the user edits product_id in the preview.
    matched_product_id = fields.Many2one("product.product", readonly=True)
    match_type = fields.Selection(
        [
            ("code", "By supplier code"),
            ("barcode", "By barcode"),
            ("name", "By name"),
            ("manual", "Chosen manually"),
            ("none", "Not found"),
        ],
        readonly=True,
    )

    # What the import does with the line. A line without a product is ignored unless the
    # user explicitly asks for a new product: creating one by mistake duplicates the catalog.
    line_action = fields.Selection(
        [
            ("product", "Use product"),
            ("create", "Create new product"),
            ("skip", "Ignore"),
        ],
        string="Action",
        compute="_compute_line_action",
        store=True,
        readonly=False,
    )

    @api.depends("product_id")
    def _compute_line_action(self):
        for line in self:
            if line.product_id:
                line.line_action = "product"
            elif line.line_action != "create":
                line.line_action = "skip"

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for line in self:
            if line.product_id and line.product_id != line.matched_product_id:
                line.match_type = "manual"
