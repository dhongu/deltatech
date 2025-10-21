# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import xml.etree.ElementTree as ET


NS = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
}


class PurchaseUblImportWizard(models.TransientModel):
    _name = "purchase.ubl.import.wizard"
    _description = "Import UBL XML for Vendor Invoice/Receipt"

    data_file = fields.Binary(string="XML File", required=True)
    filename = fields.Char(string="Filename")

    update_prices = fields.Boolean(string="Update vendor prices", default=True)
    validate_receipt = fields.Boolean(string="Validate receipt from XML", default=False)
    create_bill = fields.Boolean(string="Create vendor bill", default=True)

    log = fields.Text(readonly=True)

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
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            raise UserError(_("Invalid XML: %s") % e)

        # Header
        invoice_id = root.findtext("cbc:ID", namespaces=NS)
        issue_date = root.findtext("cbc:IssueDate", namespaces=NS)
        due_date = root.findtext("cbc:DueDate", namespaces=NS)
        currency = root.findtext("cbc:DocumentCurrencyCode", namespaces=NS) or "RON"
        order_ref = root.findtext("cac:OrderReference/cbc:ID", namespaces=NS)

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
            item_code = inv_line.findtext("cac:SellersItemIdentification/cbc:ID", namespaces=NS)
            name = inv_line.findtext("cac:Item/cbc:Name", namespaces=NS) or inv_line.findtext("cac:Item/cbc:Description", namespaces=NS)
            tax_percent = inv_line.findtext("cac:Item/cac:ClassifiedTaxCategory/cbc:Percent", namespaces=NS)
            unit = inv_line.find("cbc:InvoicedQuantity", namespaces=NS)
            unit_code = unit.get("unitCode") if unit is not None else False

            def _to_float(val):
                try:
                    return float(str(val).replace(",", ".")) if val is not None else 0.0
                except Exception:
                    return 0.0

            lines.append(
                {
                    "code": (item_code or "").strip(),
                    "name": (name or "").strip(),
                    "qty": _to_float(qty),
                    "price": _to_float(price),
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
            "supplier_vat": (supplier_vat or "").strip(),
            "supplier_name": (supplier_name or "").strip(),
            "lines": lines,
        }

    def _find_or_create_supplier(self, vat, name):
        Partner = self.env["res.partner"]
        normalized_vat = (vat or "").replace(" ", "").upper()
        partner = False
        if normalized_vat:
            # Allow formats like RO123, 123, RO 123
            number = normalized_vat.replace("RO", "").replace(" ", "")
            partner = Partner.search([("vat", "in", [normalized_vat, f"RO{number}", number])], limit=1)
        if not partner and name:
            partner = Partner.search([("name", "ilike", name)], limit=1)
        if not partner:
            partner = Partner.create({
                "name": name or _("Unknown vendor"),
                "vat": normalized_vat or False,
                "supplier_rank": 1,
                "is_company": True,
            })
        return partner

    def _match_product(self, supplier, code, name):
        Product = self.env["product.product"]
        SupplierInfo = self.env["product.supplierinfo"]
        product = False
        code = (code or "").strip()
        if supplier and code:
            sinfo = SupplierInfo.search([
                ("name", "=", supplier.id),
                ("product_code", "=", code),
            ], limit=1)
            if sinfo and sinfo.product_tmpl_id.product_variant_id:
                product = sinfo.product_tmpl_id.product_variant_id
        if not product and code:
            product = Product.search([("default_code", "=", code)], limit=1)
        if not product and code and code.isdigit():
            product = Product.search([("barcode", "=", code)], limit=1)
        if not product and name:
            product = Product.search([("name", "=", name)], limit=1)
        return product

    def _match_product_on_order(self, order, partner, code, name):
        """
        Restrict product matching to products present on the given purchase order.
        Matching priority within the order:
        1) Supplier code (product.supplierinfo.product_code) for the order's vendor
        2) Product default_code
        3) Product barcode (only if code is numeric)
        4) Product name exact match
        """
        if not order:
            return False
        code = (code or "").strip()
        # Build quick access lists
        order_lines = order.order_line
        # 1) Supplier code for this vendor
        if partner and code:
            for line in order_lines:
                tmpl = line.product_id.product_tmpl_id
                for sinfo in tmpl.seller_ids:
                    if sinfo.name.id == partner.id and (sinfo.product_code or "").strip() == code:
                        return line.product_id
        # 2) default_code within order lines
        if code:
            for line in order_lines:
                if (line.product_id.default_code or "").strip() == code:
                    return line.product_id
        # 3) barcode within order lines
        if code and code.isdigit():
            for line in order_lines:
                if (line.product_id.barcode or "").strip() == code:
                    return line.product_id
        # 4) product name exact match
        if name:
            for line in order_lines:
                if (line.product_id.name or "").strip() == (name or "").strip():
                    return line.product_id
        return False

    def _update_supplier_price(self, supplier, product, price, currency):
        SupplierInfo = self.env["product.supplierinfo"]
        sinfo = SupplierInfo.search([
            ("name", "=", supplier.id),
            ("product_tmpl_id", "=", product.product_tmpl_id.id),
        ], limit=1)
        values = {
            "name": supplier.id,
            "product_tmpl_id": product.product_tmpl_id.id,
            "product_id": product.id,
            "product_code": product.default_code or False,
            "price": price,
            "currency_id": self.env["res.currency"].search([("name", "=", currency or "RON")], limit=1).id,
        }
        if sinfo:
            sinfo.write(values)
        else:
            SupplierInfo.create(values)

    def _find_receipt(self, partner, order_ref, order=False):
        Picking = self.env["stock.picking"]
        domain = [("picking_type_id.code", "=", "incoming"), ("state", "in", ["assigned", "confirmed", "waiting", "ready"]) ]
        if partner:
            domain.append(("partner_id", "=", partner.id))
        if order:
            domain.append(("origin", "=", order.name))
        elif order_ref:
            domain.append(("origin", "ilike", order_ref))
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
                picking.write({
                    "notice": False,
                    "origin": order.partner_ref or order.name,
                })
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

    def _get_tax(self, partner, percent):
        AccountTax = self.env["account.tax"]
        company = self.env.company
        # Try to find purchase tax by percentage
        tax = AccountTax.search([
            ("type_tax_use", "in", ["purchase", "none"]),
            ("amount", "=", percent),
            ("company_id", "=", company.id),
            ("price_include", "in", [True, False]),
        ], limit=1)
        return tax

    def _create_vendor_bill(self, header, partner, mapped_lines, order=False):
        Move = self.env["account.move"]
        currency = self.env["res.currency"].search([( "name", "=", header.get("currency") or "RON")], limit=1)
        inv_partner = order.partner_id if order else partner
        origin = order.name if order else header.get("order_ref")
        move_vals = {
            "move_type": "in_invoice",
            "partner_id": inv_partner.id,
            "invoice_date": header.get("issue_date"),
            "invoice_payment_term_id": False,
            "invoice_date_due": header.get("due_date"),
            "ref": header.get("invoice_id"),
            "invoice_origin": origin,
            "currency_id": currency.id,
            "invoice_line_ids": [],
        }
        line_vals = []
        for ml in mapped_lines:
            tax = self._get_tax(inv_partner, ml.get("tax_percent", 0.0))
            line_vals.append((0, 0, {
                "product_id": ml["product"].id if ml.get("product") else False,
                "name": ml.get("name") or ml.get("code") or "/",
                "quantity": ml.get("qty", 0.0),
                "price_unit": ml.get("price", 0.0),
                "tax_ids": [(6, 0, tax.ids)] if tax else False,
            }))
        move_vals["invoice_line_ids"] = line_vals
        bill = Move.create(move_vals)
        return bill

    def action_import(self):
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please select an XML file."))
        content = base64.b64decode(self.data_file)
        header = self._parse_xml(content)

        # Determine context order if any
        order = False
        if self.env.context.get("active_model") == "purchase.order" and self.env.context.get("active_id"):
            order = self.env["purchase.order"].browse(self.env.context.get("active_id"))

        # Determine supplier: prefer order's vendor if order provided
        xml_partner = self._find_or_create_supplier(header.get("supplier_vat"), header.get("supplier_name"))
        partner = order.partner_id if order else xml_partner

        mapped_lines = []
        updated = []
        not_found = []
        for ln in header["lines"]:
            if order:
                product = self._match_product_on_order(order, partner, ln.get("code"), ln.get("name"))
            else:
                product = self._match_product(partner, ln.get("code"), ln.get("name"))
            if not product and order:
                not_found.append((ln.get("code") or ln.get("name") or "/"))
            ln_map = {**ln, "product": product}
            mapped_lines.append(ln_map)
            if self.update_prices and product:
                self._update_supplier_price(partner, product, ln.get("price", 0.0), header.get("currency"))
                updated.append(f"{product.display_name}: {ln.get('price')} {header.get('currency')}")

        # Validate receipt
        pick_log = ""
        if self.validate_receipt:
            picking = self._find_receipt(partner, header.get("order_ref"), order=order)
            if picking:
                line_map = {ml.get("product").id: ml.get("qty", 0.0) for ml in mapped_lines if ml.get("product")}
                self._validate_receipt_quantities(picking, line_map, order=order)
                pick_log = _("Receipt updated: %s") % picking.name
            else:
                pick_log = _("No receipt found to validate.")

        bill = False
        if self.create_bill:
            bill = self._create_vendor_bill(header, partner, mapped_lines, order=order)

        # Build messages
        messages = []
        # warn if XML supplier differs from order supplier
        if order and xml_partner and xml_partner.id != partner.id:
            messages.append(_("Warning: The supplier in the XML (%s) differs from the order supplier (%s).") % (xml_partner.display_name, partner.display_name))
        messages.append(_("Vendor: %s (%s)") % (partner.display_name, partner.vat or "-"))
        messages.append(_("Order: %s | XML Reference: %s") % ((order.name if order else "-"), (header.get("order_ref") or "-")))
        if updated:
            messages.append(_("Updated prices:\n") + "\n".join(updated))
        if order and not_found:
            messages.append(_("Unmatched lines in the order: %s") % ", ".join(not_found))
        if pick_log:
            messages.append(pick_log)
        if bill:
            messages.append(_("Vendor bill created: %s") % (bill.name or bill.ref or ""))

        self.log = "\n".join(messages)

        action = {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
        return action
