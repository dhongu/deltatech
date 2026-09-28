# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
from dateutil.relativedelta import relativedelta

from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCustomerSegment(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids += cls.env.ref("deltatech_customer_segment.group_customer_segment_director")
        cls.env.user.group_ids += cls.env.ref("sales_team.group_sale_manager")
        cls.today = fields.Date.today()
        cls.Segment = cls.env["deltatech.customer.segment"]
        cls.config = cls.env["deltatech.customer.segment.config"]._get_for_company(cls.env.company)
        cls.product = cls.env["product.product"].create({"name": "Segment product", "type": "service"})
        cls.salesman = cls.env["res.users"].create(
            {
                "name": "Segment agent",
                "login": "segment_agent",
                "group_ids": [
                    Command.link(cls.env.ref("base.group_user").id),
                    Command.link(cls.env.ref("deltatech_customer_segment.group_customer_segment_agent").id),
                ],
            }
        )

    @classmethod
    def _customer(cls, name, **vals):
        return cls.env["res.partner"].create({"name": name, "is_company": True, **vals})

    def _invoice(self, partner, days_ago, amount, move_type="out_invoice", due_days_ago=None, currency=None, post=True):
        invoice_date = self.today - relativedelta(days=days_ago)
        due = self.today - relativedelta(days=due_days_ago) if due_days_ago is not None else invoice_date
        move = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": partner.id,
                "invoice_date": invoice_date,
                "invoice_date_due": due,
                "currency_id": (currency or self.env.company.currency_id).id,
                "invoice_line_ids": [
                    Command.create({"product_id": self.product.id, "price_unit": amount, "tax_ids": [Command.clear()]})
                ],
            }
        )
        if post:
            move.action_post()
        return move

    def _pay(self, invoice):
        self.env["account.payment.register"].with_context(active_model="account.move", active_ids=invoice.ids).create(
            {}
        )._create_payments()

    def _recompute(self):
        self.Segment._recompute_company(self.env.company)

    def _row(self, partner):
        return self.Segment.search([("partner_id", "=", partner.id), ("company_id", "=", self.env.company.id)])

    # ------------------------------------------------------------------
    # Rhythm
    # ------------------------------------------------------------------
    def test_rhythm_is_measured_between_purchases(self):
        partner = self._customer("Weekly buyer")
        for days_ago in (40, 30, 20, 10):
            self._invoice(partner, days_ago, 100)
        self._recompute()
        row = self._row(partner)
        self.assertEqual(row.interval_days, 10)
        self.assertEqual(row.days_since, 10)
        self.assertEqual(row.sale_count, 4)
        self.assertEqual(row.first_date, self.today - relativedelta(days=40))

    def test_segment_is_judged_against_own_rhythm(self):
        weekly = self._customer("Weekly, silent for 25 days")
        for days_ago in (60, 53, 46, 39, 32, 25):
            self._invoice(weekly, days_ago, 100)
        quarterly = self._customer("Quarterly, silent for 60 days")
        for days_ago in (420, 330, 240, 150, 60):
            self._invoice(quarterly, days_ago, 100)
        self._recompute()
        # 25 days > 3 x 7: the weekly customer broke his rhythm
        self.assertEqual(self._row(weekly).rhythm_segment, "dormant")
        # 60 days < 1.5 x 90: the quarterly customer is still on time
        self.assertEqual(self._row(quarterly).rhythm_segment, "active")

    def test_lost_after_one_year(self):
        partner = self._customer("Gone")
        for days_ago in (500, 450, 400):
            self._invoice(partner, days_ago, 100)
        self._recompute()
        row = self._row(partner)
        self.assertEqual(row.rhythm_segment, "lost")
        self.assertEqual(row.classification, "inactive_3")

    def test_new_customer_judged_by_relationship_age(self):
        partner = self._customer("Newcomer")
        self._invoice(partner, 20, 100)
        self._recompute()
        row = self._row(partner)
        self.assertEqual(row.rhythm_segment, "new")
        self.assertFalse(row.interval_days, "A single purchase has no measured rhythm")

    def test_prospect_has_no_row(self):
        partner = self._customer("Prospect")
        self._invoice(partner, 5, 100, post=False)
        self._recompute()
        self.assertFalse(self._row(partner))

    def test_cancelled_sales_remove_the_row(self):
        partner = self._customer("Cancelled")
        invoice = self._invoice(partner, 5, 100)
        self._recompute()
        self.assertTrue(self._row(partner))
        invoice.button_draft()
        invoice.button_cancel()
        self._recompute()
        self.assertFalse(self._row(partner))

    # ------------------------------------------------------------------
    # Amounts
    # ------------------------------------------------------------------
    def test_amounts_untaxed_in_company_currency_net_of_refunds(self):
        tax = self.company_data["default_tax_sale"]
        partner = self._customer("Taxed")
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "invoice_date": self.today - relativedelta(days=10),
                "invoice_line_ids": [
                    Command.create(
                        {"product_id": self.product.id, "price_unit": 1000, "tax_ids": [Command.set(tax.ids)]}
                    )
                ],
            }
        )
        invoice.action_post()
        self._invoice(partner, 5, 200, move_type="out_refund")
        eur = self.setup_other_currency("EUR", rates=[("1900-01-01", 0.2)])
        self._invoice(partner, 3, 100, currency=eur)
        self._recompute()
        row = self._row(partner)
        # 1000 without VAT, minus the 200 credit note, plus 100 EUR = 500 in company currency
        self.assertAlmostEqual(row.revenue_total, 1300.0)
        self.assertEqual(row.sale_count, 2, "A credit note is not a purchase")

    def test_overdue_only_from_open_customer_invoices(self):
        partner = self._customer("Late payer")
        self._invoice(partner, 100, 300, due_days_ago=70)
        self._invoice(partner, 90, 200, due_days_ago=60)
        paid = self._invoice(partner, 80, 400, due_days_ago=50)
        self._pay(paid)
        self._invoice(partner, 5, 150, due_days_ago=-25)
        self._recompute()
        row = self._row(partner)
        self.assertAlmostEqual(row.open_balance, 650.0)
        self.assertAlmostEqual(row.overdue_amount, 500.0)
        self.assertEqual(row.overdue_invoice_count, 2)
        self.assertEqual(row.max_overdue_days, 70)

    def test_payment_risk_classification(self):
        partner = self._customer("Risky")
        for days_ago in (40, 30, 20):
            self._invoice(partner, days_ago, 100, due_days_ago=days_ago - 5)
        self.config.write({"top_min_count": 0, "top_share_pct": 0})
        self._recompute()
        self.assertEqual(self._row(partner).classification, "overdue_risk")

    def test_declining_customer(self):
        partner = self._customer("Declining")
        # previous 6-month window: 10000; current window: 2000
        self._invoice(partner, 300, 5000)
        self._invoice(partner, 250, 5000)
        self._invoice(partner, 30, 2000)
        self._pay_all(partner)
        self.config.write({"top_min_count": 0, "top_share_pct": 0})
        self._recompute()
        row = self._row(partner)
        self.assertEqual(row.classification, "declining")
        self.assertAlmostEqual(row.growth_pct, -80.0)

    def _pay_all(self, partner):
        invoices = self.env["account.move"].search(
            [("partner_id", "=", partner.id), ("state", "=", "posted"), ("payment_state", "=", "not_paid")]
        )
        for invoice in invoices:
            self._pay(invoice)

    def test_thresholds_come_from_settings(self):
        partner = self._customer("Quiet for 45 days")
        for days_ago in (200, 150, 100, 45):
            self._invoice(partner, days_ago, 100)
        self._pay_all(partner)
        self.config.write({"top_min_count": 0, "top_share_pct": 0})
        self._recompute()
        self.assertNotIn(self._row(partner).classification, ("inactive_1", "inactive_2", "inactive_3"))
        self.config.inactive_days_1 = 40
        self._recompute()
        self.assertEqual(self._row(partner).classification, "inactive_1")

    def test_top_customer(self):
        big = self._customer("Big")
        small = self._customer("Small")
        for days_ago in (30, 20, 10):
            self._invoice(big, days_ago, 10000)
            self._invoice(small, days_ago, 10)
        self._pay_all(big)
        self._pay_all(small)
        self.config.write({"top_min_count": 1, "top_share_pct": 0})
        self._recompute()
        self.assertTrue(self._row(big).is_top_client)
        self.assertEqual(self._row(big).classification, "top_client")
        self.assertFalse(self._row(small).is_top_client)

    def test_orders_basis(self):
        self.config.basis = "orders"
        partner = self._customer("Orders customer")
        for days_ago in (30, 10):
            order = self.env["sale.order"].create(
                {
                    "partner_id": partner.id,
                    "order_line": [
                        Command.create({"product_id": self.product.id, "price_unit": 250, "tax_ids": [Command.clear()]})
                    ],
                }
            )
            order.action_confirm()
            order.date_order = fields.Datetime.now() - relativedelta(days=days_ago)
        self._recompute()
        row = self._row(partner)
        self.assertEqual(row.basis, "orders")
        self.assertEqual(row.sale_count, 2)
        self.assertAlmostEqual(row.revenue_total, 500.0)
        self.assertEqual(row.interval_days, 20)

    # ------------------------------------------------------------------
    # Partners, companies, access
    # ------------------------------------------------------------------
    def test_contact_sales_roll_up_to_the_company(self):
        partner = self._customer("Parent company")
        contact = self.env["res.partner"].create({"name": "Buyer", "parent_id": partner.id, "type": "contact"})
        self._invoice(contact, 20, 100)
        self._invoice(partner, 10, 100)
        self._recompute()
        self.assertEqual(self._row(partner).sale_count, 2)
        self.assertFalse(self._row(contact))

    def test_company_isolation(self):
        partner = self._customer("Shared customer")
        self._invoice(partner, 10, 100)
        other = self.setup_other_company()["company"]
        self.env["deltatech.customer.segment"]._recompute_company(other)
        self._recompute()
        rows = self.Segment.search([("partner_id", "=", partner.id)])
        self.assertEqual(rows.company_id, self.env.company)
        self.assertAlmostEqual(rows.revenue_total, 100.0)

    def test_only_companies(self):
        person = self.env["res.partner"].create({"name": "Retail buyer"})
        self._invoice(person, 10, 100)
        self._recompute()
        self.assertTrue(self._row(person))
        self.config.only_companies = True
        self._recompute()
        self.assertFalse(self._row(person))

    def test_recompute_is_idempotent(self):
        partner = self._customer("Stable")
        for days_ago in (30, 20, 10):
            self._invoice(partner, days_ago, 100)
        self._recompute()
        row = self._row(partner)
        first = row.read(["sale_count", "revenue_total", "classification", "rhythm_segment"])
        self._recompute()
        self.assertEqual(self._row(partner), row)
        self.assertEqual(row.read(["sale_count", "revenue_total", "classification", "rhythm_segment"]), first)

    def test_agent_sees_only_own_customers(self):
        own = self._customer("Own", user_id=self.salesman.id)
        other = self._customer("Other")
        self._invoice(own, 10, 100)
        self._invoice(other, 10, 100)
        self._recompute()
        visible = self.Segment.with_user(self.salesman).search([])
        self.assertIn(own, visible.partner_id)
        self.assertNotIn(other, visible.partner_id)

    def test_install_does_not_compute(self):
        cron = self.env.ref("deltatech_customer_segment.ir_cron_customer_segment_recompute")
        self.assertEqual(cron.code, "model._cron_recompute()")
        self.assertTrue(cron.active)

    def test_settings_validation(self):
        with self.assertRaises(ValidationError):
            self.config.inactive_days_2 = 10
