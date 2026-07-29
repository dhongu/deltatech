# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_cancel(self):
        """Drop the generated purchase lines instead of leaving them behind.

        Only lines of a draft purchase order are removed, a confirmed order is
        left to the buyer.
        """
        purchase_lines = self.order_line.move_ids.created_purchase_line_ids
        purchase_lines.filtered(lambda line: line.order_id.state == "draft").unlink()
        return super()._action_cancel()
