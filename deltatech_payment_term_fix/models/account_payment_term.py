# ©  2008-2022 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta

from odoo import fields, models


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    def compute(self, value, date_ref=False, currency=None):
        result = super(AccountPaymentTerm, self).compute(value, date_ref, currency)
        pos = 0
        for line in self.line_ids:
            if line.month_of_the_year:
                next_date, val = result[pos]
                next_date = fields.Date.from_string(next_date)
                next_date += relativedelta(day=line.day_of_the_month, month=line.month_of_the_year)
                result[pos] = fields.Date.to_string(next_date), val
            pos += 1
        return result


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    month_of_the_year = fields.Integer()
