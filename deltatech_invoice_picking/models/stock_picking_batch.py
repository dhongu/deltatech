# © Terrabit
# See LICENSE file for full copyright and licensing details.


from odoo import fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain


class StockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    invoiced = fields.Boolean(compute="_compute_invoiced", search="_search_invoiced")

    def _compute_invoiced(self):
        for batch in self:
            invoiced = True
            for picking in batch.picking_ids:
                if not picking.account_move_id:
                    invoiced = False
            batch.invoiced = invoiced

    def _search_invoiced(self, operator, value):
        # Odoo 19 normalizeaza conditiile pe boolean la `in [True]` / `not in [True]`
        # (_optimize_boolean_in din odoo/orm/domains.py), nu la `= False`
        if operator in ("in", "not in"):
            if set(value) != {True}:
                return NotImplemented
            searched_value = operator == "in"
        elif operator in ("=", "!="):
            searched_value = bool(value) == (operator == "=")
        else:
            return NotImplemented
        # lot facturat = nu are nicio livrare fara factura
        not_invoiced = Domain("picking_ids.account_move_id", "=", False)
        return ~not_invoiced if searched_value else not_invoiced

    def action_create_invoice(self):
        for batch in self:
            if batch.state != "done":
                raise UserError(self.env._("You cannot invoice unconfirmed batches (%s)") % batch.name)
            if batch.picking_type_id.code == "outgoing":
                # check if pickings are already invoiced and remove invoiced pickings from list
                pickings = batch.picking_ids
                for picking in pickings:
                    if picking.account_move_id:
                        pickings -= picking
                return pickings.action_create_invoice()
            elif batch.picking_type_id.code == "incoming":
                # check if pickings are already invoiced and remove invoiced pickings from list
                pickings = batch.picking_ids
                for picking in pickings:
                    if picking.account_move_id:
                        pickings -= picking
                return pickings.action_create_supplier_invoice()
            else:
                raise UserError(
                    self.env._("You cannot invoice this type of batches: (%s)") % batch.picking_type_id.code
                )
