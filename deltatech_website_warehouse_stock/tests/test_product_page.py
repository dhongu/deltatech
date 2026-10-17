from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestProductPageWarehouseStock(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.warehouse.write({"name": "TEST WH Visible", "website_stock_display": True})
        cls.warehouse_empty = cls.env["stock.warehouse"].create(
            {"name": "TEST WH Empty", "code": "TWHE", "company_id": cls.warehouse.company_id.id}
        )
        cls.warehouse_hidden = cls.env["stock.warehouse"].create(
            {
                "name": "TEST WH Hidden",
                "code": "TWHH",
                "company_id": cls.warehouse.company_id.id,
                "website_stock_display": False,
            }
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "TEST warehouse stock product",
                "is_storable": True,
                "list_price": 10.0,
                "website_published": True,
                "sale_ok": True,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.warehouse.lot_stock_id, 3)
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.warehouse_hidden.lot_stock_id, 7)

    def _product_page(self):
        response = self.url_open(self.product.website_url)
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_product_page_shows_warehouse_stock(self):
        html = self._product_page()
        self.assertIn('id="warehouse_stock_title"', html)
        self.assertIn("TEST WH Visible", html)
        self.assertIn('id="warehouse_stock_qty_low"', html)
        self.assertIn("TEST WH Empty", html)
        self.assertIn('id="warehouse_stock_qty_out"', html)
        self.assertNotIn("TEST WH Hidden", html)

    def test_product_page_threshold(self):
        self.env["ir.config_parameter"].sudo().set_int("deltatech_website_warehouse_stock.threshold", 2)
        html = self._product_page()
        self.assertIn('id="warehouse_stock_qty_available"', html)
        self.assertNotIn('id="warehouse_stock_qty_low"', html)
