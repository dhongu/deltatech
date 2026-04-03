# © 2008-2025 Deltatech / Terrabit
# JS tour runner for deltatech_website_city: validates ZIP autofill and UI toggles.

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteCityTour(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        # Ensure a website exists (and is the current one)
        website = env["website"].search([], limit=1)
        if not website:
            website = env["website"].create({"name": "Test Website"})
        cls.website = website

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
            "/my/account?debug=1",
            "deltatech_website_city_tour_city_zip",
            login="admin",
        )
