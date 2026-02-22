# © 2008-2025 Deltatech / Terrabit
# JS tour runner for deltatech_website_city: validates ZIP autofill and UI toggles.

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteCityTour(HttpCase):
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
        # Cities: one with ZIP, one without
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

    def test_run_city_zip_tour(self):
        # Use admin to access /my/account; the tour will select country/state/city
        self.start_tour(
            "/my/account",
            "deltatech_website_city_tour_city_zip",
            login="admin",
        )

    def test_portal_city_save(self):
        # Test if city is saved when submitting the portal account form
        admin_user = self.env.ref("base.user_admin")
        admin_user.partner_id.write(
            {
                "country_id": self.country.id,
                "state_id": self.state.id,
                "city_id": False,
                "city": "Old City",
            }
        )

        self.start_tour(
            "/my/account",
            "deltatech_website_city_tour_portal_save",
            login="admin",
        )

        admin_user.partner_id.invalidate_recordset(["city", "city_id"])
        self.assertEqual(admin_user.partner_id.city, "Alpha City")
        # Check if city_id is also set if possible (depends on how Odoo handles it)
        # In our case, we manually set data['city'] = city.name in the controller,
        # but the city_id should also be in the values passed to write() because it's in optional_fields.
        city_alpha = self.env["res.city"].search([("name", "=", "Alpha City")], limit=1)
        self.assertEqual(admin_user.partner_id.city_id.id, city_alpha.id)
