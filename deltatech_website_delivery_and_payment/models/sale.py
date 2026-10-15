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
        # Further restrict carriers based on partner labels, if configured
        partner = self.partner_id.commercial_partner_id
        carriers = carriers.filtered(lambda c: not c.restrict_label_ids or not c.is_restricted(partner))
        return carriers
