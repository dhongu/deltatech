# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta

from odoo import fields, models
from odoo.tools import date_utils


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    nb_months = fields.Integer(
        string="Extra Months",
        default=0,
        help="With 'Days end of month on the', the due date moves this many more months "
        "(the rate is due on the selected day of the month).",
    )

    def _get_due_date(self, date_ref):
        due_date = super()._get_due_date(date_ref)
        if self.nb_months and self.delay_type == "days_end_of_month_on_the":
            try:
                day = int(self.days_next_month)
            except (TypeError, ValueError):
                day = 1
            if day <= 0:
                return date_utils.end_of(due_date + relativedelta(months=self.nb_months), "month")
            due_date += relativedelta(months=self.nb_months, day=day)
        return due_date
