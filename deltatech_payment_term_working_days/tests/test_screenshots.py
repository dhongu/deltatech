# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
#
# Screenshots of the module, generated during the tests, in Romanian.
#
# Seeds: the 2026 Romanian public holidays on the company, a payment term with a line in
# working days and a line in calendar days moved to the next working day, a 45 working
# days term (legal ceiling warning) and an invoice issued before Easter with the first term.
#
# Run:
#   ./odoo/odoo-bin -c odoo.conf -d <db> -i deltatech_payment_term_working_days,l10n_ro_doc_screenshots \
#       --test-tags=fise_screenshots --stop-after-init
import unittest
from datetime import date, datetime, time, timedelta

import pytz

from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

try:
    from odoo.addons.l10n_ro_doc_screenshots.tests.screenshot_case import ScreenshotCase
except ImportError:
    ScreenshotCase = None

RO_HOLIDAYS_2026 = [
    (date(2026, 1, 1), "Anul Nou"),
    (date(2026, 1, 2), "Anul Nou (a doua zi)"),
    (date(2026, 1, 6), "Boboteaza"),
    (date(2026, 1, 7), "Sfântul Ioan Botezătorul"),
    (date(2026, 1, 24), "Ziua Unirii Principatelor Române"),
    (date(2026, 4, 10), "Vinerea Mare"),
    (date(2026, 4, 12), "Paștele"),
    (date(2026, 4, 13), "A doua zi de Paști"),
    (date(2026, 5, 1), "Ziua Muncii"),
    (date(2026, 5, 31), "Rusaliile"),
    (date(2026, 6, 1), "Ziua Copilului, A doua zi de Rusalii"),
    (date(2026, 8, 15), "Adormirea Maicii Domnului"),
    (date(2026, 11, 30), "Sfântul Andrei"),
    (date(2026, 12, 1), "Ziua Națională a României"),
    (date(2026, 12, 25), "Crăciunul"),
    (date(2026, 12, 26), "A doua zi de Crăciun"),
]


@tagged("-at_install", "post_install", "fise_screenshots")
class TestPaymentTermWorkingDaysScreenshots(AccountTestInvoicingCommon, ScreenshotCase or object):
    screenshots_module = "deltatech_payment_term_working_days"

    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        if ScreenshotCase is None:
            raise unittest.SkipTest("l10n_ro_doc_screenshots indisponibil")
        super().setUpClass()
        company = cls.prepare_ro_company(name="Demo Termene SRL")
        cls.env.ref("base.user_admin").write({"company_ids": [(4, company.id)], "company_id": company.id})
        env = cls.env

        calendar = company.resource_calendar_id
        calendar.tz = "Europe/Bucharest"
        tz = pytz.timezone("Europe/Bucharest")
        env["resource.calendar.leaves"].create(
            [
                {
                    "name": name,
                    "company_id": company.id,
                    "calendar_id": False,
                    "date_from": tz.localize(datetime.combine(day, time.min)).astimezone(pytz.utc).replace(tzinfo=None),
                    "date_to": tz.localize(datetime.combine(day, time.max) - timedelta(microseconds=999999))
                    .astimezone(pytz.utc)
                    .replace(tzinfo=None),
                    "time_type": "leave",
                }
                for day, name in RO_HOLIDAYS_2026
            ]
        )

        cls.term = env["account.payment.term"].create(
            {
                "name": "Avans 50% în 3 zile lucrătoare, rest la 30 de zile",
                "postpone_to_working_day": True,
                "line_ids": [
                    Command.create({"value": "percent", "value_amount": 50.0, "nb_days": 3, "day_count": "working"}),
                    Command.create({"value": "percent", "value_amount": 50.0, "nb_days": 30, "day_count": "calendar"}),
                ],
            }
        )
        cls.term_long = env["account.payment.term"].create(
            {
                "name": "45 de zile lucrătoare",
                "line_ids": [
                    Command.create({"value": "percent", "value_amount": 100.0, "nb_days": 45, "day_count": "working"})
                ],
            }
        )
        product = env["product.product"].create({"name": "Servicii de consultanță", "type": "service"})
        partner = env["res.partner"].create(
            {"name": "Client Demo SRL", "country_id": env.ref("base.ro").id, "lang": "ro_RO"}
        )
        # Thursday before Easter: the first rate skips Good Friday, Easter and Easter Monday,
        # the second one (30 days, Saturday 09.05) moves to Monday 11.05
        cls.invoice = cls._create_invoice(
            partner_id=partner,
            invoice_date="2026-04-09",
            invoice_payment_term_id=cls.term,
            invoice_line_ids=[Command.create({"product_id": product.id, "quantity": 1, "price_unit": 1000.0})],
            post=True,
        )

    def test_capture_fise(self):
        # opened through the action, else the breadcrumb shows the "New" chip on a saved record
        terms = self.env.ref("account.action_payment_term_form").id
        # the printed invoice lists the installments with their due dates
        invoice_shot = self.report_shot("account.report_invoice", self.invoice, "working_days_invoice_due_dates.png")
        self.capture_screenshots(
            [
                {
                    "url": f"action={terms}&id={self.term.id}&model=account.payment.term&view_type=form",
                    "name": "working_days_payment_term.png",
                    "wait": ".o_form_view",
                    "highlight": [
                        "div[name='line_ids'] td[name='day_count']",
                        "div[name='postpone_to_working_day']",
                    ],
                    "settle": 2000,
                    "full": True,
                },
                {
                    "url": f"action={terms}&id={self.term_long.id}&model=account.payment.term&view_type=form",
                    "name": "working_days_legal_warning.png",
                    "wait": ".o_form_view",
                    "highlight": [".o_form_sheet .alert-warning"],
                    "settle": 2000,
                    "full": True,
                },
                invoice_shot,
            ],
            viewport=(1500, 1000),
        )
