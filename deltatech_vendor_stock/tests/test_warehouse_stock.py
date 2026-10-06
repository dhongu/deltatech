# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWarehouseStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Vendor Stock Customer"})
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.company.id)], limit=1)
        cls.warehouse_2 = cls.env["stock.warehouse"].create(
            {"name": "Vendor Stock WH 2", "code": "VSW2", "company_id": cls.company.id}
        )
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.products = cls.env["product.product"].create(
            [{"name": f"Vendor Stock Product {index}", "is_storable": True} for index in range(6)]
        )
        cls.product = cls.products[0]
        for product in cls.products:
            cls._set_stock(product, cls.warehouse, 5)
            cls._set_stock(product, cls.warehouse_2, 24)
        cls.service = cls.env["product.product"].create({"name": "Vendor Stock Service", "type": "service"})

    @classmethod
    def _set_stock(cls, product, warehouse, quantity):
        cls.env["stock.quant"]._update_available_quantity(product, warehouse.lot_stock_id, quantity)

    def _order(self, products, **line_values):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.warehouse.id,
                "order_line": [
                    (0, 0, dict({"product_id": product.id, "product_uom_qty": 1}, **line_values))
                    for product in products
                ],
            }
        )

    def test_lists_each_warehouse_of_the_company(self):
        line = self._order(self.product).order_line
        self.assertIn(f"{self.warehouse.code}: 5", line.warehouse_stock)
        self.assertIn("VSW2: 24", line.warehouse_stock)

    def test_ignores_warehouses_of_other_companies(self):
        other_company = self.env["res.company"].create({"name": "Vendor Stock Other Company"})
        other_warehouse = self.env["stock.warehouse"].search([("company_id", "=", other_company.id)], limit=1)
        other_warehouse.code = "VSOC"
        self._set_stock(self.product, other_warehouse, 99)
        line = self._order(self.product).order_line
        self.assertNotIn("VSOC", line.warehouse_stock)
        self.assertIn("VSW2: 24", line.warehouse_stock)

    def test_quantities_in_line_uom(self):
        line = self._order(self.product, product_uom=self.uom_dozen.id).order_line
        self.assertIn("VSW2: 2", line.warehouse_stock)
        self.assertIn(self.uom_dozen.name, line.warehouse_stock)

    def test_single_warehouse_shows_nothing(self):
        other_company = self.env["res.company"].create({"name": "Vendor Stock Single Warehouse"})
        other_warehouse = self.env["stock.warehouse"].search([("company_id", "=", other_company.id)])
        self.assertEqual(len(other_warehouse), 1)
        self._set_stock(self.product, other_warehouse, 3)
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": other_company.id,
                "warehouse_id": other_warehouse.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1})],
            }
        )
        self.assertFalse(order.order_line.warehouse_stock)

    def test_service_line_not_computed(self):
        line = self._order(self.service).order_line
        self.assertFalse(line.warehouse_stock)

    def test_queries_do_not_grow_with_lines(self):
        def count_queries(lines):
            # a fresh browse, as the form loads the lines; the recordset returned by create()
            # loses its prefetch after invalidate_all() and would count one read per line
            lines = self.env["sale.order.line"].browse(lines.ids)
            self.env.invalidate_all()
            # display_qty_widget is computed line by line by sale_stock/sale_mrp (a BoM search per line) and
            # the form already has it before warehouse_stock is read; keep it out of the measurement
            lines.mapped("display_qty_widget")
            before = self.env.cr.sql_log_count
            lines._compute_warehouse_stocks()
            return self.env.cr.sql_log_count - before

        small = self._order(self.products[:2]).order_line
        large = self._order(self.products).order_line
        count_queries(small)  # warm up the ormcaches (decimal precision, config parameters)
        self.assertEqual(count_queries(large), count_queries(small))

    def test_vendor_qty_in_line_uom(self):
        self.product.seller_ids = [(0, 0, {"partner_id": self.partner.id, "qty_available": 24})]
        line = self._order(self.product, product_uom=self.uom_dozen.id).order_line
        self.assertAlmostEqual(line.vendor_qty_available, 2)

    def test_stock_colors_from_settings(self):
        self.env["ir.config_parameter"].sudo().set_param("deltatech_vendor_stock.color_fulfilled", "#000001")
        colors = self.env["sale.order.line"].get_stock_colors()
        self.assertEqual(colors["color_fulfilled"], "#000001")
        self.assertEqual(colors["color_default"], "#007bff")
