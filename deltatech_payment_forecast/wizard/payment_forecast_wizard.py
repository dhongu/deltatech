# Copyright (c) 2024-now Terrabit Solutions All Rights Reserved


from dateutil.relativedelta import relativedelta

from odoo import fields, models


class PaymentForecastWizard(models.TransientModel):
    _name = "payment.forecast.wizard"
    _description = "Payment forecast wizard"

    date_to = fields.Date(string="End Date", required=True, default=fields.Date.today)
    company_id = fields.Many2one("res.company", "Company", required=True, default=lambda self: self.env.user.company_id)

    def empty_forecast(self):
        query = "delete from payment_forecast"
        self.env.cr.execute(query)

    def get_estimated_payment_date(self, invoice):
        """
        Computes average payment time for invoice's commercial partner
        :param invoice: invoice
        :return: estimated payment date
        """
        # get average payment time
        date_today = fields.Date.context_today(self)
        date_from = date_today - relativedelta(days=365)
        domain = [("partner_id", "=", invoice.commercial_partner_id.id), ("date", ">=", date_from)]
        if invoice.move_type in ["out_invoice", "out_refund"]:
            domain.append(("account_code", "ilike", "4111"))
        else:
            domain.append(("account_code", "ilike", "401"))
        payment_times = self.env["account.average.payment.report"].sudo().search(domain)
        no_payment_times = len(payment_times)
        partner_payment_days = 0
        if no_payment_times:
            all_payment_days = 0
            for payment_time in payment_times:
                all_payment_days += payment_time.payment_days
            partner_payment_days = round(all_payment_days / no_payment_times)
        if not partner_payment_days:
            return False
        else:
            return invoice.date + relativedelta(days=partner_payment_days)

    def get_forecast_lines(self):
        self.empty_forecast()
        domain = [
            ("state", "=", "posted"),
            ("move_type", "in", ["out_invoice", "out_refund", "in_invoice", "in_refund"]),
            ("invoice_date_due", "<=", self.date_to),
            ("payment_state", "in", ["not_paid", "partial"]),
        ]
        invoices = self.env["account.move"].search(domain)
        lines = []
        for invoice in invoices:
            if invoice.move_type in ["out_invoice", "out_refund"]:
                move_type = "outgoing"
            else:
                move_type = "incoming"
            estimated_payment_date = self.get_estimated_payment_date(invoice)
            if not estimated_payment_date:
                payment_amount_forecasted = invoice.amount_residual_signed
            else:
                if estimated_payment_date <= self.date_to:
                    payment_amount_forecasted = invoice.amount_residual_signed
                else:
                    payment_amount_forecasted = 0.0
            vals = {
                "partner_id": invoice.commercial_partner_id.id,
                "move_id": invoice.id,
                "currency_id": invoice.currency_id.id,
                "move_date": invoice.date,
                "move_due_date": invoice.invoice_date_due,
                "move_amount": invoice.amount_total_signed,
                "journal_id": invoice.journal_id.id,
                "move_type": move_type,
                "move_amount_residual": invoice.amount_residual_signed,
                "payment_amount_forecasted": payment_amount_forecasted,
            }
            lines.append(vals)
        self.env["payment.forecast"].sudo().create(lines)
