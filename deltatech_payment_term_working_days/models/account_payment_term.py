# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.tools import date_utils

from .working_days import WorkingDays

# Legal ceiling of the payment term between professionals, in calendar days
MAX_CALENDAR_DAYS = 60


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    postpone_to_working_day = fields.Boolean(
        string="Move to the Next Working Day",
        help="When a due date falls on a weekend or on a public holiday of the company, "
        "it is moved to the next working day.",
    )
    working_days_warning = fields.Boolean(compute="_compute_working_days_warning")

    @api.depends("line_ids.day_count", "line_ids.nb_days", "line_ids.delay_type")
    def _compute_working_days_warning(self):
        for term in self:
            term.working_days_warning = any(
                line._estimated_calendar_days() > MAX_CALENDAR_DAYS
                for line in term.line_ids
                if line.day_count == "working"
            )

    def _compute_terms(
        self,
        date_ref,
        currency,
        company,
        tax_amount,
        tax_amount_currency,
        sign,
        untaxed_amount,
        untaxed_amount_currency,
        cash_rounding=None,
    ):
        pay_term = super()._compute_terms(
            date_ref,
            currency,
            company,
            tax_amount,
            tax_amount_currency,
            sign,
            untaxed_amount,
            untaxed_amount_currency,
            cash_rounding=cash_rounding,
        )
        lines = self.line_ids
        if not self.postpone_to_working_day and "working" not in lines.mapped("day_count"):
            return pay_term
        working_days = WorkingDays(self.env, company)
        date_ref = fields.Date.to_date(date_ref) or fields.Date.context_today(self)
        # super() returns one term per payment term line, in the same order
        for line, term_vals in zip(lines, pay_term["line_ids"], strict=True):
            due_date = line._get_working_due_date(date_ref, working_days) or term_vals["date"]
            if self.postpone_to_working_day:
                due_date = working_days.next_working(due_date)
            term_vals["date"] = due_date
        return pay_term


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    day_count = fields.Selection(
        [("calendar", "Calendar Days"), ("working", "Working Days")],
        string="Count",
        required=True,
        default="calendar",
        help="Working days skip the weekends and the public holidays of the company. "
        "They are not used when the due date is a fixed day of the next month.",
    )

    def _get_working_due_date(self, date_ref, working_days):
        """Due date with the days counted in working days, None when the line counts calendar days."""
        self.ensure_one()
        if self.day_count != "working" or self.delay_type == "days_end_of_month_on_the":
            return None
        if self.delay_type == "days_after_end_of_month":
            start = date_utils.end_of(date_ref, "month")
        elif self.delay_type == "days_after_end_of_next_month":
            start = date_utils.end_of(date_ref + relativedelta(months=1), "month")
        else:
            start = date_ref
        return working_days.add(start, self.nb_days)

    def _estimated_calendar_days(self):
        """Rough calendar length of the line: five working days make a week."""
        self.ensure_one()
        days = self.nb_days * 7 / 5
        if self.delay_type == "days_after_end_of_month":
            days += 30
        elif self.delay_type == "days_after_end_of_next_month":
            days += 60
        return days
