# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleLineLoad(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Customer XLS"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "Product XLS A", "default_code": "XLSA", "list_price": 10}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "Product XLS B", "default_code": "XLSB", "list_price": 20}
        )
        cls.order = cls.env["sale.order"].create({"partner_id": cls.partner.id})

    def _load(self, fields, data):
        lines = self.env["sale.order.line"].with_context(default_order_id=self.order.id)
        result = lines.load(fields, data)
        self.assertFalse([m for m in result["messages"] if m["type"] == "error"], result["messages"])
        return result

    def test_show_order_lines(self):
        action = self.order.show_order_lines()
        self.assertEqual(action["res_model"], "sale.order.line")
        self.assertEqual(action["domain"], [("order_id", "=", self.order.id)])
        view = self.env.ref("deltatech_sale_xls.sale_order_line_tree")
        self.assertEqual(action["views"], [(view.id, "list")])

    def test_import_new_lines(self):
        self._load(
            ["product_id", "product_uom_qty", "price_unit"],
            [["[XLSA] Product XLS A", "2", "15"], ["Product XLS B", "3", "25"]],
        )
        self.assertEqual(len(self.order.order_line), 2)
        line_a = self.order.order_line.filtered(lambda line: line.product_id == self.product_a)
        self.assertEqual(line_a.product_uom_qty, 2)
        self.assertEqual(line_a.price_unit, 15)

    def test_import_update_existing_lines(self):
        self._load(["product_id", "product_uom_qty"], [["[XLSA] Product XLS A", "1"]])
        line = self.order.order_line
        self.assertEqual(len(line), 1)
        # existing product is updated, unknown product and product not on the order are skipped
        self._load(
            ["product_id", "product_uom_qty"],
            [["[XLSA] Product XLS A", "7"], ["Unknown product", "5"], ["[XLSB] Product XLS B", "4"]],
        )
        self.assertEqual(self.order.order_line, line)
        self.assertEqual(line.product_uom_qty, 7)
