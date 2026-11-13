# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


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
        precision = self.env["decimal.precision"].precision_get("Product Unit")
        # Orders with nothing to bill are left out: otherwise the native grouping by
        # vendor would create a bill without lines for them.
        billable = self.filtered(
            lambda order: any(
                line.display_type not in ("line_section", "line_subsection", "line_note")
                and not float_is_zero(line.qty_to_invoice, precision_digits=precision)
                for line in order.order_line
            )
        )
        if not billable:
            raise UserError(self.env._("There is nothing to bill: no quantity left to invoice on the selected orders."))
        bills_before = billable.invoice_ids
        res = super(PurchaseOrder, billable).action_create_invoice(attachment_ids=attachment_ids)
        self._remove_zero_quantity_bill_lines(billable.invoice_ids - bills_before, precision)
        # The native grouping keeps the scalar values of the first order only: put back
        # the vendor references of all the orders billed together (same policy as the
        # grouped customer invoices: every reference in "ref", the payment reference
        # only when it is the same for all the orders).
        for bill in billable.invoice_ids - bills_before:
            orders = bill.invoice_line_ids.purchase_line_id.order_id
            refs = list(dict.fromkeys(ref for ref in orders.sorted("id").mapped("partner_ref") if ref))
            if len(orders) > 1 and len(refs) > 1:
                bill.write({"ref": ", ".join(refs), "payment_reference": False})
        return res

    @api.model
    def _remove_zero_quantity_bill_lines(self, bills, precision):
        """The native method copies every order line to the bill, so a backordered
        line (ordered, not received yet) arrives with quantity 0. Remove those lines,
        and the sections or notes left without any line under them."""
        for bill in bills:
            lines = bill.invoice_line_ids.sorted("sequence")
            to_remove = lines.filtered(
                lambda line: line.purchase_line_id
                and line.display_type == "product"
                and float_is_zero(line.quantity, precision_digits=precision)
            )
            kept = lines - to_remove
            # A section owns the notes under it: when no product line is left under a
            # section, the section and its notes go away together.
            orphans = self.env["account.move.line"]
            block = self.env["account.move.line"]
            has_product = False
            for line in kept:
                if line.display_type in ("line_section", "line_subsection"):
                    if block and not has_product:
                        orphans |= block
                    block = line
                    has_product = False
                    continue
                if block:
                    block |= line
                if line.display_type == "product":
                    has_product = True
            if block and not has_product:
                orphans |= block
            (to_remove | orphans).unlink()
