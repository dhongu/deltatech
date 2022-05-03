# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.onchange("state")
    def update_sale_order_status(self):
        for picking in self:
            if picking.sale_id:
                picking.sale_id._compute_picking_status()

    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        self.update_sale_order_status()
        return res

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        self.update_sale_order_status()
        return res

    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        self.update_sale_order_status()
        return res

    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        self.update_sale_order_status()
        return res
