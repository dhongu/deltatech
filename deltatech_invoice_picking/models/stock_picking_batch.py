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
            # a batch without transfers has nothing invoiced
            batch.invoiced = bool(batch.picking_ids) and all(p.account_move_id for p in batch.picking_ids)

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
        # lot facturat = are livrari si nu are nicio livrare fara factura
        not_invoiced = Domain("picking_ids.account_move_id", "=", False) | Domain("picking_ids", "=", False)
        return ~not_invoiced if searched_value else not_invoiced

    def action_create_invoice(self):
        """Invoice the not yet invoiced transfers of all the selected batches."""
        pickings_by_code = {}
        for batch in self:
            if batch.state != "done":
                raise UserError(self.env._("You cannot invoice unconfirmed batches (%s)", batch.name))
            code = batch.picking_type_id.code
            if code not in ("outgoing", "incoming"):
                raise UserError(self.env._("You cannot invoice this type of batches: (%s)", code))
            # skip the transfers that are already invoiced
            pickings = batch.picking_ids.filtered(lambda p: not p.account_move_id)
            pickings_by_code[code] = pickings_by_code.get(code, self.env["stock.picking"]) | pickings
        if len(pickings_by_code) > 1:
            raise UserError(self.env._("You cannot invoice delivery and receipt batches together."))
        if "outgoing" in pickings_by_code:
            return pickings_by_code["outgoing"].action_create_invoice()
        if "incoming" in pickings_by_code:
            return pickings_by_code["incoming"].action_create_supplier_invoice()
        return True
