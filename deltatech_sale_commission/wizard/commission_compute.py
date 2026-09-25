# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from collections import defaultdict

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

# Invoices whose payment counts as received: "in_payment" is a payment registered and
# reconciled with the invoice, only not yet matched with the bank statement.
PAID_STATES = ("paid", "in_payment")


class CommissionCompute(models.TransientModel):
    _name = "commission.compute"
    _description = "Compute commission"

    invoice_line_ids = fields.Many2many(
        "sale.margin.report",
        "commission_compute_inv_rel",
        "compute_id",
        "invoice_line_id",
        string="Account invoice line",
    )

    @api.model
    def default_get(self, fields):
        defaults = super().default_get(fields)

        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            domain = [("id", "in", active_ids)]
        else:
            domain = [("payment_state", "in", PAID_STATES), ("commission", "=", 0.0)]
        res = self.env["sale.margin.report"].search(domain)
        defaults["invoice_line_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    @api.model
    def _get_days_for_commission(self):
        """The maximum number of days between the due date and the last payment, or None when the
        commission does not depend on the payment. 0 means paid at the latest on the due date."""
        value = self.env["ir.config_parameter"].sudo().get_param("deltatech_sale_commission.days_for_commission")
        if value is False or not str(value).strip():
            return None
        try:
            days = int(value)
        except ValueError as e:
            raise UserError(
                self.env._(
                    "The system parameter deltatech_sale_commission.days_for_commission must be a whole number "
                    "of days, not %(value)s.",
                    value=value,
                )
            ) from e
        if days < 0:
            raise UserError(
                self.env._("The system parameter deltatech_sale_commission.days_for_commission can not be negative.")
            )
        return days

    def _get_line_commission(self, line, days_limit):
        """The commission granted on a margin report line."""
        invoice = line.invoice_id
        if days_limit is None or invoice.move_type == "out_refund":
            return line.commission_computed
        if invoice.payment_state not in PAID_STATES + ("reversed",):
            return 0.0
        payments = invoice.invoice_payments_widget and invoice.invoice_payments_widget["content"]
        if not payments:
            # nothing received: only a loss (negative commission) is kept
            return line.commission_computed if line.commission_computed < 0 else 0.0
        last_payment_date = max(fields.Date.to_date(payment["date"]) for payment in payments)
        days_late = (last_payment_date - invoice.invoice_date_due).days
        return line.commission_computed if days_late <= days_limit else 0.0

    def do_compute(self):
        # The commission is stored on the invoice lines, which the sales roles can only read.
        # The wizard writes with sudo, so the right to do it is checked here, on the commission
        # group, instead of asking for an invoicing right.
        if not self.env.user.has_group("deltatech_sale_commission.group_commission_manager"):
            raise AccessError(self.env._("Only a Commission Manager can compute the commissions."))
        days_limit = self._get_days_for_commission()
        res = []
        # Grouped by the value written, one write per distinct commission instead of one per line.
        # Now that the default selection of the wizard actually returns something (it used to
        # filter on a state an invoice never has), running it without a selection can bring in
        # every unpaid-commission line of the database — over 10.000 of them on some clients — and
        # most of them get either the computed value or a plain 0.
        by_commission = defaultdict(list)
        for line in self.invoice_line_ids:
            by_commission[self._get_line_commission(line, days_limit)].append(line.id)
            res.append(line.id)
        AccountMoveLine = self.env["account.move.line"].sudo()
        for commission, line_ids in by_commission.items():
            AccountMoveLine.browse(line_ids).write({"commission": commission})
        self.env["account.move.line"].flush_model(["commission"])
        self.invoice_line_ids.invalidate_recordset()
        return {
            "domain": [("id", "in", res)],
            "name": self.env._("Commission"),
            "view_mode": "list,form",
            "res_model": "sale.margin.report",
            "view_id": False,
            "type": "ir.actions.act_window",
        }
