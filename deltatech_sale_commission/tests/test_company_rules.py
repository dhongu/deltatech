# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCommissionUsersCompanyRule(AccountTestInvoicingCommon):
    """COMMISSION-003: commission rates are restricted to the allowed companies."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.company_data["company"]
        data_b = cls.setup_other_company()
        cls.company_b = data_b["company"]
        cls.journal_a = cls.company_data["default_journal_sale"]
        cls.journal_b = data_b["default_journal_sale"]
        cls.manager_a = new_test_user(
            cls.env,
            login="commission003_manager_a",
            groups="sales_team.group_sale_salesman,deltatech_sale_commission.group_commission_manager",
            company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )
        salesman = new_test_user(cls.env, login="commission003_salesman", groups="sales_team.group_sale_salesman")
        salesman_b = new_test_user(cls.env, login="commission003_salesman_b", groups="sales_team.group_sale_salesman")
        Rates = cls.env["commission.users"].sudo()
        cls.rate_a = Rates.create(
            {"user_id": salesman.id, "rate": 0.01, "journal_id": cls.journal_a.id, "company_id": cls.company_a.id}
        )
        cls.rate_b = Rates.create(
            {"user_id": salesman_b.id, "rate": 0.02, "journal_id": cls.journal_b.id, "company_id": cls.company_b.id}
        )
        cls.rate_a = cls.rate_a.sudo(False)
        cls.rate_b = cls.rate_b.sudo(False)

    def test_manager_sees_only_allowed_company(self):
        rates = self.env["commission.users"].with_user(self.manager_a).search([])
        self.assertIn(self.rate_a, rates)
        self.assertNotIn(self.rate_b, rates)

    def test_manager_cannot_touch_other_company(self):
        other = self.rate_b.with_user(self.manager_a)
        with self.assertRaises(AccessError):
            other.read(["rate"])
        with self.assertRaises(AccessError):
            other.write({"rate": 0.5})
        with self.assertRaises(AccessError):
            other.unlink()
        self.assertEqual(self.rate_b.sudo().rate, 0.02)

    def test_manager_cannot_create_or_move_to_other_company(self):
        Rates = self.env["commission.users"].with_user(self.manager_a)
        with self.assertRaises(AccessError):
            Rates.create(
                {
                    "user_id": self.manager_a.id,
                    "rate": 0.5,
                    "journal_id": self.journal_b.id,
                    "company_id": self.company_b.id,
                }
            )
        with self.assertRaises(AccessError):
            self.rate_a.with_user(self.manager_a).write(
                {"journal_id": self.journal_b.id, "company_id": self.company_b.id}
            )
        self.assertEqual(self.rate_a.sudo().company_id, self.company_a)

    def test_manager_edits_own_company(self):
        self.rate_a.with_user(self.manager_a).write({"rate": 0.03})
        self.assertEqual(self.rate_a.sudo().rate, 0.03)
