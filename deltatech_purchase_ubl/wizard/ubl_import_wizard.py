# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

import base64
import logging
import xml.etree.ElementTree as ET

from odoo import _, api, fields, models
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
                invoice_xml = wizard._parse_xml(base64.b64decode(wizard.data_file))
            except Exception:
                continue
            total_check = wizard._get_order_total_check(wizard.order_id, invoice_xml)
            if total_check and not total_check["matches"]:
                wizard.total_check_warning = wizard._format_total_check_message(total_check)

    def _uom_from_ubl(self, unit_code):
        return self._uom_from_code(unit_code)

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

    def action_import(self):
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please select an XML file."))
        content = base64.b64decode(self.data_file)
        invoice_xml = self._parse_xml(content)
        return self._process_invoice_data(invoice_xml)
