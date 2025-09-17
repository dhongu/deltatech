# © 2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_confirm(self):
        for order in self:
            lines = order.order_line.filtered(lambda r: not r.is_discount_line or not r.is_delivery)
            lines = lines.filtered(lambda r: r.product_id)
            if not lines:
                raise UserError(_("You cannot confirm an order without products."))
        return super()._action_confirm()
