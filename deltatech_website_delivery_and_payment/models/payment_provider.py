# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models

from odoo.addons.payment import utils as payment_utils


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

    def _filter_allowed_for_order(self, order, report=None):
        """Return the providers of `self` that are allowed to pay the sales order.

        A provider is excluded when:

        - the order total exceeds its `value_limit`;
        - the commercial partner of the order has one of its restricted labels;
        - the delivery method of the order allows only some providers (`acquirer_allowed_ids`)
          and it is not one of them.

        Used both to filter the providers offered at checkout and to check the provider of a
        transaction before paying the order.

        :param sale.order order: The sales order to pay.
        :param dict report: The availability report into which the excluded providers are logged.
        :return: The allowed providers.
        :rtype: payment.provider
        """
        providers = self
        unfiltered_providers = providers
        providers = providers.filtered(lambda p: not p.value_limit or order.amount_total <= p.value_limit)
        payment_utils.add_to_report(
            report,
            unfiltered_providers - providers,
            available=False,
            reason=self.env._("Order amount exceeds the value limit"),
        )

        partner = order.partner_id.commercial_partner_id
        unfiltered_providers = providers
        providers = providers.filtered(lambda p: not p.is_restricted(partner))
        payment_utils.add_to_report(
            report,
            unfiltered_providers - providers,
            available=False,
            reason=self.env._("Restricted for the partner labels"),
        )

        # If the order has a selected delivery method with allowed providers, intersect
        carrier = order.carrier_id.sudo()
        if carrier.acquirer_allowed_ids:
            unfiltered_providers = providers
            providers = providers & carrier.acquirer_allowed_ids
            payment_utils.add_to_report(
                report,
                unfiltered_providers - providers,
                available=False,
                reason=self.env._("Not allowed by the selected delivery method"),
            )
        return providers

    @api.model
    def _find_available_providers(
        self, company_id, partner_id, amount, *args, sale_order_id=None, report=None, **kwargs
    ):
        """Exclude the providers that are not allowed for the sales order
        (see `_filter_allowed_for_order`)."""
        available_providers = super()._find_available_providers(
            company_id, partner_id, amount, *args, sale_order_id=sale_order_id, report=report, **kwargs
        )
        order = sale_order_id and self.env["sale.order"].browse(sale_order_id).exists()
        if not order:
            return available_providers
        return available_providers._filter_allowed_for_order(order, report=report)
