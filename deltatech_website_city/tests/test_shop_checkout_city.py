# © 2008-2025 Deltatech / Terrabit
# JS tour runner for deltatech_website_city: validates shop checkout with city/ZIP selection.

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteCityShopTour(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        # Prepare minimal geographic data used by the tour selections
        cls.country = env["res.country"].create(
            {"name": "Testland", "code": "XZ", "enforce_cities": True, "zip_required": True, "state_required": True}
        )
        cls.state = env["res.country.state"].create(
            {
                "name": "Test State",
                "code": "TS",
                "country_id": cls.country.id,
            }
        )
        # Cities
        env["res.city"].create(
            {
                "name": "Alpha City",
                "state_id": cls.state.id,
                "country_id": cls.country.id,
                "zipcode": "12345",
            }
        )
        env["res.city"].create(
            {
                "name": "Beta City",
                "state_id": cls.state.id,
                "country_id": cls.country.id,
            }
        )

        # Create a product
        cls.product = env["product.product"].create(
            {
                "name": "Test Product",
                "is_storable": True,
                "list_price": 100.0,
                "website_published": True,
            }
        )

    def test_run_shop_checkout_city_tour(self):
        # Create a user to use in the tour
        self.env["res.users"].create(
            {
                "name": "Shop User",
                "login": "shop_user",
                "email": "shop_user@test.com",
                "groups_id": [(6, 0, [self.env.ref("base.group_portal").id])],
            }
        )
        # Run the shop checkout tour
        self.start_tour(
            "/shop",
            "deltatech_website_city_shop_checkout_tour",
            login="shop_user",
        )
