# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from datetime import date, datetime, time, timedelta

from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentTermWorkingDays(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # Monday to Friday, Bucharest time
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Working Days Test",
                "company_id": cls.company.id,
                "attendance_ids": [
                    Command.create({"dayofweek": str(day), "hour_from": 8, "hour_to": 16}) for day in range(5)
                ],
            }
        )
        cls.company.resource_calendar_id = cls.calendar
        cls.company.tz = "Europe/Bucharest"
        # Romanian public holidays of spring 2026: Good Friday, Easter, Easter Monday, Labour Day
        for day in (date(2026, 4, 10), date(2026, 4, 12), date(2026, 4, 13), date(2026, 5, 1)):
            cls.env["resource.calendar.leaves"].create(
                {
                    "name": f"Holiday {day}",
                    "company_id": cls.company.id,
                    "calendar_id": False,
                    # 00:00-23:59 in Bucharest (UTC+3 in summer time)
                    "date_from": datetime.combine(day, time.min) - timedelta(hours=3),
                    "date_to": datetime.combine(day, time.max) - timedelta(hours=3),
                    "count_as": "absence",
                }
            )

    def _term(self, nb_days, day_count="working", postpone=False, delay_type="days_after"):
        return self.env["account.payment.term"].create(
            {
                "name": f"{nb_days} {day_count} days",
                "postpone_to_working_day": postpone,
                "line_ids": [
                    Command.create(
                        {
                            "value": "percent",
                            "value_amount": 100.0,
                            "nb_days": nb_days,
                            "delay_type": delay_type,
                            "day_count": day_count,
                        }
                    )
                ],
            }
        )

    def _invoice(self, term, invoice_date):
        return self._create_invoice(
            invoice_date=invoice_date,
            invoice_payment_term_id=term,
            invoice_line_ids=[Command.create({"name": "Service", "quantity": 1, "price_unit": 100.0})],
            post=True,
        )

    def test_working_days_over_weekend(self):
        # Friday 2026-03-06 + 3 working days: Monday, Tuesday, Wednesday
        invoice = self._invoice(self._term(3), "2026-03-06")
        self.assertEqual(invoice.invoice_date_due, date(2026, 3, 11))
        term_line = invoice.line_ids.filtered(lambda line: line.display_type == "payment_term")
        self.assertEqual(term_line.date_maturity, date(2026, 3, 11))

    def test_working_days_over_easter(self):
        # Thursday 2026-04-09 + 2 working days: Good Friday, the weekend and Easter Monday are skipped
        invoice = self._invoice(self._term(2), "2026-04-09")
        self.assertEqual(invoice.invoice_date_due, date(2026, 4, 15))

    def test_working_days_over_labour_day(self):
        # Thursday 2026-04-30 + 1 working day: 1 May (Friday) and the weekend are skipped
        invoice = self._invoice(self._term(1), "2026-04-30")
        self.assertEqual(invoice.invoice_date_due, date(2026, 5, 4))

    def test_postpone_calendar_days(self):
        # 2026-03-06 + 15 calendar days = Saturday 2026-03-21
        self.assertEqual(self._invoice(self._term(15, "calendar"), "2026-03-06").invoice_date_due, date(2026, 3, 21))
        postponed = self._invoice(self._term(15, "calendar", postpone=True), "2026-03-06")
        self.assertEqual(postponed.invoice_date_due, date(2026, 3, 23))

    def test_postpone_over_holiday(self):
        # 2026-04-01 + 9 calendar days = Good Friday 2026-04-10: next working day is Tuesday 2026-04-14
        invoice = self._invoice(self._term(9, "calendar", postpone=True), "2026-04-01")
        self.assertEqual(invoice.invoice_date_due, date(2026, 4, 14))

    def test_working_days_after_end_of_month(self):
        # end of March 2026 (Tuesday 31) + 3 working days: April 1, 2, 3
        invoice = self._invoice(self._term(3, delay_type="days_after_end_of_month"), "2026-03-10")
        self.assertEqual(invoice.invoice_date_due, date(2026, 4, 3))

    def test_installments_mixed(self):
        term = self.env["account.payment.term"].create(
            {
                "name": "Mixed",
                "line_ids": [
                    Command.create({"value": "percent", "value_amount": 50.0, "nb_days": 3, "day_count": "working"}),
                    Command.create({"value": "percent", "value_amount": 50.0, "nb_days": 15, "day_count": "calendar"}),
                ],
            }
        )
        invoice = self._invoice(term, "2026-03-06")
        dates = invoice.line_ids.filtered(lambda line: line.display_type == "payment_term").mapped("date_maturity")
        self.assertEqual(sorted(dates), [date(2026, 3, 11), date(2026, 3, 21)])
        self.assertEqual(invoice.invoice_date_due, date(2026, 3, 21))

    def test_company_without_calendar(self):
        self.company.resource_calendar_id = False
        # Monday to Friday with the global holidays of the company: Friday + 1 working day = Monday
        invoice = self._invoice(self._term(1), "2026-03-06")
        self.assertEqual(invoice.invoice_date_due, date(2026, 3, 9))
        # Thursday 2026-04-30 + 1 working day: 1 May is still a holiday
        invoice = self._invoice(self._term(1), "2026-04-30")
        self.assertEqual(invoice.invoice_date_due, date(2026, 5, 4))

    def test_calendar_term_unchanged(self):
        invoice = self._invoice(self._term(3, "calendar"), "2026-03-06")
        self.assertEqual(invoice.invoice_date_due, date(2026, 3, 9))

    def test_legal_ceiling_warning(self):
        self.assertFalse(self._term(40).working_days_warning)
        self.assertTrue(self._term(45).working_days_warning)
        self.assertFalse(self._term(45, "calendar").working_days_warning)

    def test_form_view(self):
        with Form(self.env["account.payment.term"]) as form:
            form.name = "Form term"
            form.postpone_to_working_day = True
            # a new payment term starts with one 100% line
            with form.line_ids.edit(0) as line:
                line.nb_days = 5
                line.day_count = "working"
        term = form.record
        self.assertTrue(term.postpone_to_working_day)
        self.assertEqual(term.line_ids.day_count, "working")
