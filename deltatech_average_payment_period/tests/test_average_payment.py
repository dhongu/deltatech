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

        cls.outstanding_account = cls.env["account.account"].create(
            {
                "name": "Outstanding Receipts (test)",
                "code": "TESTOUT1",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        cls.journal_bank.inbound_payment_method_line_ids[:1].payment_account_id = cls.outstanding_account

    def _stored_payment_date(self, line):
        # payment_date din nucleul Odoo 19 suprascrie citirea prin ORM; citim coloana stocată
        self.env.flush_all()
        self.env.cr.execute("SELECT payment_date FROM account_move_line WHERE id = %s", [line.id])
        return self.env.cr.fetchone()[0]

    def _create_paid_invoice(self, days=10, price_unit=100.0):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "journal_id": self.journal_sale.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (0, 0, {"name": "Test product", "quantity": 1, "price_unit": price_unit}),
                ],
            }
        )
        invoice.action_post()
        payment_date = fields.Date.add(invoice.invoice_date, days=days)
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
        receivable_line = invoice.line_ids.filtered(lambda l: l.account_id.account_type == "asset_receivable")
        return invoice, receivable_line, payment_date

    def test_average_payment_period(self):
        invoice, receivable_line, payment_date = self._create_paid_invoice()

        # Verifică dacă factura este plătită și reconciliată
        self.assertIn(invoice.payment_state, ("paid", "in_payment"), "Factura ar trebui să fie plătită")

        # Verifică calculul payment_days pe liniile facturii
        # Forțăm recalcularea câmpurilor compute store=True dacă e cazul,
        # deși în Odoo 17+ se face automat la flush.
        invoice.invalidate_model(["line_ids"])
        receivable_line = invoice.line_ids.filtered(lambda l: l.account_id.account_type == "asset_receivable")

        for line in receivable_line:
            self.assertTrue(line.full_reconcile_id, "Linia ar trebui să fie reconciliată complet")
            self.assertEqual(
                self._stored_payment_date(line), payment_date, "Data plății ar trebui să fie data plății înregistrate"
            )
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

        # Verificăm _read_group-ul customizat
        group_data = self.env["account.average.payment.report"]._read_group(
            [("partner_id", "=", self.partner.id)], ["partner_id"], ["payment_days:avg"]
        )
        self.assertEqual(group_data[0][1], 10.0, "Media zilelor de plată în raport ar trebui să fie 10.0")

    def test_unreconcile_clears_payment_fields(self):
        """AVGPAY-001: câmpurile se golesc când dispare reconcilierea completă"""
        invoice, receivable_line, payment_date = self._create_paid_invoice()
        self.assertEqual(receivable_line.payment_days, 10)

        # contrapartida (linia de plată), o păstrăm ca să putem reconcilia din nou
        counterpart = receivable_line.full_reconcile_id.reconciled_line_ids - receivable_line

        # 1. anulăm reconcilierea
        receivable_line.remove_move_reconcile()
        self.env.flush_all()
        receivable_line.invalidate_recordset()

        self.assertFalse(receivable_line.full_reconcile_id)
        self.assertFalse(self._stored_payment_date(receivable_line))
        self.assertEqual(receivable_line.payment_days, 0)
        self.assertEqual(receivable_line.payment_days_simple, 0.0)

        # 2. reconciliem din nou: valorile trebuie să revină
        (receivable_line | counterpart).reconcile()
        self.env.flush_all()
        receivable_line.invalidate_recordset()

        self.assertTrue(receivable_line.full_reconcile_id)
        self.assertEqual(self._stored_payment_date(receivable_line), payment_date)
        self.assertEqual(receivable_line.payment_days, 10)
        self.assertEqual(receivable_line.payment_days_simple, 10.0)

    def test_report_weighted_average_in_pivot(self):
        """Pivotul (_read_grouping_sets) și graficul (_read_group) dau aceeași medie ponderată"""
        small, __, __ = self._create_paid_invoice(days=10, price_unit=100.0)
        big, __, __ = self._create_paid_invoice(days=30, price_unit=200.0)
        self.env.flush_all()
        a1, a2 = small.amount_total, big.amount_total
        expected = (a1 * 10 + a2 * 30) / (a1 + a2)

        report = self.env["account.average.payment.report"]
        domain = [("partner_id", "=", self.partner.id)]
        pivot = report._read_grouping_sets(domain, [["partner_id"], []], ["payment_days:avg"])
        self.assertAlmostEqual(pivot[0][0][1], expected, places=2, msg="Pivot: media pe partener")
        self.assertAlmostEqual(pivot[1][0][0], expected, places=2, msg="Pivot: totalul")
        graph = report._read_group(domain, ["partner_id"], ["payment_days:avg"])
        self.assertAlmostEqual(graph[0][1], expected, places=2, msg="Grafic: media pe partener")
