# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest.mock import patch

import requests

from odoo.tests import TransactionCase, tagged

from odoo.addons.http_routing.tests.common import MockRequest

from ..controllers.website_sale import WebsiteSaleVATValidation


@tagged("post_install", "-at_install")
class TestWebsiteSaleVATValidation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.controller = WebsiteSaleVATValidation()
        self.country_ro = self.env.ref("base.ro")

        # Creăm un partener existent pentru teste de unicitate
        self.existing_partner = self.env["res.partner"].create(
            {
                "name": "Existing Partner",
                "vat": "RO8001011234567",
                "email": "existing@example.com",
                "phone": "+40711111111",
                "country_id": self.country_ro.id,
            }
        )

    def test_01_vat_uniqueness(self):
        address_values = {
            "name": "New Partner",
            "vat": " RO8001011234567 ",  # Cu spații pentru a testa și striping
            "country_id": self.country_ro.id,
        }
        with MockRequest(self.env):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),  # Nou partener
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
            )

            self.assertIn("vat", invalid_fields)
            self.assertTrue(any("already has an account" in msg for msg in error_messages))
            self.assertFalse(any("Existing Partner" in msg for msg in error_messages), "the account is not named")

    def test_02_email_uniqueness(self):
        address_values = {
            "name": "New Partner",
            "email": " existing@example.com ",
            "country_id": self.country_ro.id,
        }
        with MockRequest(self.env):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="email",
            )

            self.assertIn("email", invalid_fields)
            self.assertTrue(any("belongs to another account" in msg for msg in error_messages))

    def test_03_phone_shared_is_accepted(self):
        """Colleagues share the company phone, relatives a home phone: not a duplicate."""
        address_values = {
            "name": "New Partner",
            "phone": " +40711111111 ",
            "country_id": self.country_ro.id,
        }
        with MockRequest(self.env):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="phone",
            )

            self.assertNotIn("phone", invalid_fields)

    def test_04_anaf_integration(self):
        # Simulăm datele ANAF folosind contextul, așa cum am văzut în l10n_ro_partner_create_by_vat/models/res_partner.py:_get_Anaf
        anaf_data = {
            "1234567897": {
                "date_generale": {
                    "denumire": "COMPANIA TEST ANAF SRL",
                    "cui": "1234567897",
                    "adresa": "STR. TEST NR. 1",
                },
                "adresa_sediu_social": {
                    "sdenumire_Strada": "TEST",
                    "snumar_Strada": "1",
                    "sdenumire_Localitate": "BUCURESTI",
                    "sdenumire_Judet": "BUCURESTI",
                    "scod_JudetAuto": "B",
                },
                "adresa_domiciliu_fiscal": {
                    "ddenumire_Strada": "TEST",
                    "dnumar_Strada": "1",
                    "ddetalii_Adresa": "",
                    "dcod_Postal": "010101",
                    "ddenumire_Localitate": "BUCURESTI",
                    "ddenumire_Judet": "BUCURESTI",
                    "dcod_JudetAuto": "B",
                    "adresa": "STR. TEST NR. 1",
                },
            }
        }
        address_values = {
            "vat": "RO1234567897",
            "country_id": self.country_ro.id,
        }
        # Trebuie să ne asigurăm că metodele ANAF există pe res.partner (adică modulul e instalat)
        if not hasattr(self.env["res.partner"], "_get_Anaf"):
            self.skipTest("Modulul l10n_ro_partner_create_by_vat nu este instalat.")

        # MockRequest keeps only the context passed to it, not the one of the env
        with MockRequest(self.env, context={"anaf_data": anaf_data}):
            # Ne asigurăm că adresa este pentru România
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
            )

            self.assertEqual(address_values.get("name"), "COMPANIA TEST ANAF SRL")
            self.assertEqual(address_values.get("city"), "Bucuresti")
            self.assertEqual(address_values.get("street"), "Test Nr. 1")
            self.assertTrue(address_values.get("is_company"))

    def test_05_public_user_no_enumeration(self):
        public_user = self.env.ref("base.public_user")
        for field, value in [
            ("email", "existing@example.com"),
            ("phone", "+40711111111"),
            ("vat", "RO8001011234567"),
        ]:
            address_values = {"name": "Guest", field: value, "country_id": self.country_ro.id}
            with MockRequest(self.env(user=public_user)):
                invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                    address_values=address_values,
                    partner_sudo=self.env["res.partner"].sudo(),
                    address_type="delivery",
                    use_delivery_as_billing=False,
                    required_fields=field,
                )
            self.assertNotIn(field, invalid_fields)
            self.assertFalse(any("already exists" in msg for msg in error_messages))
            self.assertFalse(any(value in msg for msg in error_messages))

    def test_06_public_user_vat_format_still_checked(self):
        public_user = self.env.ref("base.public_user")
        address_values = {"name": "Guest", "vat": "RO12AB34", "country_id": self.country_ro.id}
        with MockRequest(self.env(user=public_user)):
            invalid_fields, missing_fields, error_messages = self.controller._validate_address_values(
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
            )
        self.assertIn("vat", invalid_fields)

    def _validate_billing(self, address_values, anaf_data=None, cart=None):
        # MockRequest keeps only the context passed to it, not the one of the env
        with MockRequest(self.env, context={"anaf_data": anaf_data or {}}) as request:
            if cart is not None:
                request.cart = cart
            return self.controller._validate_address_values(
                address_values=address_values,
                partner_sudo=self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
            )

    def _skip_without_anaf(self):
        if not hasattr(self.env["res.partner"], "_Anaf_to_Odoo"):
            self.skipTest("l10n_ro_partner_create_by_vat is not installed")

    def test_07_cnp_gets_a_clear_message(self):
        """A person who types their CNP is told so, not that ANAF refused the number."""
        address_values = {"name": "Ion Popescu", "vat": "1900101400012", "country_id": self.country_ro.id}
        invalid_fields, _missing, error_messages = self._validate_billing(address_values)
        self.assertIn("vat", invalid_fields)
        self.assertTrue(any("CNP" in msg for msg in error_messages))
        self.assertFalse(any("ANAF" in msg for msg in error_messages))

    def test_08_vat_not_found_at_anaf_refused(self):
        self._skip_without_anaf()
        address_values = {"name": "Firma", "vat": "RO1234567897", "country_id": self.country_ro.id}
        invalid_fields, _missing, error_messages = self._validate_billing(address_values, anaf_data={})
        self.assertIn("vat", invalid_fields)
        self.assertTrue(any("ANAF" in msg for msg in error_messages))

    def test_09_anaf_unavailable_does_not_block(self):
        """ANAF down: the number is accepted as typed and the cart gets an internal note."""
        self._skip_without_anaf()
        product = self.env["product.product"].create({"name": "Produs", "list_price": 10})
        cart = self.env["sale.order"].create(
            {"partner_id": self.existing_partner.id, "order_line": [(0, 0, {"product_id": product.id})]}
        )
        address_values = {"name": "Firma Mea SRL", "vat": "RO1234567897", "country_id": self.country_ro.id}
        invalid_fields, _missing, error_messages = self._validate_billing(
            address_values, anaf_data={"1234567897": {"unavailable": True}}, cart=cart
        )
        self.assertNotIn("vat", invalid_fields)
        self.assertFalse(any("ANAF" in msg for msg in error_messages))
        self.assertEqual(address_values["name"], "Firma Mea SRL", "what the customer typed is kept")
        note = cart.message_ids.filtered(lambda m: "could not be checked at ANAF" in (m.body or ""))
        self.assertTrue(note)
        self.assertTrue(note.subtype_id.internal)

    def test_10_anaf_down_answer(self):
        """The real request: a network error is an unavailable service, not an unknown company."""
        self._skip_without_anaf()
        with MockRequest(self.env), patch.object(requests, "post", side_effect=requests.ConnectTimeout("timeout")):
            state, values = self.controller._anaf_lookup("1234567897")
        self.assertEqual((state, values), ("unavailable", {}))

    def _validate_vat_as(self, vat, partner_sudo=None):
        with MockRequest(self.env):
            return self.controller._validate_address_values(
                address_values={"name": "Contact", "vat": vat, "country_id": self.country_ro.id},
                partner_sudo=partner_sudo or self.env["res.partner"].sudo(),
                address_type="billing",
                use_delivery_as_billing=False,
                required_fields="vat",
            )

    def test_11_vat_duplicate_with_or_without_prefix(self):
        self.env["res.partner"].create(
            {"name": "Firma Existenta SRL", "is_company": True, "vat": "RO1234567897", "country_id": self.country_ro.id}
        )
        invalid_fields, _missing, error_messages = self._validate_vat_as("1234567897")
        self.assertIn("vat", invalid_fields)
        if "b2b_state" in self.env["res.partner"]._fields:
            self.assertTrue(any("/b2b" in msg for msg in error_messages), "the access request form is offered")
        else:
            self.assertTrue(any("contact us" in msg for msg in error_messages))

    def test_12_own_company_vat_is_not_a_duplicate(self):
        """A contact of a company who types the tax code of their own company is not blocked."""
        company = self.env["res.partner"].create(
            {"name": "Firma Mea SRL", "is_company": True, "vat": "RO1234567897", "country_id": self.country_ro.id}
        )
        contact = self.env["res.partner"].create({"name": "Coleg", "parent_id": company.id, "type": "invoice"})
        invalid_fields, _missing, error_messages = self._validate_vat_as("RO1234567897", partner_sudo=contact.sudo())
        self.assertNotIn("vat", invalid_fields)
        self.assertFalse(any("already has an account" in msg for msg in error_messages))
