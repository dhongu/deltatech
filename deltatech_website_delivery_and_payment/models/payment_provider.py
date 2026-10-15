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

    @api.model
    def _find_available_providers(
        self, company_id, partner_id, amount, *args, sale_order_id=None, report=None, **kwargs
    ):
        """Exclude the providers that are not allowed for the sales order.

        - the order total exceeds the provider's `value_limit`;
        - the order partner has one of the provider's restricted labels;
        - the delivery method of the order allows only some providers (`acquirer_allowed_ids`).
        """
        available_providers = super()._find_available_providers(
            company_id, partner_id, amount, *args, sale_order_id=sale_order_id, report=report, **kwargs
        )
        order = sale_order_id and self.env["sale.order"].browse(sale_order_id).exists()
        if not order:
            return available_providers

        unfiltered_providers = available_providers
        available_providers = available_providers.filtered(
            lambda p: not p.value_limit or order.amount_total <= p.value_limit
        )
        payment_utils.add_to_report(
            report,
            unfiltered_providers - available_providers,
            available=False,
            reason=self.env._("Order amount exceeds the value limit"),
        )

        partner_labels = order.partner_id.category_id
        unfiltered_providers = available_providers
        available_providers = available_providers.filtered(lambda p: not (p.restrict_label_ids & partner_labels))
        payment_utils.add_to_report(
            report,
            unfiltered_providers - available_providers,
            available=False,
            reason=self.env._("Restricted for the partner labels"),
        )

        # If the order has a selected delivery carrier with allowed providers, intersect
        carrier = order.carrier_id
        if carrier and carrier.acquirer_allowed_ids:
            unfiltered_providers = available_providers
            available_providers = available_providers & carrier.acquirer_allowed_ids
            payment_utils.add_to_report(
                report,
                unfiltered_providers - available_providers,
                available=False,
                reason=self.env._("Not allowed by the selected delivery method"),
            )
        return available_providers
