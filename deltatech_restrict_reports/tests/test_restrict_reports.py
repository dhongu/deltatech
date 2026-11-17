# Copyright (C) 2026 Terrabit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import new_test_user, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

BASE_GROUPS = "sales_team.group_sale_salesman_all_leads,account.group_account_invoice"


@tagged("post_install", "-at_install")
class TestRestrictReports(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_none = new_test_user(cls.env, login="rr_none", groups=BASE_GROUPS)
        cls.user_own = new_test_user(
            cls.env,
            login="rr_own",
            groups=BASE_GROUPS + ",deltatech_restrict_reports.group_restrict_reports_own",
        )
        cls.user_all = new_test_user(
            cls.env,
            login="rr_all",
            groups=BASE_GROUPS + ",deltatech_restrict_reports.group_restrict_reports_all",
        )
        for user in cls.user_none | cls.user_own | cls.user_all:
            user.write({"company_ids": [(6, 0, cls.company.ids)], "company_id": cls.company.id})

        cls.customer = cls.env["res.partner"].create({"name": "Restrict Reports Customer"})
        cls.product = cls.env["product.product"].create({"name": "Restrict Reports Product", "list_price": 100.0})

        cls.order_own = cls._create_order(cls.user_own)
        cls.order_other = cls._create_order(cls.user_all)
        cls.invoice_own = cls._create_restrict_invoice(cls.user_own)
        cls.invoice_other = cls._create_restrict_invoice(cls.user_all)
        cls.env.flush_all()

    @classmethod
    def _create_order(cls, salesperson):
        return (
            cls.env["sale.order"]
            .sudo()
            .create(
                {
                    "partner_id": cls.customer.id,
                    "user_id": salesperson.id,
                    "company_id": cls.company.id,
                    "order_line": [(0, 0, {"product_id": cls.product.id, "product_uom_qty": 1})],
                }
            )
        )

    @classmethod
    def _create_restrict_invoice(cls, salesperson):
        return cls._create_invoice(
            partner_id=cls.customer.id,
            invoice_user_id=salesperson.id,
            invoice_line_ids=[cls._prepare_invoice_line(product_id=cls.product, price_unit=100.0)],
            post=True,
        )

    def _sale_salespersons(self, user):
        lines = self.env["sale.report"].with_user(user).search([("partner_id", "=", self.customer.id)])
        return lines.mapped("user_id")

    def _invoice_salespersons(self, user):
        lines = self.env["account.invoice.report"].with_user(user).search([("partner_id", "=", self.customer.id)])
        return lines.mapped("invoice_user_id")

    def test_sale_report_tiers(self):
        self.assertFalse(self._sale_salespersons(self.user_none))
        self.assertEqual(self._sale_salespersons(self.user_own), self.user_own)
        self.assertEqual(self._sale_salespersons(self.user_all), self.user_own | self.user_all)

    def test_invoice_report_tiers(self):
        self.assertFalse(self._invoice_salespersons(self.user_none))
        self.assertEqual(self._invoice_salespersons(self.user_own), self.user_own)
        self.assertEqual(self._invoice_salespersons(self.user_all), self.user_own | self.user_all)

    def test_report_actions_restricted(self):
        group_own = self.env.ref("deltatech_restrict_reports.group_restrict_reports_own")
        for xmlid in (
            "sale.action_order_report_all",
            "sale.action_order_report_salesperson",
            "sale.action_order_report_products",
            "sale.action_order_report_customers",
            "account.action_account_invoice_report_all",
            "account.action_account_invoice_report_all_supp",
        ):
            self.assertEqual(self.env.ref(xmlid).group_ids, group_own, xmlid)
