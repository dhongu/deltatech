# ©  2008-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _can_be_invoiced_alone(self):
        # return super()._can_be_invoiced_alone() and not self.is_delivery
        return super()._can_be_invoiced_alone() and self.product_id and self.product_id.type != "service"
