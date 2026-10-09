# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestStockPickingReportCompany(TransactionCase):
    """STOCKREPORT-003: the report must follow the user's active companies"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env["res.company"].create({"name": "Report Company B"})
        cls.product = cls.env["product.product"].create(
            {"name": "Report Product", "type": "consu", "is_storable": True, "standard_price": 10.0}
        )
        cls.picking_a = cls._create_done_receipt(cls.company_a)
        cls.picking_b = cls._create_done_receipt(cls.company_b)
        cls.pickings = cls.picking_a | cls.picking_b
        cls.env.flush_all()

        groups = "stock.group_stock_manager"
        cls.user_a = new_test_user(
            cls.env,
            login="report_user_a",
            groups=groups,
            company_id=cls.company_a.id,
            company_ids=[(6, 0, cls.company_a.ids)],
        )
        cls.user_ab = new_test_user(
            cls.env,
            login="report_user_ab",
            groups=groups,
            company_id=cls.company_a.id,
            company_ids=[(6, 0, (cls.company_a | cls.company_b).ids)],
        )

    @classmethod
    def _create_done_receipt(cls, company):
        env = cls.env(context=dict(cls.env.context, allowed_company_ids=company.ids))
        warehouse = env["stock.warehouse"].search([("company_id", "=", company.id)], limit=1)
        picking = env["stock.picking"].create(
            {
                "picking_type_id": warehouse.in_type_id.id,
                "location_id": env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": warehouse.lot_stock_id.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.product.id,
                            "product_uom_qty": 5.0,
                            "location_id": env.ref("stock.stock_location_suppliers").id,
                            "location_dest_id": warehouse.lot_stock_id.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.move_ids.write({"quantity": 5.0, "picked": True})
        picking.button_validate()
        return picking

    def _report_companies(self, user, companies):
        report = self.env["stock.picking.report"].with_user(user).with_context(allowed_company_ids=companies.ids)
        rows = report.search([("picking_id", "in", self.pickings.ids)])
        return rows.mapped("company_id")

    def test_pickings_done_in_both_companies(self):
        self.assertEqual(self.picking_a.state, "done")
        self.assertEqual(self.picking_b.state, "done")
        rows = self.env["stock.picking.report"].sudo().search([("picking_id", "in", self.pickings.ids)])
        self.assertEqual(rows.mapped("company_id"), self.company_a | self.company_b)

    def test_single_company_user_sees_only_own_company(self):
        self.assertEqual(self._report_companies(self.user_a, self.company_a), self.company_a)

    def test_multi_company_user_sees_active_companies(self):
        both = self.company_a | self.company_b
        self.assertEqual(self._report_companies(self.user_ab, both), both)
        # after switching to company A only, company B rows are hidden
        self.assertEqual(self._report_companies(self.user_ab, self.company_a), self.company_a)
