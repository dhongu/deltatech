# © 2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _action_confirm(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        check_empty_order = get_param("sales.check_empty_order", default="False")
        check_empty_order = safe_eval(check_empty_order)
        if not check_empty_order:
            return super()._action_confirm()

        for order in self:
            lines = order.order_line.filtered(lambda r: not r.is_discount_line or not r.is_delivery)
            lines = lines.filtered(lambda r: r.product_id)
            if not lines:
                raise UserError(_("You cannot confirm an order without products."))
        return super()._action_confirm()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_discount_line = fields.Boolean(compute="_compute_is_discount_line")

    def _compute_is_discount_line(self):
        for line in self:
            line.is_discount_line = line._is_discount_line()
