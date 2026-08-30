# ©  Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools import html2plaintext


class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, values):
        res = super().write(values)
        if self and "state" in values and values["state"] == "done" and self.can_create_analytics():
            for move in self:
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
                analytic_lines = [analytic_source_values, analytic_dest_values]
                self.env["account.analytic.line"].create(analytic_lines)

        return res

    def can_create_analytics(self):
        if self.location_id.analytic_id and self.location_dest_id.analytic_id:
            return True
        return False
