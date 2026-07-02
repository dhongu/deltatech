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
            {"name": "Testland", "code": "XZ", "enforce_cities": True, "zip_required": True, "state_required": True}
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
        if hasattr(response, "get_data"):
            text = response.get_data(as_text=True)
        elif isinstance(response, (bytes, bytearray)):
            text = response.decode()
        else:
            text = str(response)
        payload = json.loads(text)
        return payload.get("result", payload)


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

    def test_mandatory_fields_enforce_cities(self):
        # Import the controller class and call its method directly.
        # The implementation only relies on the provided country and the parent logic.
        from ..controller.portal import CustomerPortalCity

        controller = CustomerPortalCity()
        fields_set = controller._get_mandatory_address_fields(self.country.sudo())

        # It should be a set-like collection containing state_id and city_id
        assert "state_id" in fields_set, "state_id must be mandatory when cities are enforced"
        assert "city_id" in fields_set, "city_id must be mandatory when cities are enforced"
        # And the free-text 'city' should not be mandatory
        assert "city" not in fields_set, "free-text city must be removed when cities are enforced"


class TestCityTemplate(TransactionCase):
    def test_initial_city_options_expose_zipcode(self):
        view = self.env.ref("deltatech_website_city.address_form_fields")
        self.assertIn("t-att-data-code=\"city.zipcode or ''\"", view.arch_db)
