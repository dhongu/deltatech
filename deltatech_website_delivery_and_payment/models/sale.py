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

    def _check_carrier_quotation(self, force_carrier_id=None):
        if force_carrier_id and force_carrier_id == self.carrier_id.id == int(force_carrier_id):
            return True
        return super(SaleOrder, self)._check_carrier_quotation(force_carrier_id)

    def _action_confirm(self):
        for order in self:
            tx = order.sudo().transaction_ids.get_last_transaction()
            if tx:
                order.write({"acquirer_id": tx.acquirer_id.id})
        return super(SaleOrder, self)._action_confirm()
