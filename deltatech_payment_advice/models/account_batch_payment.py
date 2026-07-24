# ©  2026 Deltatech
import base64

from odoo import models
from odoo.exceptions import UserError


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

        When the context key ``advice_partner_id`` is set, only that supplier's
        advice is returned — used to render/e-mail one advice per supplier.
        """
        self.ensure_one()
        partner_filter = self.env.context.get("advice_partner_id")
        groups = {}
        for payment in self.payment_ids:
            partner = payment.partner_id
            if partner_filter and partner.id != partner_filter:
                continue
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

    def action_send_payment_advice(self):
        """E-mail each supplier its own payment advice, with the PDF attached.

        One message per supplier, rendered and translated in that supplier's
        language. Suppliers without an e-mail address are skipped and reported.
        """
        self.ensure_one()
        template = self.env.ref("deltatech_payment_advice.mail_template_payment_advice")
        report = self.env.ref("deltatech_payment_advice.action_report_payment_advice")
        missing = self.env["res.partner"]
        sent = 0
        for advice in self._get_advice_data():
            partner = advice["partner"]
            if not partner.email:
                missing |= partner
                continue
            pdf_content, _dummy = report.with_context(advice_partner_id=partner.id)._render_qweb_pdf(
                report.report_name, self.ids
            )
            # Localized report name so the attachment filename matches the supplier's language.
            report_name = report.with_context(lang=partner.lang).name
            attachment = self.env["ir.attachment"].create(
                {
                    "name": f"{report_name} - {self.name}.pdf",
                    "type": "binary",
                    "datas": base64.b64encode(pdf_content),
                    "mimetype": "application/pdf",
                    "res_model": self._name,
                    "res_id": self.id,
                }
            )
            template.with_context(lang=partner.lang).send_mail(
                self.id,
                email_values={
                    "email_to": partner.email_formatted,
                    "attachment_ids": [attachment.id],
                },
                force_send=False,
            )
            sent += 1

        if not sent and missing:
            raise UserError(
                self.env._(
                    "No payment advice was sent: none of the suppliers has an e-mail address (%s).",
                    ", ".join(missing.mapped("name")),
                )
            )
        message = self.env._("%s payment advice(s) queued for sending.", sent)
        if missing:
            message += "\n" + self.env._(
                "Skipped suppliers without an e-mail address: %s.",
                ", ".join(missing.mapped("name")),
            )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success" if not missing else "warning",
                "message": message,
                "sticky": bool(missing),
            },
        }


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
