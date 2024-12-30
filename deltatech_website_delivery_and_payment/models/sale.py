# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_delivery_methods(self):
        carriers = super()._get_delivery_methods()
        weight = self._get_estimated_weight()
        carriers = carriers.filtered(lambda c: not c.weight_min or c.weight_min <= weight)
        carriers = carriers.filtered(lambda c: not c.weight_max or c.weight_max >= weight)
        return carriers

    def _check_carrier_quotation(self, force_carrier_id=None, keep_carrier=False):
        if force_carrier_id and force_carrier_id == self.carrier_id.id == int(force_carrier_id):
            return True
        return super()._check_carrier_quotation(force_carrier_id=force_carrier_id, keep_carrier=keep_carrier)
