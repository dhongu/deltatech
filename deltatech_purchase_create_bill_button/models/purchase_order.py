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

    def action_create_invoice(self, attachment_ids=False):
        bills_before = self.invoice_ids
        res = super().action_create_invoice(attachment_ids=attachment_ids)
        # The native grouping keeps the scalar values of the first order only: put back
        # the vendor references of all the orders billed together (same policy as the
        # grouped customer invoices: every reference in "ref", the payment reference
        # only when it is the same for all the orders).
        for bill in self.invoice_ids - bills_before:
            orders = bill.invoice_line_ids.purchase_line_id.order_id
            refs = list(dict.fromkeys(ref for ref in orders.sorted("id").mapped("partner_ref") if ref))
            if len(orders) > 1 and len(refs) > 1:
                bill.write({"ref": ", ".join(refs), "payment_reference": False})
        return res
