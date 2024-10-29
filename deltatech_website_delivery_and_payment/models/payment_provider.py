# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = "payment.provider"

    value_limit = fields.Float(string="Value Limit")
    restrict_label_ids = fields.Many2many("res.partner.category")

    def is_restricted(self, partner_id):
        self.ensure_one()
        for label in self.sudo().restrict_label_ids:
            if label in partner_id.sudo().category_id:
                return True
        return False

    @api.model
    def _get_compatible_providers(self, *args, sale_order_id=None, website_id=None, **kwargs):
        compatible_providers = super()._get_compatible_providers(
            *args, sale_order_id=sale_order_id, website_id=website_id, **kwargs
        )
        if sale_order_id:
            order = self.env["sale.order"].browse(sale_order_id)
            for provider in compatible_providers:
                if provider.value_limit and order.amount_total > provider.value_limit:
                    compatible_providers -= provider
                label_ids = list(set(order.partner_id.category_id.ids) & set(provider.restrict_label_ids.ids))
                if label_ids:
                    compatible_providers -= provider
        return compatible_providers
