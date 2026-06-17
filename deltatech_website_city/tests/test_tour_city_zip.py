# © 2008-2025 Deltatech / Terrabit
# JS tour runner for deltatech_website_city: validates ZIP autofill and UI toggles.
#
# Modulul `deltatech_website_city` e gândit să meargă împreună cu `l10n_ro_city`
# (singura sursă reală de localități pentru România). În Odoo standard `res.city`
# e gol pentru RO, iar dependența e moale — modulul nu o cere explicit în
# `__manifest__.py`. Skip dacă nu e instalată: nu vrem să rulăm tour-ul peste
# date sintetice (Testland/Test State) care divergh de comportamentul real și
# au dovedit că pică intermitent în funcție de timing-ul layout-ului (vezi
# PR #2519 + #2523).

import unittest

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestWebsiteCityTour(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env

        l10n_ro_city = env["ir.module.module"].search(
            [("name", "=", "l10n_ro_city"), ("state", "=", "installed")], limit=1
        )
        if not l10n_ro_city:
            raise unittest.SkipTest(
                "l10n_ro_city must be installed for this tour: "
                "deltatech_website_city relies on res.city being populated"
            )

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
