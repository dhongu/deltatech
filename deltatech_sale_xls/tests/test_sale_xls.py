# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleXls(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner = cls.env["res.partner"].create({"name": "XLS Test Partner"})
        cls.product_a = cls.env["product.product"].create(
            {"name": "XLS Product A", "default_code": "XLSA", "type": "consu", "list_price": 10.0}
        )
        cls.product_b = cls.env["product.product"].create(
            {"name": "XLS Product B", "default_code": "XLSB", "type": "consu", "list_price": 20.0}
        )
        cls.product_c = cls.env["product.product"].create(
            {"name": "XLS Product C", "type": "consu", "list_price": 30.0}
        )

    def _create_order(self, products=None):
        lines = [(0, 0, {"product_id": p.id, "product_uom_qty": 1.0, "price_unit": 5.0}) for p in products or []]
        return self.env["sale.order"].create({"partner_id": self.partner.id, "order_line": lines})

    def test_show_order_lines(self):
        order = self._create_order([self.product_a])
        action = order.show_order_lines()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "sale.order.line")
        self.assertEqual(action["domain"], [("order_id", "=", order.id)])
        self.assertEqual(action["context"]["default_order_id"], order.id)
        view = self.env.ref("deltatech_sale_xls.sale_order_line_tree")
        self.assertEqual(action["views"], [(view.id, "list")])

    def test_load_update_existing_lines(self):
        """Lines matching products of the order are updated, the others are dropped."""
        order = self._create_order([self.product_a, self.product_c])
        line_a = order.order_line.filtered(lambda line: line.product_id == self.product_a)
        line_c = order.order_line.filtered(lambda line: line.product_id == self.product_c)
        fields = ["product_id", "product_uom_qty"]
        data = [
            ["[XLSA] XLS Product A", "7"],  # matched by code
            ["XLS Product C", "4"],  # matched by name
            ["[XLSB] XLS Product B", "3"],  # product exists but not on order
            ["[NOPE] Unknown product", "2"],  # product does not exist
        ]
        result = self.env["sale.order.line"].with_context(default_order_id=order.id).load(fields, data)
        self.assertFalse([m for m in result["messages"] if m["type"] == "error"], result["messages"])
        self.assertEqual(len(data), 2)
        self.assertIn(".id", fields)
        self.assertEqual(line_a.product_uom_qty, 7.0)
        self.assertEqual(line_c.product_uom_qty, 4.0)
        self.assertEqual(len(order.order_line), 2)
        self.assertNotIn(self.product_b, order.order_line.product_id)

    def test_load_existing_lines_without_product_column(self):
        order = self._create_order([self.product_a])
        line = order.order_line
        fields = ["product_uom_qty"]
        data = [["9"]]
        # without a product column the ".id" stays empty and no order_id is added, so the standard
        # load would try to create an orphan line; only the preprocessing is checked here
        with patch("odoo.models.BaseModel.load", autospec=True) as mock_load:
            mock_load.return_value = {"ids": [], "messages": []}
            self.env["sale.order.line"].with_context(active_id=order.id).load(fields, data)
        mock_load.assert_called_once()
        self.assertEqual(fields, ["product_uom_qty", ".id"])
        self.assertEqual(data, [["9", ""]])
        self.assertEqual(order.order_line, line)

    def test_load_new_lines_in_empty_order(self):
        order = self._create_order()
        fields = ["product_id", "product_uom_qty", "price_unit"]
        data = [["[XLSA] XLS Product A", "2", "11"], ["XLS Product B", "3", "12"]]
        with patch.object(
            type(self.env["sale.order.line"]), "use_specific_price_formula", autospec=True
        ) as mock_formula:
            result = self.env["sale.order.line"].with_context(default_order_id=order.id).load(fields, data)
        mock_formula.assert_called_once()
        self.assertFalse([m for m in result["messages"] if m["type"] == "error"], result["messages"])
        self.assertIn("order_id", fields)
        self.assertEqual(len(order.order_line), 2)
        self.assertEqual(order.order_line.product_id, self.product_a | self.product_b)
        line_b = order.order_line.filtered(lambda line: line.product_id == self.product_b)
        self.assertEqual(line_b.product_uom_qty, 3.0)
        self.assertEqual(line_b.price_unit, 12.0)

    def test_load_new_lines_without_price(self):
        order = self._create_order()
        fields = ["product_id", "product_uom_qty"]
        data = [["XLS Product C", "5"]]
        result = self.env["sale.order.line"].with_context(default_order_id=order.id).load(fields, data)
        self.assertFalse([m for m in result["messages"] if m["type"] == "error"], result["messages"])
        self.assertEqual(order.order_line.product_id, self.product_c)
        self.assertEqual(order.order_line.product_uom_qty, 5.0)

    def test_use_specific_price_formula_default(self):
        data = [["x", "1"]]
        self.assertIsNone(self.env["sale.order.line"].use_specific_price_formula(data, 1))
        self.assertEqual(data, [["x", "1"]])

    def test_load_order_from_order_id_column(self):
        """Without context the order is taken from the order_id column (database id)."""
        order = self._create_order([self.product_a])
        line = order.order_line
        fields = ["order_id", "product_id", "product_uom_qty"]
        data = [[order.id, "[XLSA] XLS Product A", "6"]]
        with patch("odoo.models.BaseModel.load", autospec=True) as mock_load:
            mock_load.return_value = {"ids": [], "messages": []}
            self.env["sale.order.line"].load(fields, data)
        mock_load.assert_called_once()
        self.assertEqual(fields, ["order_id", "product_id", "product_uom_qty", ".id"])
        self.assertEqual(data[0][-1], str(line.id))

    def test_load_without_order(self):
        """Without any order the import falls through to the standard load, unchanged."""
        fields = ["product_id", "product_uom_qty"]
        data = [["XLS Product A", "1"]]
        with patch("odoo.models.BaseModel.load", autospec=True) as mock_load:
            mock_load.return_value = {"ids": [], "messages": []}
            self.env["sale.order.line"].load(fields, data)
        mock_load.assert_called_once()
        self.assertEqual(fields, ["product_id", "product_uom_qty"])
        self.assertEqual(data, [["XLS Product A", "1"]])

    def test_parse_import_data(self):
        """The override only delegates to super; BaseModel has no such method (base_import defines it
        on base_import.import), so calling it on sale.order.line raises AttributeError."""
        with self.assertRaises(AttributeError):
            self.env["sale.order.line"]._parse_import_data([["2"]], ["product_uom_qty"], {})
