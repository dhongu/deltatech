# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    acquirer_id = fields.Many2one("payment.acquirer")

    def _get_delivery_methods(self):
        carriers = super(SaleOrder, self)._get_delivery_methods()
        weight = self._get_estimated_weight()
        carriers = carriers.filtered(lambda c: not c.weight_min or c.weight_min <= weight)
        carriers = carriers.filtered(lambda c: not c.weight_max or c.weight_max >= weight)
        return carriers
