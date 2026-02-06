# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DeliveryVendorDocument(models.Model):
    _name = "delivery.vendor.document"
    _description = "Vendor Delivery Document"
    _order = "id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default="New", readonly=True)
    partner_id = fields.Many2one("res.partner", required=True, domain=[("supplier_rank", ">", 0)])
    date = fields.Date(required=True, default=fields.Date.context_today)
    document_no = fields.Char(required=True)
    currency_id = fields.Many2one("res.currency", default=lambda self: self.env.company.currency_id.id)
    line_ids = fields.One2many("delivery.vendor.document.line", "document_id")
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company.id, required=True)
    picking_type_id = fields.Many2one(
        "stock.picking.type", domain="[('code', '=', 'incoming'), ('company_id', '=', company_id)]"
    )
    responsible_id = fields.Many2one("res.users")
    wave_id = fields.Many2one("stock.picking.batch", readonly=True)
    state = fields.Selection([("draft", "Draft"), ("processed", "Processed")], default="draft")
    allow_excess = fields.Boolean(string="Allow excess (log only)")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name") in (False, "New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("delivery.vendor.document") or "New"
        records = super().create(vals_list)
        return records

    def _moves_domain(self, product_ids):
        self.ensure_one()
        domain = [
            ("picking_id.partner_id", "=", self.partner_id.id),
            ("company_id", "=", self.company_id.id),
            ("product_id", "in", product_ids),
            ("state", "in", ("confirmed", "assigned")),
            ("picking_id.state", "in", ("confirmed", "assigned")),
            ("picking_id.picking_type_id.code", "=", "incoming"),
        ]
        if self.picking_type_id:
            domain.append(("picking_id.picking_type_id", "=", self.picking_type_id.id))
        return domain

    def action_generate_wave(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("There are no lines on the document."))
        if any(l.quantity <= 0 for l in self.line_ids):
            raise UserError(_("All quantities must be > 0."))

        products = self.line_ids.product_id
        moves = self.env["stock.move"].search(self._moves_domain(products.ids))
        # sortează cronologic după data programată sau data mișcării
        moves = moves.sorted(key=lambda m: (m.picking_id.scheduled_date or m.date, m.picking_id.id, m.id))

        # open qty în UoM de produs
        open_qty = {
            m.id: (
                m.product_uom._compute_quantity(m.product_uom_qty, m.product_id.uom_id)
                - m.product_uom._compute_quantity(m.quantity_done, m.product_id.uom_id)
            )
            for m in moves
        }

        allocations = {}  # move_id -> qty (in product UoM)
        not_covered = []

        for line in self.line_ids:
            need = line.product_uom._compute_quantity(line.quantity, line.product_id.uom_id)
            for m in (mv for mv in moves if mv.product_id == line.product_id and open_qty.get(mv.id, 0) > 0):
                take = min(need, open_qty[m.id])
                if take <= 0:
                    continue
                allocations[m.id] = allocations.get(m.id, 0) + take
                open_qty[m.id] -= take
                need -= take
                if need <= 0:
                    break
            if need > 0:
                if not self.allow_excess:
                    # compute the remaining qty in the line UoM for the message
                    rest_in_line_uom = line.product_id.uom_id._compute_quantity(need, line.product_uom)
                    raise UserError(
                        _(
                            f"Product {line.product_id.display_name}: quantity {rest_in_line_uom} {line.product_uom.name} exceeds the open quantity in receipts."
                        )
                    )
                not_covered.append((line, need))

        if not allocations:
            raise UserError(_("No open receipts found for the selected vendor/products."))

        mls_to_add = self.env["stock.move.line"]
        for move in self.env["stock.move"].browse(list(allocations.keys())):
            # creează un move line minim dacă nu există niciunul nefinalizat
            pending_mls = move.move_line_ids.filtered(lambda ml: ml.state != "done")
            if pending_mls:
                mls_to_add |= pending_mls
            else:
                ml = self.env["stock.move.line"].create(
                    {
                        "move_id": move.id,
                        "product_id": move.product_id.id,
                        "product_uom_id": move.product_uom.id,
                        "qty_done": 0.0,
                        "location_id": move.location_id.id,
                        "location_dest_id": move.location_dest_id.id,
                    }
                )
                mls_to_add |= ml

        # Validations for a single Operation Type and a single company
        if not mls_to_add:
            raise UserError(_("There are no move lines to add to the wave."))
        picking_types = mls_to_add.picking_id.picking_type_id
        companies = mls_to_add.company_id
        if len(companies) > 1:
            raise UserError(
                _(
                    "The selected operations belong to multiple companies. Please restrict the document to a single company."
                )
            )
        if self.picking_type_id and any(pt != self.picking_type_id for pt in picking_types):
            raise UserError(
                _("There are receipts with a different Operation Type than the one selected on the document.")
            )
        # dacă nu e setat pe document, deducem unicitatea
        if len(picking_types) > 1:
            raise UserError(
                _(
                    "The identified receipts have different Operation Types. Set the Operation Type field on the document to narrow the selection."
                )
            )

        # Creează un singur wave conform cerinței și atașează toate liniile
        target_pt = self.picking_type_id or picking_types[0]
        target_company = self.company_id or companies[0]
        wave = self.env["stock.picking.batch"].create(
            {
                "is_wave": True,
                "picking_type_id": target_pt.id,
                "company_id": target_company.id,
                "user_id": self.responsible_id.id if self.responsible_id else False,
            }
        )
        mls_to_add.with_context(active_owner_id=self.responsible_id.id if self.responsible_id else False)._add_to_wave(
            wave
        )

        body = _("Generated wave: %s") % (wave.name)
        if not_covered:
            lines = "\n".join(
                f"- {l.product_id.display_name}: missing {l.product_id.uom_id._compute_quantity(need_qty, l.product_uom)} {l.product_uom.name}"
                for l, need_qty in not_covered
            )
            body += "\n" + _("Quantities not covered by open receipts:") + "\n" + lines
        self.message_post(body=body)
        self.write({"state": "processed", "wave_id": wave.id})

        action = self.env["ir.actions.act_window"]._for_xml_id("stock_picking_batch.action_picking_batch")
        action.update({"res_id": wave.id, "view_mode": "form", "domain": [("id", "=", wave.id)]})
        return action

    def action_open_import_wizard(self):
        self.ensure_one()
        action = self.env.ref("deltatech_delivery_wave_doc.action_delivery_document_import_wizard").read()[0]
        action["context"] = dict(self.env.context, active_id=self.id, default_file_type="xlsx")
        return action


class DeliveryVendorDocumentLine(models.Model):
    _name = "delivery.vendor.document.line"
    _description = "Vendor Delivery Document Line"

    document_id = fields.Many2one("delivery.vendor.document", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", required=True)
    name = fields.Char()
    price_unit = fields.Monetary()
    quantity = fields.Float(required=True)
    product_uom = fields.Many2one("uom.uom", required=True)
    currency_id = fields.Many2one(related="document_id.currency_id", store=True, readonly=True)

    @api.onchange("product_id")
    def _onchange_product(self):
        for l in self:
            if l.product_id:
                l.name = l.product_id.display_name
                l.product_uom = l.product_id.uom_id
