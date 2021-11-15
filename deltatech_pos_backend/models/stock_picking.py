# ©  2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        if self.env.context.get("from_pos_order_confirm", False):
            return
        return super(StockPicking, self)._action_done()
