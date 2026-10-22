# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestSaleMarginReportManufacturerPos(TestPoSCommon):
    def setUp(self):
        super().setUp()
        # the orders of the point of sale are in the report only with deltatech_sale_margin_pos
        if "pos_order_id" not in self.env["sale.margin.report"]._fields:
            self.skipTest("deltatech_sale_margin_pos is not installed")
        self.config = self.basic_config
        self.env.user.group_ids |= self.env.ref("sales_team.group_sale_manager")
        self.manufacturer = self.env["res.partner"].create({"name": "Manufacturer TEST", "is_manufacturer": True})
        self.product = self.create_product("Manufacturer POS", self.categ_basic, 100, 60)
        self.product.manufacturer_id = self.manufacturer
        self.open_new_session()

    def test_manufacturer_on_pos_order(self):
        orders = self._create_orders(
            [{"pos_order_lines_ui_args": [(self.product, 2)], "payments": [(self.cash_pm1, 200)]}]
        )
        order = next(iter(orders.values()))
        self.env.flush_all()

        row = self.env["sale.margin.report"].search([("pos_order_id", "=", order.id)])
        self.assertEqual(len(row), 1)
        self.assertEqual(row.manufacturer_id, self.manufacturer)

        groups = self.env["sale.margin.report"].formatted_read_group(
            [("pos_order_id", "=", order.id)], ["manufacturer_id"], ["sale_val:sum"]
        )
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["manufacturer_id"][0], self.manufacturer.id)
        self.assertAlmostEqual(groups[0]["sale_val:sum"], 200)
