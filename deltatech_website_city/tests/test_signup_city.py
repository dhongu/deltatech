# © 2008-2025 Deltatech / Terrabit
# JS tour runner for deltatech_website_city: validates signup and field presence.

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteCitySignupTour(HttpCase):
    def test_run_signup_city_tour(self):
        # Enable uninvited signup (B2C)
        self.env["res.config.settings"].create({"auth_signup_uninvited": "b2c"}).execute()

        # Run the signup tour
        self.start_tour(
            "/web/signup",
            "deltatech_website_city_signup_tour",
            login=None,
        )
