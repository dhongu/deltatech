# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    weight = fields.Float("Gross Weight", digits="Stock Weight", help="The gross weight in Kg.")
    weight_net = fields.Float("Net Weight", digits="Stock Weight", help="The net weight in Kg.")
    weight_package = fields.Float("Package Weight", digits="Stock Weight")

    @api.model_create_multi
    def create(self, vals_list):
        # Create the invoices using the default implementation
        invoices = super().create(vals_list)
        self._compute_weights(invoices)
        return invoices

    def _compute_weights(self, invoices):
        for invoice in invoices:
            gross_weight = 0.0
            net_weight = 0.0
            # Extract the products from the order lines
            for line in invoice.invoice_line_ids:
                # Calculate the new weight
                gross_weight += line.product_id.weight * line.quantity
                net_weight += line.product_id.l10n_ro_net_weight * line.quantity
            # Update the weight fields
            invoice.weight = gross_weight
            invoice.weight_net = net_weight
