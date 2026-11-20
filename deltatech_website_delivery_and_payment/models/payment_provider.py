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
        """The provider is hidden when the partner or its company has one of the restricted tags."""
        self.ensure_one()
        partner = partner_id.sudo()
        labels = partner.category_id | partner.commercial_partner_id.category_id
        return bool(self.sudo().restrict_label_ids & labels)

    @api.model
    def _get_compatible_providers(self, *args, sale_order_id=None, website_id=None, **kwargs):
        compatible_providers = super()._get_compatible_providers(
            *args, sale_order_id=sale_order_id, website_id=website_id, **kwargs
        )
        order = self.env["sale.order"].browse(sale_order_id)
        # Partner of the payment: the customer of the order, otherwise the one passed by the caller
        # (invoice payment from the portal, payment link, saved payment methods)
        partner = order.partner_id
        if not partner:
            partner_id = kwargs.get("partner_id", args[1] if len(args) > 1 else False)
            partner = self.env["res.partner"].browse(partner_id)
        if partner:
            compatible_providers = compatible_providers.filtered(lambda p: not p.is_restricted(partner))
        if sale_order_id:
            for provider in compatible_providers:
                if provider.value_limit and order.amount_total > provider.value_limit:
                    compatible_providers -= provider

            # If the order has a selected delivery carrier with allowed providers, intersect
            carrier = order.carrier_id
            if carrier and carrier.acquirer_allowed_ids:
                compatible_providers = compatible_providers & carrier.acquirer_allowed_ids
        return compatible_providers
