# ©  Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools import html2plaintext


class StockMove(models.Model):
    _inherit = "stock.move"

    location_analytic_line_ids = fields.Many2many(
        "account.analytic.line",
        "stock_move_location_analytic_line_rel",
        "move_id",
        "analytic_line_id",
        string="Location Analytic Lines",
        copy=False,
        readonly=True,
    )

    def write(self, values):
        # Liniile analitice se creează doar la tranziția efectivă în `done`:
        # o scriere repetată cu state="done" pe o mișcare deja finalizată nu mai creează nimic.
        moves_to_done = self.browse()
        if values.get("state") == "done":
            moves_to_done = self.filtered(lambda m: m.state != "done")
        res = super().write(values)
        if moves_to_done:
            moves_to_done._create_location_analytic_lines()
        return res

    def _create_location_analytic_lines(self):
        AnalyticLine = self.env["account.analytic.line"]
        for move in self:
            # Idempotent: o mișcare are cel mult o pereche sursă/destinație.
            if move.location_analytic_line_ids or not move.can_create_analytics():
                continue
            price_unit = move.price_unit
            if not price_unit:
                # În Odoo 19 valorizarea stă direct pe mișcare (câmpul `value`),
                # iar `_get_price_unit` întoarce direct prețul unitar.
                price_unit = move._get_price_unit() or move.product_id.standard_price
            note = html2plaintext(move.picking_id.note or "").strip()
            if note:
                ref = f"{note}({move.picking_id.name})"
            else:
                ref = move.picking_id.name
            date = fields.Date.context_today(move, move.date)
            analytic_source_values = {
                "name": move.product_id.name,
                "account_id": move.location_id.analytic_id.id,
                "ref": ref,
                "date": date,
                "amount": move.quantity * price_unit,
                "unit_amount": move.quantity,
                "product_id": move.product_id.id,
                "product_uom_id": move.product_uom.id,
            }
            analytic_dest_values = {
                "name": move.product_id.name,
                "account_id": move.location_dest_id.analytic_id.id,
                "ref": ref,
                "date": date,
                "amount": -1 * move.quantity * price_unit,
                "unit_amount": move.quantity,
                "product_id": move.product_id.id,
                "product_uom_id": move.product_uom.id,
            }
            lines = AnalyticLine.create([analytic_source_values, analytic_dest_values])
            move.location_analytic_line_ids = [(6, 0, lines.ids)]

    def can_create_analytics(self):
        self.ensure_one()
        if self.location_id.analytic_id and self.location_dest_id.analytic_id:
            return True
        return False
