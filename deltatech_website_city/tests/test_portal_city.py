# © 2008-2025 Deltatech / Terrabit
# Test suite for deltatech_website_city
# Focus: JSON-RPC route for state -> cities, and mandatory address fields logic.

import json

from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPortalCityRoute(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        # Create a dedicated country with enforced cities to avoid coupling with demo data
        cls.country = env["res.country"].create(
            {
                "name": "Testland",
                "code": "XZ",
                "enforce_cities": True,
                "zip_applicability": "required",
                "state_required": True,
            }
        )
        cls.state = env["res.country.state"].create(
            {
                "name": "Test State",
                "code": "TS",
                "country_id": cls.country.id,
            }
        )
        # Two cities, one with zipcode, one without
        cls.city1 = env["res.city"].create(
            {
                "name": "Alpha City",
                "state_id": cls.state.id,
                "country_id": cls.country.id,
                "zipcode": "12345",
            }
        )
        cls.city2 = env["res.city"].create(
            {
                "name": "Beta City",
                "state_id": cls.state.id,
                "country_id": cls.country.id,
                # zipcode left empty on purpose
            }
        )

    def _jsonrpc(self, url, params=None):
        body = {"jsonrpc": "2.0", "method": "call", "params": params or {}}
        response = self.url_open(url, data=json.dumps(body), headers={"Content-Type": "application/json"})
        response.raise_for_status()
        payload = response.json()
        self.assertNotIn("error", payload, payload.get("error"))
        return payload["result"]

    def test_city_choice_enforced_for_any_country(self):
        """In 20.0 `portal` offers the city dropdown only for BR, CL, PE, CO and TW."""
        self.assertTrue(self.country._enforce_city_choice())
        self.country.enforce_cities = False
        self.assertFalse(self.country._enforce_city_choice())

    def test_state_info_returns_cities_with_zip(self):
        result = self._jsonrpc(
            "/my/address/state_info",
            {"country_id": self.country.id, "state_id": self.state.id, "address_type": "billing"},
        )
        cities = {city["name"]: city for city in result["cities"]}
        self.assertEqual(set(cities), {"Alpha City", "Beta City"})
        self.assertEqual(cities["Alpha City"]["zipcode"], "12345")

    def test_legacy_state_infos_route(self):
        result = self._jsonrpc(f"/portal/state_infos/{self.state.id}")
        self.assertIn([self.city1.id, self.city1.display_name, "12345"], result["cities"])

    def test_address_form_offers_the_cities_of_the_state(self):
        partner = self.env.ref("base.partner_admin")
        partner.write({"country_id": self.country.id, "state_id": self.state.id, "city_id": self.city1.id})
        self.authenticate("admin", "admin")
        response = self.url_open(f"/my/address?partner_id={partner.id}")
        response.raise_for_status()
        self.assertIn('data-zipcode="12345"', response.text)
        self.assertRegex(response.text, r'id="div_city"[^>]*style="display:none;"')


class TestMandatoryFields(TransactionCase):
    def setUp(self):
        super().setUp()
        self.country = self.env["res.country"].create(
            {
                "name": "Must City Country",
                "code": "XY",
                "enforce_cities": True,
            }
        )
        state = self.env["res.country.state"].create(
            {"name": "Must State", "code": "MS", "country_id": self.country.id}
        )
        self.env["res.city"].create({"name": "Must City", "state_id": state.id, "country_id": self.country.id})

    def test_mandatory_fields_enforce_cities(self):
        fields_set = self.env["res.partner"]._get_mandatory_address_fields(self.country.sudo())

        # It should be a set-like collection containing state_id and city_id
        self.assertIn("state_id", fields_set, "state_id must be mandatory when cities are enforced")
        self.assertIn("city_id", fields_set, "city_id must be mandatory when cities are enforced")
        # And the free-text 'city' should not be mandatory
        self.assertNotIn("city", fields_set, "free-text city must be removed when cities are enforced")

    def test_mandatory_fields_without_cities_enforced(self):
        self.country.enforce_cities = False
        fields_set = self.env["res.partner"]._get_mandatory_address_fields(self.country.sudo())
        self.assertIn("city", fields_set)
        self.assertNotIn("city_id", fields_set)


class TestCityTemplate(TransactionCase):
    def test_free_text_city_hidden_when_city_is_chosen_from_list(self):
        view = self.env.ref("deltatech_website_city.address_form_fields")
        self.assertIn("'city_id' in (required_fields or ())", view.arch_db)
