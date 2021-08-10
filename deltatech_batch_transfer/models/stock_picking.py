# © Terrabit
# See LICENSE file for full copyright and licensing details.


from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        from_batch = self.env.context.get("from_batch")
        if not from_batch:
            return super(StockPicking, self).button_validate()
        else:
            all_pickings = self
            for picking in self:
                move_lines = picking.move_line_ids.filtered(lambda r: r.qty_done > 0)
                if not move_lines:
                    all_pickings -= picking
            if not all_pickings:
                raise UserError(_("No effective quantities set"))
            return super(StockPicking, all_pickings).button_validate()
