# -*- coding: utf-8 -*-
# ©  2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from dateutil.relativedelta import relativedelta
from odoo.tools import float_round


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"


    @api.one
    def compute(self, value, date_ref=False):
        date_ref = date_ref or fields.Date.today()
        amount = value
        sign = value < 0 and -1 or 1
        result = []
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value == 'balance':
                amt = currency.round(amount)
            if amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_of_month':
                    next_date += relativedelta(months=int(line.days/30))
                    if line.days2 < 0:
                        next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                        next_date = next_first_date + relativedelta(days=line.days2)
                    if line.days2 > 0:
                        next_date += relativedelta(day=line.days2, months=1)

                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)

                elif line.option == 'after_invoice_month':
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1)
                elif line.option == 'day_following_month':
                    next_date += relativedelta(day=line.days, months=1)
                elif line.option == 'day_current_month':
                    next_date += relativedelta(day=line.days, months=0)
                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt
        amount = sum(amt for _, amt in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))
        return result


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    option = fields.Selection(selection_add=[('day_of_month', 'Day of the Month')])
    days2 = fields.Integer('Day of the Month', required=True,
                            help="Day of the month, set -1 for the last day of the current month. If it's positive, it gives the day of the next month. Set 0 for net days (otherwise it's based on the beginning of the month).")



