# © Terrabit
# See LICENSE file for full copyright and licensing details.


from odoo import _, fields, models
from odoo.exceptions import UserError


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
        if operator in ("=", "!="):
            searched_value = bool(value) == (operator == "=")
        elif operator in ("in", "not in") and isinstance(value, list | tuple | set) and set(value) == {True}:
            searched_value = operator == "in"
        else:
            raise UserError(_("Unsupported operator %s on field invoiced") % operator)
        # lot facturat = nu are nicio livrare fara factura
        not_invoiced = [("picking_ids.account_move_id", "=", False)]
        return ["!"] + not_invoiced if searched_value else not_invoiced

    def action_create_invoice(self):
        for batch in self:
            if batch.state != "done":
                raise UserError(_("You cannot invoice unconfirmed batches (%s)") % batch.name)
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
                raise UserError(_("You cannot invoice this type of batches: (%s)") % batch.picking_type_id.code)
