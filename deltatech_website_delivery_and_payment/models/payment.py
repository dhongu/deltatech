# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    _inherit = "payment.provider"

    value_limit = fields.Float(string="Value Limit")
    restrict_label_ids = fields.Many2many("res.partner.category")
    submit_txt = fields.Char(string="Submit text", default="Finalize order", translate=True)

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

        order = self.env["sale.order"].browse(sale_order_id).exists()
        if order:
            partner = order.partner_id
            compatible_providers = compatible_providers.filtered(lambda p: not p.is_restricted(partner))

        carrier = order.carrier_id
        if carrier:
            if carrier.acquirer_allowed_ids:
                compatible_providers = compatible_providers.filtered(lambda p: p.id in carrier.acquirer_allowed_ids.ids)

        return compatible_providers
