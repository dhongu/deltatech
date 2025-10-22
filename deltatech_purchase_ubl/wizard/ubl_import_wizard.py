# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

import base64
import xml.etree.ElementTree as ET

from odoo import _, api, fields, models
from odoo.exceptions import UserError

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

    # Stores the created vendor bill to allow opening it from the wizard
    bill_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True)

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

            def _to_float(val):
                try:
                    return float(str(val).replace(",", ".")) if val is not None else 0.0
                except Exception:
                    return 0.0

            lines.append(
                {
                    "code": (item_code or "").strip(),
                    "barcode": (barcode_val or "").strip(),
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
            partner = Partner.create(
                {
                    "name": name or _("Unknown vendor"),
                    "vat": normalized_vat or False,
                    "supplier_rank": 1,
                    "is_company": True,
                }
            )
        return partner

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
            sinfo = SupplierInfo.search(
                [
                    ("partner_id", "=", supplier.id),
                    ("product_code", "=", code),
                ],
                limit=1,
            )
            if sinfo and sinfo.product_tmpl_id.product_variant_id:
                product = sinfo.product_tmpl_id.product_variant_id
        if not product and code:
            product = Product.search([("default_code", "=", code)], limit=1)

        # Fallback: sometimes supplier code is actually barcode digits
        if not product and code and code.isdigit():
            product = Product.search([("barcode", "=", code)], limit=1)
        if not product and name:
            product = Product.search([("name", "=", name)], limit=1)

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

    def _update_supplier_price(self, supplier, product, price, currency):
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
            "product_code": product.default_code or False,
            "price": price,
            "currency_id": self.env["res.currency"].search([("name", "=", currency or "RON")], limit=1).id,
            "delay": 1,
        }
        if sinfo:
            sinfo.write(values)
        else:
            SupplierInfo.create(values)

    def _find_receipt(self,   order):
        Picking = self.env["stock.picking"]
        domain = [
            ("purchase_id", "=", order.id),
            ("state", "in", ["assigned", "confirmed", "waiting", "ready"]),
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
                picking.write(
                    {
                        "notice": False,
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

    def _get_tax(self, partner, percent):
        AccountTax = self.env["account.tax"]
        company = self.env.company
        # Try to find purchase tax by percentage
        tax = AccountTax.search(
            [
                ("type_tax_use", "in", ["purchase", "none"]),
                ("amount", "=", percent),
                ("company_id", "=", company.id),
                ("price_include", "in", [True, False]),
            ],
            limit=1,
        )
        return tax

    def _create_vendor_bill(self, xml_invoice,  order):

        old_invoice= order.invoice_ids
        action = order.action_create_invoice()
        new_invoice = order.invoice_ids - old_invoice
        if new_invoice:
            origin = xml_invoice.get("order_ref")
            invoice_date = xml_invoice.get("issue_date")
            ref = xml_invoice.get("invoice_id")
            due_date = xml_invoice.get("due_date")

            new_invoice.write({
                "invoice_origin": origin,
                "invoice_date": invoice_date,
                "ref": ref,
                "invoice_due_date":due_date
            })

        # Move = self.env["account.move"]
        # currency = self.env["res.currency"].search([("name", "=", header.get("currency") or "RON")], limit=1)
        # inv_partner = order.partner_id if order else partner
        # origin = order.name if order else header.get("order_ref")
        # move_vals = {
        #     "move_type": "in_invoice",
        #     "partner_id": inv_partner.id,
        #     "invoice_date": header.get("issue_date"),
        #     "invoice_payment_term_id": False,
        #     "invoice_date_due": header.get("due_date"),
        #     "ref": header.get("invoice_id"),
        #     "invoice_origin": origin,
        #     "currency_id": currency.id,
        #     "invoice_line_ids": [],
        # }
        # line_vals = []
        # for ml in mapped_lines:
        #     tax = self._get_tax(inv_partner, ml.get("tax_percent", 0.0))
        #     line_vals.append(
        #         (
        #             0,
        #             0,
        #             {
        #                 "product_id": ml["product"].id if ml.get("product") else False,
        #                 "name": ml.get("name") or ml.get("code") or "/",
        #                 "quantity": ml.get("qty", 0.0),
        #                 "price_unit": ml.get("price", 0.0),
        #                 "tax_ids": [(6, 0, tax.ids)] if tax else False,
        #             },
        #         )
        #     )
        # move_vals["invoice_line_ids"] = line_vals
        # bill = Move.create(move_vals)
        return new_invoice

    def action_import(self):
        self.ensure_one()
        if not self.data_file:
            raise UserError(_("Please select an XML file."))
        content = base64.b64decode(self.data_file)
        invoice_xml = self._parse_xml(content)

        # Determine context order if any
        order = False
        if self.env.context.get("active_model") == "purchase.order" and self.env.context.get("active_id"):
            order = self.env["purchase.order"].browse(self.env.context.get("active_id"))

        # Determine supplier: prefer order's vendor if order provided
        xml_partner = self._find_or_create_supplier(invoice_xml.get("supplier_vat"), invoice_xml.get("supplier_name"))
        partner = order.partner_id if order else xml_partner

        mapped_lines = []
        updated = []
        not_found = []
        for ln in invoice_xml["lines"]:
            # If order has lines, restrict match to the order; otherwise match globally
            if order and order.order_line:
                product = self._match_product_on_order(
                    order, partner, ln.get("code"), ln.get("name"), ln.get("barcode")
                )
            else:
                product = self._match_product(partner, ln.get("code"), ln.get("name"), ln.get("barcode"))
            if not product:
                not_found.append(ln.get("code") or ln.get("name") or "/")
            ln_map = {**ln, "product": product}
            mapped_lines.append(ln_map)
            if self.update_prices and product:
                self._update_supplier_price(partner, product, ln.get("price", 0.0), invoice_xml.get("currency"))
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
                    "product_uom": product.uom_po_id.id or product.uom_id.id,
                    "date_planned": fields.Datetime.now(),
                }
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
                # Optionally update description with XML name/code when empty
                if not line.name and (xml_ln.get("name") or xml_ln.get("code")):
                    vals["name"] = xml_ln.get("name") or xml_ln.get("code")
                if vals:
                    line.write(vals)
                    updated_lines_count += 1

        # Validate receipt
        pick_log = ""
        if self.validate_receipt:
            picking = self._find_receipt( order)
            if picking:
                line_map = {ml.get("product").id: ml.get("qty", 0.0) for ml in mapped_lines if ml.get("product")}
                self._validate_receipt_quantities(picking, line_map, order=order)
                pick_log = _("Receipt updated: %s") % picking.name
            else:
                pick_log = _("No receipt found to validate.")

        bill = False
        if self.create_bill:
            bill = self._create_vendor_bill(invoice_xml, order)
            # store for quick access from the wizard button
            self.bill_id = bill and bill.id or False

        # Build messages
        messages = []
        # warn if XML supplier differs from order supplier
        if order and xml_partner and xml_partner.id != partner.id:
            messages.append(
                _("Warning: The supplier in the XML (%s) differs from the order supplier (%s).")
                % (xml_partner.display_name, partner.display_name)
            )
        messages.append(_("Vendor: %s (%s)") % (partner.display_name, partner.vat or "-"))
        messages.append(
            _("Order: %s | XML Reference: %s") % ((order.name if order else "-"), (invoice_xml.get("order_ref") or "-"))
        )
        if updated:
            messages.append(_("Updated prices:\n") + "\n".join(updated))
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

    def action_view_vendor_bill(self):
        self.ensure_one()
        # Open the vendor bill(s) from the related purchase order context
        ctx = self.env.context or {}
        order = False
        if ctx.get("active_model") == "purchase.order" and ctx.get("active_id"):
            order = self.env["purchase.order"].browse(ctx.get("active_id"))
        if not order:
            return {"type": "ir.actions.act_window_close"}
        invoices = self.bill_id if self.bill_id else False
        return order.action_view_invoice(invoices=invoices)
