# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update(
            {
                "ref": self.partner_ref or "",
                "payment_reference": self.partner_ref or "",
            }
        )
        return invoice_vals
