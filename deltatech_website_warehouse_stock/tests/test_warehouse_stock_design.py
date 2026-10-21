from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWarehouseStockDesign(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].browse(1)
        company = cls.website.company_id
        cls.env["stock.warehouse"].search([("company_id", "=", company.id)]).website_stock_display = False
        cls.wh_full = cls.env["stock.warehouse"].create(
            {"name": "TEST WH Full", "code": "TWF", "company_id": company.id}
        )
        cls.wh_low = cls.env["stock.warehouse"].create({"name": "TEST WH Low", "code": "TWL", "company_id": company.id})
        cls.wh_empty = cls.env["stock.warehouse"].create(
            {"name": "TEST WH Empty", "code": "TWE", "company_id": company.id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "TEST stock design product", "is_storable": True, "is_published": True, "website_id": False}
        )
        quant = cls.env["stock.quant"]
        quant._update_available_quantity(cls.product, cls.wh_full.lot_stock_id, 50)
        quant._update_available_quantity(cls.product, cls.wh_low.lot_stock_id, 3)

    def _lines(self):
        lines = (
            self.product.product_tmpl_id.with_context(website_id=self.website.id)
            .sudo()
            .get_warehouse_stock_distribution()
        )
        return {line["warehouse"]: line for line in lines}

    def _page(self):
        response = self.url_open(self.product.product_tmpl_id.website_url)
        self.assertEqual(response.status_code, 200)
        return response.text

    def test_defaults_keep_previous_look(self):
        self.assertEqual(self.website.warehouse_stock_style, "badges")
        self.assertEqual(self.website.warehouse_stock_zero_message, "out_of_stock")
        self.assertEqual(self.website.warehouse_stock_qty_display, "exact")
        self.assertFalse(self.website.warehouse_stock_theme_colors)
        lines = self._lines()
        self.assertEqual(lines["TEST WH Full"]["quantity"], "Available")
        self.assertEqual(lines["TEST WH Low"]["quantity"], "3")
        self.assertEqual(lines["TEST WH Empty"]["quantity"], "Out of stock")
        self.assertEqual(lines["TEST WH Empty"]["state"], "out")

    def test_on_order_and_status_only(self):
        self.website.write({"warehouse_stock_zero_message": "on_order", "warehouse_stock_qty_display": "status_only"})
        lines = self._lines()
        self.assertEqual(lines["TEST WH Full"]["quantity"], "In stock")
        self.assertEqual(lines["TEST WH Low"]["quantity"], "In stock")
        self.assertEqual(lines["TEST WH Empty"]["quantity"], "On order")
        self.assertEqual(lines["TEST WH Empty"]["state"], "on_order")
        self.assertEqual(lines["TEST WH Low"]["message"], "In stock at TEST WH Low. Ready for delivery.")

    def test_selector_messages(self):
        self.website.warehouse_stock_zero_message = "on_order"
        lines = self._lines()
        self.assertEqual(lines["TEST WH Low"]["message"], "In stock at TEST WH Low: 3 pcs. Ready for delivery.")
        self.assertEqual(
            lines["TEST WH Empty"]["message"],
            "Currently not on the shelf at TEST WH Empty. Brought in on order.",
        )

    def test_settings_write_website(self):
        settings = self.env["res.config.settings"].create(
            {
                "website_id": self.website.id,
                "warehouse_stock_style": "card",
                "warehouse_stock_zero_message": "on_order",
                "warehouse_stock_zero_note": "Delivery in 3-5 days",
                "warehouse_stock_qty_display": "status_only",
                "warehouse_stock_theme_colors": True,
            }
        )
        settings.execute()
        self.assertRecordValues(
            self.website,
            [
                {
                    "warehouse_stock_style": "card",
                    "warehouse_stock_zero_message": "on_order",
                    "warehouse_stock_zero_note": "Delivery in 3-5 days",
                    "warehouse_stock_qty_display": "status_only",
                    "warehouse_stock_theme_colors": True,
                }
            ],
        )

    def test_render_badges(self):
        html = self._page()
        self.assertIn("o_wh_stock_style_badges", html)
        self.assertIn('class="badge bg-success"', html)
        self.assertIn('class="badge bg-danger"', html)
        self.assertNotIn("o_wh_stock_pill", html)

    def test_render_badges_theme_colors(self):
        self.website.write({"warehouse_stock_theme_colors": True, "warehouse_stock_zero_message": "on_order"})
        html = self._page()
        self.assertIn("o_wh_stock_theme", html)
        self.assertIn("o_wh_stock_pill_success", html)
        self.assertIn("o_wh_stock_pill_warning", html)
        self.assertNotIn('class="badge bg-danger"', html)

    def test_render_list(self):
        self.website.write({"warehouse_stock_style": "list", "warehouse_stock_zero_message": "on_order"})
        html = self._page()
        self.assertIn("o_wh_stock_list", html)
        self.assertIn("fa-check-circle", html)
        self.assertIn("fa-clock-o", html)

    def test_render_card(self):
        self.website.write(
            {
                "warehouse_stock_style": "card",
                "warehouse_stock_zero_message": "on_order",
                "warehouse_stock_zero_note": "Delivery in 3-5 days",
            }
        )
        html = self._page()
        self.assertIn("o_wh_stock_card", html)
        self.assertIn("fa-map-marker", html)
        self.assertIn("Delivery in 3-5 days", html)

    def test_render_selector(self):
        self.website.write({"warehouse_stock_style": "selector", "warehouse_stock_zero_message": "on_order"})
        html = self._page()
        self.assertIn("o_wh_stock_selector", html)
        self.assertIn("o_wh_stock_check", html)
        self.assertIn('data-message="In stock at TEST WH Low: 3 pcs. Ready for delivery."', html)
        self.assertIn('data-state="on_order"', html)
