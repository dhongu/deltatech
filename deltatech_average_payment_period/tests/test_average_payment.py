# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields
from odoo.tests import common, tagged


@tagged("post_install", "-at_install")
class TestAveragePaymentPeriod(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.journal_sale = cls.env["account.journal"].search([("type", "=", "sale")], limit=1)
        cls.journal_bank = cls.env["account.journal"].search([("type", "=", "bank")], limit=1)

    def test_average_payment_period(self):
        # 1. Creează o factură de vânzare (out_invoice)
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal_sale.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test product",
                            "quantity": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        invoice.action_post()

        # 2. Înregistrează o plată pentru această factură peste 10 zile
        payment_date = fields.Date.add(invoice.invoice_date, days=10)

        # Obține liniile de plată ce pot fi reconciliate
        receivable_line = invoice.line_ids.filtered(lambda l: l.account_id.account_type == "asset_receivable")

        # Creează plata folosind account.payment.register pentru simplitate și reconciliere automată
        payment_register = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "journal_id": self.journal_bank.id,
                    "payment_date": payment_date,
                    "amount": invoice.amount_total,
                }
            )
        )
        payment_register.action_create_payments()

        # Verifică dacă factura este plătită și reconciliată
        self.assertEqual(invoice.payment_state, "paid", "Factura ar trebui să fie în starea 'paid'")

        # 3. Verifică calculul payment_days pe liniile facturii
        # Forțăm recalcularea câmpurilor compute store=True dacă e cazul,
        # deși în Odoo 17+ se face automat la flush.
        invoice.invalidate_model(["line_ids"])
        receivable_line = invoice.line_ids.filtered(lambda l: l.account_id.account_type == "asset_receivable")

        for line in receivable_line:
            self.assertTrue(line.full_reconcile_id, "Linia ar trebui să fie reconciliată complet")
            self.assertEqual(line.payment_date, payment_date, "Data plății ar trebui să fie data plății înregistrate")
            self.assertEqual(line.payment_days, 10, "Zilele de plată ar trebui să fie 10")
            self.assertEqual(line.payment_days_simple, 10.0, "Zilele de plată simple ar trebui să fie 10.0")

    def test_report_average_payment(self):
        # Verificăm că raportul (view-ul SQL) poate fi citit fără erori
        self.test_average_payment_period()
        self.env.flush_all()

        report_lines = self.env["account.average.payment.report"].search([("partner_id", "=", self.partner.id)])
        self.assertTrue(
            len(report_lines) > 0, "Raportul ar trebui să conțină cel puțin o linie pentru partenerul de test"
        )

        # Verificăm datele din raport
        for line in report_lines:
            self.assertEqual(line.payment_days, 10, "Zilele de plată în raport ar trebui să fie 10")

        # Verificăm read_group-ul customizat
        group_data = self.env["account.average.payment.report"].read_group(
            [("partner_id", "=", self.partner.id)], ["payment_days", "amount"], ["partner_id"]
        )
        self.assertEqual(group_data[0]["payment_days"], 10.0, "Media zilelor de plată în raport ar trebui să fie 10.0")
