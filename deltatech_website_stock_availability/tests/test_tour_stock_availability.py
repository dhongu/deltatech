# © 2008-2025 Deltatech / Terrabit
# JS tour runner for deltatech_website_stock_availability

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteStockAvailabilityTour(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        cls.partner_a = env["res.partner"].create({"name": "Test Vendor"})

        seller_ids = [
            (0, 0, {"partner_id": cls.partner_a.id, "date_start": "2020-01-01", "delay": 5, "qty_available": 100})
        ]

        cls.product_a = env["product.product"].create(
            {
                "name": "Test Product A",
                "is_storable": True,
                "standard_price": 100,
                "list_price": 150,
                "seller_ids": seller_ids,
                "website_published": True,
            }
        )

        cls.product_c = env["product.product"].create(
            {
                "name": "Test Product C",
                "is_storable": True,
                "standard_price": 70,
                "list_price": 150,
                "seller_ids": seller_ids,
                "website_published": True,
            }
        )

        cls.stock_location = env.ref("stock.stock_location_stock")
        env["stock.quant"]._update_available_quantity(cls.product_a, cls.stock_location, 1000)

    def test_run_stock_availability_tour(self):
        self.start_tour(
            "/shop",
            "deltatech_website_stock_availability_tour",
            login="admin",
        )
