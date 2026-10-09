# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAveragePaymentCompany(AccountTestInvoicingCommon):
    """AVGPAY-002: the report must follow the user's active companies"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_data_2 = cls.setup_other_company()
        cls.company_a = cls.company_data["company"]
        cls.company_b = cls.company_data_2["company"]
        cls.invoice_a = cls._paid_invoice(cls.company_data)
        cls.invoice_b = cls._paid_invoice(cls.company_data_2)
        cls.invoices = cls.invoice_a | cls.invoice_b
        cls.env.flush_all()

        groups = "account.group_account_user"
        cls.user_a = new_test_user(
            cls.env,
            login="avgpay_user_a",
            groups=groups,
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.user_ab = new_test_user(
            cls.env,
            login="avgpay_user_ab",
            groups=groups,
            company_id=cls.company_a.id,
            company_ids=[(6, 0, (cls.company_a | cls.company_b).ids)],
        )

    @classmethod
    def _paid_invoice(cls, company_data):
        company = company_data["company"]
        invoice = cls.init_invoice("out_invoice", amounts=[100.0], post=True, company=company)
        cls.env["account.payment.register"].with_company(company).with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({"journal_id": company_data["default_journal_bank"].id})._create_payments()
        return invoice

    def _report_moves(self, user, companies):
        report = (
            self.env["account.average.payment.report"].with_user(user).with_context(allowed_company_ids=companies.ids)
        )
        rows = report.search([("move_id", "in", self.invoices.ids)])
        groups = report._read_group([("move_id", "in", self.invoices.ids)], ["move_id"], ["payment_days:avg"])
        self.assertEqual({move for move, __ in groups}, set(rows.mapped("move_id")))
        return rows.mapped("move_id")

    def test_invoices_paid_in_both_companies(self):
        self.assertEqual(set(self.invoices.sudo().mapped("payment_state")), {"paid"})
        rows = self.env["account.average.payment.report"].sudo().search([("move_id", "in", self.invoices.ids)])
        self.assertEqual(rows.mapped("move_id"), self.invoices)
        self.assertEqual(rows.mapped("company_id"), self.company_a | self.company_b)

    def test_single_company_user_sees_only_own_company(self):
        self.assertEqual(self._report_moves(self.user_a, self.company_a), self.invoice_a)

    def test_multi_company_user_sees_active_companies(self):
        both = self.company_a | self.company_b
        self.assertEqual(self._report_moves(self.user_ab, both), self.invoices)
        # after switching to company A only, company B rows are hidden
        self.assertEqual(self._report_moves(self.user_ab, self.company_a), self.invoice_a)
