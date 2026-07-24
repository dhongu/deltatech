# ©  2026 Deltatech
from odoo import models


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"

    def _get_advice_data(self):
        """Group the batch payments by supplier for the payment advice report.

        A single batch may pay several suppliers, while the advice itself is issued
        per supplier. This returns one entry per partner:

            {
                "partner": res.partner,
                "payments": account.payment recordset,
                "lines": [{"bill": account.move, "amount": float}, ...],
                "total": float,
            }
        """
        self.ensure_one()
        groups = {}
        for payment in self.payment_ids:
            partner = payment.partner_id
            data = groups.setdefault(
                partner.id,
                {
                    "partner": partner,
                    "payments": self.env["account.payment"],
                    "lines": [],
                    "total": 0.0,
                },
            )
            data["payments"] |= payment
            for bill in payment._deltatech_advice_bills():
                # Amount settled from the reconciliation when available (accurate
                # for partial payments); otherwise the bill gross total, since the
                # advice may be issued before the payment is fully reconciled.
                amount = payment._deltatech_allocated_amount(bill) or abs(bill.amount_total_signed)
                data["lines"].append({"bill": bill, "amount": amount})
                data["total"] += amount
        return list(groups.values())


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _deltatech_advice_bills(self):
        """Vendor bills this payment is applied to.

        Uses ``invoice_ids`` (populated as soon as the payment targets the bills,
        i.e. already in the ``in_process`` state) rather than
        ``reconciled_bill_ids`` (populated only once the payment reaches the
        ``paid`` state), so the advice can be issued at payment time.
        """
        self.ensure_one()
        return self.invoice_ids.filtered(lambda m: m.move_type in ("in_invoice", "in_refund"))

    def _deltatech_allocated_amount(self, move):
        """Amount of ``move`` settled by this payment, in company currency.

        Computed from the partial reconciliations of the payment's
        payable/receivable lines, so partial payments are reported correctly
        instead of the full invoice total.
        """
        self.ensure_one()
        amount = 0.0
        pay_lines = self.move_id.line_ids.filtered(
            lambda line: line.account_type in ("asset_receivable", "liability_payable")
        )
        for line in pay_lines:
            for partial in line.matched_debit_ids:
                if partial.debit_move_id.move_id == move:
                    amount += partial.amount
            for partial in line.matched_credit_ids:
                if partial.credit_move_id.move_id == move:
                    amount += partial.amount
        return amount
