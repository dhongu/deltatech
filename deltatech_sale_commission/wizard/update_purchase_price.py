# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import AccessError

from .commission_compute import PAID_STATES


class CommissionUpdatePurchasePrice(models.TransientModel):
    _name = "commission.update.purchase.price"
    _description = "Update purchase price"

    for_all = fields.Boolean(string="For all lines")
    price_from_doc = fields.Boolean(string="Price from delivery", default=True)

    invoice_line_ids = fields.Many2many(
        "sale.margin.report",
        "commission_update_purchase_price_inv_rel",
        "compute_id",
        "invoice_line_id",
        string="Account invoice line",
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            domain = [("id", "in", active_ids)]
        else:
            domain = [("payment_state", "in", PAID_STATES), ("commission", "=", 0.0)]
        res = self.env["sale.margin.report"].search(domain)
        defaults["invoice_line_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    def do_compute(self):
        """Rewrite the cost of the selected lines (or of every line, with *for all*).

        Careful with *for all* on a database upgraded to 19.0.1.6.0: the rule for the cost of a
        credit note changed, so running it over the whole history rewrites the cost of the old
        credit notes and with it the profit already reported for those months. That is the
        correction the audit asked for, but it is a retroactive change to figures the client has
        seen — agree on it first, do not let it happen as a side effect of a routine refresh.
        """
        # the cost is written with sudo on the invoice lines, so only the commission managers
        # may run it (the wizard access is also limited to them)
        if not self.env.user.has_group("deltatech_sale_commission.group_commission_manager"):
            raise AccessError(self.env._("Only a Commission Manager can update the purchase price."))
        if self.for_all:
            lines = self.env["sale.margin.report"].search([])
        else:
            lines = self.invoice_line_ids

        for line in lines:
            invoice_line = self.env["account.move.line"].sudo().browse(line.id)

            if self.price_from_doc:
                # The cost the documents give, by the rule shared with the cron
                # (account.move.line._purchase_price_from_document). Unlike the cron, the wizard
                # *resets* the cost: a 0 on a credit note is written, because that is how a note
                # wrongly costed in the past gets corrected. Only None — the documents say nothing
                # — leaves the stored value alone.
                purchase_price = invoice_line._purchase_price_from_document()
                if purchase_price is not None:
                    invoice_line.write({"purchase_price": purchase_price})

            elif invoice_line.product_id.standard_price > 0:
                invoice_line.write({"purchase_price": invoice_line.product_id.standard_price})
        return True
