# © 2025 Deltatech
# Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import SQL


class PurchaseInvoiceImportMixin(models.AbstractModel):
    _name = "purchase.invoice.import.mixin"
    _description = "Common matching/bill-creation logic for purchase invoice import wizards"

    state = fields.Selection(
        [("draft", "Draft"), ("preview", "Preview"), ("done", "Done")],
        default="draft",
        readonly=True,
    )

    order_id = fields.Many2one("purchase.order", string="Purchase Order", readonly=True)
    order_lines_warning = fields.Text(compute="_compute_order_lines_warning")
    # total_check_warning is declared+computed by each concrete wizard (it depends on the
    # wizard-specific data_file field and parse method: _parse_xml, _parse_pdf, ...), but relies
    # on _get_order_total_check/_format_total_check_message below, which are shared.

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
                    "Purchase order already has lines. Import will update only the existing order lines; "
                    "new lines from the source document will not be added to the purchase order."
                )
            else:
                wizard.order_lines_warning = False

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

    def _uom_from_code(self, unit_code):
        """Resolve a uom.uom record from a unit code/text found in the source document.
        Covers both UBL unitCode enum values (C62, KGM, ...) and common Romanian
        text units used on vendor-specific PDF layouts (Buc, Kg, L, ...).
        """
        code = (unit_code or "").strip().upper()
        xml_ids = {
            # pieces / units
            "C62": "uom.product_uom_unit",
            "H87": "uom.product_uom_unit",
            "PCE": "uom.product_uom_unit",
            "EA": "uom.product_uom_unit",
            "BUC": "uom.product_uom_unit",
            "SET": "uom.product_uom_set",
            # weight
            "KGM": "uom.product_uom_kgm",
            "KG": "uom.product_uom_kgm",
            "GRM": "uom.product_uom_gram",
            "G": "uom.product_uom_gram",
            "TNE": "uom.product_uom_ton",
            # volume
            "LTR": "uom.product_uom_litre",
            "L": "uom.product_uom_litre",
            "MLT": "uom.product_uom_ml",
            "MTQ": "uom.product_uom_cubic_meter",
            # length / area
            "MTR": "uom.product_uom_meter",
            "M": "uom.product_uom_meter",
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

        return self.env.ref("uom.product_uom_unit", raise_if_not_found=True)

    def _create_product_from_xml_line(self, supplier, line_vals, currency):
        """Create a storable product based on an invoice line and link supplierinfo.
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
        uom = self._uom_from_code(line_vals.get("unit_code"))

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

    def _get_order_total_check(self, order, invoice_data):
        if not order:
            return False

        xml_total = invoice_data.get("payable_amount") or invoice_data.get("tax_inclusive_amount")
        order_amount = order.amount_total
        label = _("total")

        if not xml_total:
            xml_total = invoice_data.get("tax_exclusive_amount") or invoice_data.get("line_extension_amount")
            if not xml_total:
                xml_total = sum(line.get("line_total", 0.0) for line in invoice_data.get("lines", []))
            order_amount = order.amount_untaxed
            label = _("untaxed total")

        if xml_total is None:
            return False

        difference = order_amount - xml_total
        return {
            "label": label,
            "currency": order.currency_id.name or invoice_data.get("currency") or "",
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

    def _resolve_order_and_partner(self, invoice_data):
        order = self.order_id.exists()
        if not order and self.env.context.get("active_model") == "purchase.order" and self.env.context.get("active_id"):
            order = self.env["purchase.order"].browse(self.env.context.get("active_id")).exists()

        supplier_vat = invoice_data.get("supplier_vat")
        supplier_name = invoice_data.get("supplier_name")
        xml_partner = self._find_supplier_partner(supplier_vat, supplier_name)

        if not order:
            order = self._find_order_from_xml(invoice_data.get("order_ref"), xml_partner)

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
                return product_template.product_variant_id, "name"

        return Product.browse(), False

    def _match_product_on_order(self, order, partner, code, name, barcode=None):
        return self._match_product_on_order_detailed(order, partner, code, name, barcode=barcode)[0]

    def _match_product_on_order_detailed(self, order, partner, code, name, barcode=None):
        """
        Restrict product matching to products present on the given purchase order.
        Matching priority within the order:
        1) Product barcode (from source document)
        2) Supplier code (product.supplierinfo.product_code) for the order's vendor
        3) Product default_code
        4) Product barcode (when code itself is numeric)
        5) Product name exact match

        Returns (product, match_type) like _match_product_detailed.
        """
        Product = self.env["product.product"]
        if not order:
            return Product.browse(), False
        code = (code or "").strip()
        barcode = (barcode or "").strip()
        # Build quick access lists
        order_lines = order.order_line

        # 1) barcode from source document within order lines
        if barcode:
            for line in order_lines:
                if (line.product_id.barcode or "").strip() == barcode:
                    return line.product_id, "barcode"

        # 2) Supplier code for this vendor
        if partner and code:
            for line in order_lines:
                tmpl = line.product_id.product_tmpl_id
                for sinfo in tmpl.seller_ids:
                    if sinfo.partner_id.id == partner.id and (sinfo.product_code or "").strip() == code:
                        return line.product_id, "code"
        # 3) default_code within order lines
        if code:
            for line in order_lines:
                if (line.product_id.default_code or "").strip() == code:
                    return line.product_id, "code"

        # 4) barcode when code is numeric
        if code and code.isdigit():
            for line in order_lines:
                if (line.product_id.barcode or "").strip() == code:
                    return line.product_id, "barcode"
        # 5) product name exact match
        if name:
            for line in order_lines:
                if (line.product_id.name or "").strip() == (name or "").strip():
                    return line.product_id, "name"
        return Product.browse(), False

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

    def _mark_line_received_if_manual(self, line):
        """Mark a purchase order line as received when its quantity is tracked manually.

        Service/consu products (qty_received_method == "manual") never get a qty_received
        from stock moves or from _validate_receipt_quantities below, since they have no
        stock picking. Without this, a line matched from the supplier invoice (e.g. an
        "Ecovaloare" eco-tax line) stays at qty_to_invoice == 0 and action_create_invoice()
        silently drops it from the vendor bill, even though it is present on the order.
        """
        if line.qty_received_method == "manual":
            line.qty_received_manual = line.product_qty

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
                picking_vals = {"origin": order.partner_ref or order.name}
                # Reset the "notice" flag if the field exists (l10n_ro or other)
                if "notice" in self.env["stock.picking"]._fields:
                    picking_vals["notice"] = False
                if "l10n_ro_notice" in self.env["stock.picking"]._fields:
                    picking_vals["l10n_ro_notice"] = False
                picking.write(picking_vals)
                # Set done quantities from source map only for matched products.
                # Odoo 19: stock.move.line uses `quantity` (qty_done removed) and
                # the move/line `picked` flag drives validation in _action_done.
                picked_moves = self.env["stock.move"]
                for move in picking.move_ids:
                    qty = line_map.get(move.product_id.id, 0.0)
                    if qty and qty > 0:
                        move._set_quantity_done(qty)
                        picked_moves |= move
                # Mark only the moves we set as picked; the rest go to a backorder
                picked_moves.picked = True
                picking.with_context(force_period_date=order.date_order)._action_done()
                return True
        # Fallback: original behavior using button_validate with backorder wizard handling
        # Odoo 19: iterate move_ids (move_ids_without_package was removed from stock.picking)
        for move in picking.move_ids:
            qty = line_map.get(move.product_id.id, 0.0)
            if qty and qty > 0:
                move._set_quantity_done(qty)
                move.picked = True
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
        """Override bill line taxes with the tax percentage declared in the source document."""
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

    def _create_vendor_bill(self, invoice_data, order, mapped_lines=None):
        old_invoice = order.invoice_ids
        order.action_create_invoice()
        new_invoice = order.invoice_ids - old_invoice
        if new_invoice:
            origin = invoice_data.get("order_ref")
            invoice_date = invoice_data.get("issue_date")
            ref = invoice_data.get("invoice_id")
            due_date = invoice_data.get("due_date")

            new_invoice.write(
                {"invoice_origin": origin, "invoice_date": invoice_date, "ref": ref, "invoice_date_due": due_date}
            )
            if mapped_lines:
                self._apply_xml_taxes_to_bill(new_invoice, mapped_lines)

        return new_invoice

    def _process_invoice_data(self, invoice_data, product_map=None):
        """Generic processing shared by all invoice import wizards, regardless of the
        source document format (UBL XML, Marso PDF, ...). Expects invoice_data as a dict
        shaped like the return value of _parse_source():
        {
            "invoice_id", "issue_date", "due_date", "currency", "order_ref",
            "supplier_vat", "supplier_name",
            "lines": [{"code", "barcode", "name", "qty", "price", "discount",
                       "line_total", "tax_percent", "unit_code"}, ...],
            "line_extension_amount", "tax_exclusive_amount", "tax_inclusive_amount",
            "payable_amount", "tax_amount",
        }

        product_map, when given, is a manual mapping coming from the wizard preview step:
        {source line index: product.product record (possibly empty)}. An entry present in
        the map REPLACES automatic matching for that line — the user saw the preview and
        either confirmed the match or picked another product; an empty product means
        "leave unmatched" (still subject to create_missing_products).
        """
        self.ensure_one()

        supplier_vat = invoice_data.get("supplier_vat")
        order, partner, vat_mismatch_warning = self._resolve_order_and_partner(invoice_data)

        mapped_lines = []
        updated = []
        not_found = []
        created = []
        for index, ln in enumerate(invoice_data["lines"]):
            if product_map is not None and index in product_map:
                product = product_map[index]
            elif order and order.order_line:
                # If order has lines, restrict match to the order; otherwise match globally
                product = self._match_product_on_order(
                    order, partner, ln.get("code"), ln.get("name"), ln.get("barcode")
                )
            else:
                product = self._match_product(partner, ln.get("code"), ln.get("name"), ln.get("barcode"))
            # Optionally create missing product
            if not product and self.create_missing_products:
                product = self._create_product_from_xml_line(partner, ln, invoice_data.get("currency"))
                created.append(product.display_name)
            elif not product:
                not_found.append(ln.get("code") or ln.get("name") or "/")
            ln_map = {**ln, "product": product}
            mapped_lines.append(ln_map)
            if self.update_prices and product:
                self._update_supplier_price(
                    partner, product, ln.get("code"), ln.get("price", 0.0), invoice_data.get("currency")
                )
                updated.append(f"{product.display_name}: {ln.get('price')} {invoice_data.get('currency')}")

        # Update existing order lines from the source document, then add any remaining
        # source lines (products not already on the order) as new order lines, instead of
        # silently dropping them.
        added_count = 0
        updated_lines_count = 0
        if order:
            POL = self.env["purchase.order.line"]
            # Build a product->list of source lines map to support duplicates
            source_map = {}
            for ml in mapped_lines:
                product = ml.get("product")
                if not product:
                    continue
                source_map.setdefault(product.id, []).append(ml)
            # Iterate existing order lines and update when a matching source line exists
            for line in order.order_line:
                lines_for_prod = source_map.get(line.product_id.id)
                if not lines_for_prod:
                    continue
                src_ln = lines_for_prod.pop(0)
                vals = {}
                qty = src_ln.get("qty")
                if qty is not None:
                    vals["product_qty"] = qty
                price = src_ln.get("price")
                if price is not None:
                    vals["price_unit"] = price
                discount = src_ln.get("discount")
                if discount is not None and "discount" in self.env["purchase.order.line"]._fields:
                    vals["discount"] = discount
                # Optionally update description with source name/code when empty
                if not line.name and (src_ln.get("name") or src_ln.get("code")):
                    vals["name"] = src_ln.get("name") or src_ln.get("code")
                if vals:
                    line.write(vals)
                    updated_lines_count += 1
                self._mark_line_received_if_manual(line)
            # Any source lines left unconsumed (product not already on the order) become new lines
            for lines_for_prod in source_map.values():
                for src_ln in lines_for_prod:
                    product = src_ln.get("product")
                    vals = {
                        "order_id": order.id,
                        "product_id": product.id,
                        "name": src_ln.get("name") or product.display_name,
                        "product_qty": src_ln.get("qty", 0.0) or 0.0,
                        "price_unit": src_ln.get("price", 0.0) or 0.0,
                        "product_uom_id": product.uom_id.id,
                        "date_planned": fields.Datetime.now(),
                    }
                    if src_ln.get("discount") and "discount" in self.env["purchase.order.line"]._fields:
                        vals["discount"] = src_ln.get("discount")
                    new_line = POL.create(vals)
                    added_count += 1
                    self._mark_line_received_if_manual(new_line)

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
                pick_log = _(
                    "Receipt validation skipped: no purchase order was resolved from the context or source document."
                )

        bill = False
        bill_log = ""
        duplicate_bill = False
        # Always create the vendor bill when the source document identifies an invoice number,
        # so the supplier's invoice reference/date are not lost when the user forgets to tick
        # "Create vendor bill". The checkbox stays available to force bill creation even when
        # the source has no invoice number.
        if self.create_bill or invoice_data.get("invoice_id"):
            if order and order.state not in ("purchase", "done"):
                # A draft/unconfirmed order has qty_to_invoice = 0 on every line
                # (purchase_order_line._compute_qty_invoiced), regardless of product_qty.
                # action_create_invoice() would still "succeed", producing a vendor bill
                # with every line at zero quantity/amount - a useless ghost document. This
                # hits the SPV auto-import flow, where a purchase order can be created and
                # attached to its XML before it is ever confirmed (tichet #9287).
                bill_log = _(
                    "Vendor bill creation skipped: purchase order %(order)s is not confirmed "
                    "yet, so there is nothing to invoice."
                ) % {"order": order.name}
            elif order:
                invoice_ref = invoice_data.get("invoice_id")
                duplicate_bill = self._find_duplicate_bill(partner, invoice_ref)
                if duplicate_bill:
                    self.bill_id = duplicate_bill.id
                else:
                    try:
                        bill = self._create_vendor_bill(invoice_data, order, mapped_lines=mapped_lines)
                        self.bill_id = bill and bill.id or False
                    except UserError as e:
                        bill_log = _("Vendor bill not created: %s") % str(e)
            else:
                bill_log = _(
                    "Vendor bill creation skipped: no purchase order was resolved from the context or source document."
                )

        # Build messages
        messages = []

        messages.append(_("Vendor: %(name)s (%(vat)s)") % {"name": partner.display_name, "vat": partner.vat or "-"})
        messages.append(
            _("Order: %(order)s | XML Reference: %(ref)s")
            % {"order": (order.name if order else "-"), "ref": (invoice_data.get("order_ref") or "-")}
        )
        total_check = self._get_order_total_check(order, invoice_data)
        if total_check:
            messages.append(self._format_total_check_message(total_check))
        if vat_mismatch_warning:
            messages.append(
                _(
                    "Warning: Supplier VAT in source document (%(xml_vat)s) differs from order supplier (%(po_vat)s). Proceeded with order's vendor."
                )
                % {"xml_vat": supplier_vat or "-", "po_vat": partner.vat or "-"}
            )
        if updated:
            messages.append(_("Updated prices:\n") + "\n".join(updated))
        if created:
            messages.append(_("Created products:\n") + "\n".join(created))
        if order and updated_lines_count:
            messages.append(_("Updated %s purchase order lines from source document.") % updated_lines_count)
        if order and added_count:
            messages.append(_("Added %s lines to the purchase order from source document.") % added_count)
        if order and not_found:
            messages.append(_("Unmatched lines in the order: %s") % ", ".join(not_found))
        elif not_found:
            messages.append(_("Unmatched products: %s") % ", ".join(not_found))
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
